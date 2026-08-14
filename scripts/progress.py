#!/usr/bin/env python3
"""Track solution-free practice metadata with deterministic adaptive reviews."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 4
VALID_OUTCOMES = {
    "independent",
    "lightly_assisted",
    "heavily_assisted",
    "walked_through",
    "incomplete",
}
VALID_INITIAL_RESULTS = {"correct", "partial", "incorrect"}
VALID_RECALL = {"again", "hard", "good", "easy"}
VALID_CAPABILITIES = {
    "debugging_diagnosis",
    "code_reading",
    "decomposition_modeling",
    "invariants_failures",
    "ai_code_review",
    "algorithms_data",
}
# "immediate_transfer" is readable in legacy state but is no longer a session phase:
# the transfer task happens inside a session, so its score is a session field.
VALID_PHASES = {
    "baseline",
    "practice",
    "immediate_transfer",
    "retention_7d",
    "retention_21d",
    "final",
}
RECORDABLE_PHASES = VALID_PHASES - {"immediate_transfer"}
VALID_ASSISTANCE = {
    "strict_unaided",
    "standard_unaided",
    "coached",
    "conventional_ai",
}
VALID_EVALUATORS = {"coach"}
VALID_EVALUATOR_CONTEXTS = {"coaching"}
# Legacy files may still contain these labels; they are readable, not recordable.
LEGACY_EVALUATORS = {"coach", "independent"}
LEGACY_EVALUATOR_CONTEXTS = {"coaching", "isolated"}

UNAIDED_POLICIES = {"strict_unaided", "standard_unaided"}
ASSISTED_POLICIES = VALID_ASSISTANCE - UNAIDED_POLICIES
UNAIDED_PHASES = RECORDABLE_PHASES - {"practice"}
RETENTION_MIN_GAP_DAYS = {"retention_7d": 7, "retention_21d": 21}
ASSISTED_FIRST_DUE_DAYS = 7

# rubric.md defines each outcome by the highest conceptual hint that preceded it.
HINT_RANGE_BY_OUTCOME = {
    "independent": (0, 0),
    "lightly_assisted": (1, 3),
    "heavily_assisted": (4, 5),
    "walked_through": (6, 6),
    "incomplete": (0, 5),
}


def empty_state() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "program": None, "sessions": [], "cards": []}


def require_iso_date(value: object, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"Invalid {field} (use YYYY-MM-DD): {value!r}") from exc


def normalize_session(session: Any) -> dict[str, Any]:
    if not isinstance(session, dict):
        raise SystemExit(f"Session must be an object, not {type(session).__name__}")
    normalized = dict(session)
    if normalized.get("date"):
        require_iso_date(normalized["date"], "session date")
    normalized.setdefault("capability", "unclassified")
    normalized.setdefault("phase", "practice")
    normalized.setdefault("assistance", "coached")
    evaluator = normalized.setdefault("evaluator", "coach")
    if evaluator not in LEGACY_EVALUATORS:
        raise SystemExit(f"Invalid evaluator in session: {evaluator}")
    context = normalized.setdefault("evaluator_context", "coaching")
    if context not in LEGACY_EVALUATOR_CONTEXTS:
        raise SystemExit(f"Invalid evaluator_context in session: {context}")
    normalized.setdefault("package_id", "")
    normalized.setdefault("policy_deviations", "")
    normalized.setdefault("transfer", None)
    # The transfer task is unaided by protocol; legacy rows predate the explicit field.
    normalized.setdefault(
        "transfer_policy", "standard_unaided" if normalized["transfer"] is not None else None
    )
    return normalized


def normalize_card(card: Any) -> dict[str, Any]:
    """Fill scheduler fields a card may lack so read-only commands cannot crash."""
    if not isinstance(card, dict):
        raise SystemExit(f"Card must be an object, not {type(card).__name__}")
    for key in ("id", "due"):
        if not card.get(key):
            raise SystemExit(f"Card is missing required field '{key}': {card}")
    require_iso_date(card["due"], "card due")
    normalized = dict(card)
    if normalized.get("last_review"):
        require_iso_date(normalized["last_review"], "card last_review")
    normalized.setdefault("topic", normalized["id"])
    normalized.setdefault("stability_days", 1.0)
    normalized.setdefault("difficulty", 5.0)
    normalized.setdefault("last_review", None)
    normalized.setdefault("reviews", 0)
    normalized.setdefault("lapses", 0)
    normalized.setdefault("last_confidence", None)
    normalized.setdefault("calibration", "unknown")
    return normalized


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "concept"


def parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use YYYY-MM-DD") from exc


def migrate_v1(data: dict[str, Any]) -> dict[str, Any]:
    migrated = empty_state()
    migrated["sessions"] = list(data.get("sessions", []))
    seen: set[str] = set()
    for session in migrated["sessions"]:
        topic = str(session.get("topic", "legacy concept"))
        concept_id = slugify(topic)
        if concept_id in seen:
            continue
        seen.add(concept_id)
        session_day = require_iso_date(
            session.get("date", date.today().isoformat()), "session date"
        )
        reviews = session.get("reviews", [])
        pending = []
        for review in reviews:
            if review.get("completed") or not review.get("due"):
                continue
            pending.append(require_iso_date(review.get("due"), "legacy review due").isoformat())
        due = min(pending) if pending else (session_day + timedelta(days=2)).isoformat()
        migrated["cards"].append(
            {
                "id": concept_id,
                "topic": topic,
                "stability_days": 2.0,
                "difficulty": 5.0,
                "due": due,
                "last_review": session_day.isoformat(),
                "reviews": 0,
                "lapses": 0,
                "last_confidence": None,
                "calibration": "unknown",
            }
        )
    return migrated


def migrate_v2(data: dict[str, Any]) -> dict[str, Any]:
    migrated = empty_state()
    migrated["sessions"] = list(data.get("sessions", []))
    migrated["cards"] = data.get("cards", [])
    return migrated


def migrate_v3(data: dict[str, Any]) -> dict[str, Any]:
    migrated = empty_state()
    migrated["program"] = data.get("program")
    migrated["sessions"] = list(data.get("sessions", []))
    migrated["cards"] = data.get("cards", [])
    return migrated


def load_state(path: Path, allow_missing: bool = False) -> dict[str, Any]:
    if not path.exists():
        if allow_missing:
            return empty_state()
        raise SystemExit(f"State file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read valid JSON from {path}: {exc}") from exc
    if data.get("schema_version") == 1 and isinstance(data.get("sessions"), list):
        data = migrate_v1(data)
    elif data.get("schema_version") == 2 and isinstance(data.get("sessions"), list):
        data = migrate_v2(data)
    elif data.get("schema_version") == 3 and isinstance(data.get("sessions"), list):
        data = migrate_v3(data)
    elif data.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit(f"Unsupported state schema in {path}")
    if not isinstance(data.get("sessions"), list) or not isinstance(data.get("cards"), list):
        raise SystemExit(f"Invalid state structure in {path}")
    data["sessions"] = [normalize_session(session) for session in data["sessions"]]
    data["cards"] = [normalize_card(card) for card in data["cards"]]
    data.setdefault("program", None)
    return data


def save_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def calibration_label(initial_result: str, confidence: int) -> str:
    if initial_result in {"incorrect", "partial"} and confidence >= 4:
        return "confident_wrong"
    if initial_result == "correct" and confidence <= 2:
        return "uncertain_correct"
    return "calibrated"


def initial_recall(
    outcome: str, initial_result: str, explain_back: int, transfer: int | None
) -> str:
    if initial_result == "incorrect":
        return "again"
    if initial_result == "partial" or outcome in {"heavily_assisted", "walked_through", "incomplete"}:
        return "hard"
    # A session without a transfer attempt cannot earn the strongest rating.
    if outcome == "independent" and explain_back >= 3 and (transfer or 0) >= 4:
        return "easy"
    return "good"


def find_card(data: dict[str, Any], concept_id: str) -> dict[str, Any] | None:
    return next((card for card in data["cards"] if card.get("id") == concept_id), None)


def new_card(concept_id: str, topic: str, review_day: date) -> dict[str, Any]:
    return {
        "id": concept_id,
        "topic": topic,
        "stability_days": 1.0,
        "difficulty": 5.0,
        "due": review_day.isoformat(),
        "last_review": None,
        "reviews": 0,
        "lapses": 0,
        "last_confidence": None,
        "calibration": "unknown",
    }


def update_schedule(
    card: dict[str, Any], review_day: date, recall: str, confidence: int
) -> None:
    stability = float(card.get("stability_days", 1.0))
    difficulty = float(card.get("difficulty", 5.0))
    calibration = "calibrated"

    if recall == "again":
        stability = max(0.5, stability * 0.35)
        difficulty = min(10.0, difficulty + 1.0)
        card["lapses"] = int(card.get("lapses", 0)) + 1
        if confidence >= 4:
            stability = 0.5
            difficulty = min(10.0, difficulty + 0.8)
            calibration = "confident_wrong"
    elif recall == "hard":
        growth = 1.15 if confidence <= 2 else 1.25
        stability = max(1.0, stability * growth)
        difficulty = min(10.0, difficulty + 0.3)
        if confidence <= 2:
            calibration = "uncertain_correct"
    elif recall == "good":
        growth = 1.8 + max(0.0, 10.0 - difficulty) * 0.05
        if confidence <= 2:
            growth *= 0.85
            calibration = "uncertain_correct"
        stability = max(2.0, stability * growth)
        difficulty = min(10.0, max(1.0, difficulty + (3 - confidence) * 0.1))
    elif recall == "easy":
        growth = 2.5 + max(0.0, 10.0 - difficulty) * 0.06
        stability = max(4.0, stability * growth)
        difficulty = max(1.0, difficulty - 0.5)
    else:
        raise SystemExit(f"Invalid recall rating: {recall}")

    interval = 1 if calibration == "confident_wrong" else max(1, min(365, math.ceil(stability)))
    card.update(
        {
            "stability_days": round(stability, 2),
            "difficulty": round(difficulty, 2),
            "due": (review_day + timedelta(days=interval)).isoformat(),
            "last_review": review_day.isoformat(),
            "reviews": int(card.get("reviews", 0)) + 1,
            "last_confidence": confidence,
            "calibration": calibration,
            "last_recall": recall,
        }
    )


def validate_score(name: str, value: int, minimum: int, maximum: int) -> None:
    if not minimum <= value <= maximum:
        raise SystemExit(f"--{name} must be between {minimum} and {maximum}")


def last_session_day(data: dict[str, Any], concept_id: str) -> date | None:
    days = [
        require_iso_date(session["date"], "session date")
        for session in data["sessions"]
        if session.get("concept_id") == concept_id and session.get("date")
    ]
    return max(days) if days else None


def has_unaided_session(data: dict[str, Any], concept_id: str) -> bool:
    return any(
        session.get("concept_id") == concept_id and session.get("assistance") in UNAIDED_POLICIES
        for session in data["sessions"]
    )


def validate_retention_gap(
    data: dict[str, Any], concept_id: str, phase: str, session_day: date
) -> None:
    gap = RETENTION_MIN_GAP_DAYS.get(phase)
    if gap is None:
        return
    prior = last_session_day(data, concept_id)
    if prior is None:
        raise SystemExit(f"phase {phase} requires a prior session for this concept")
    earliest = prior + timedelta(days=gap)
    if session_day < earliest:
        raise SystemExit(
            f"phase {phase} requires at least {gap} days after the last session "
            f"for this concept (earliest {earliest.isoformat()})"
        )


def validate_consistency(
    outcome: str,
    initial_result: str,
    hints: int,
    assistance: str,
    phase: str,
    transfer: int | None,
) -> None:
    """Reject sessions whose fields contradict rubric.md and assistance-policy.md."""
    low, high = HINT_RANGE_BY_OUTCOME[outcome]
    if not low <= hints <= high:
        raise SystemExit(
            f"outcome {outcome} requires --hints between {low} and {high} (rubric.md)"
        )
    if outcome == "independent" and initial_result != "correct":
        raise SystemExit("outcome independent requires --initial-result correct (rubric.md)")
    if outcome == "incomplete" and initial_result == "correct":
        raise SystemExit("outcome incomplete cannot pair with --initial-result correct")
    if initial_result == "correct" and outcome in {"heavily_assisted", "walked_through"}:
        raise SystemExit(
            "a correct first answer cannot pair with heavily_assisted or walked_through"
        )
    if assistance in UNAIDED_POLICIES and hints > 0:
        raise SystemExit(
            f"assistance {assistance} forbids conceptual hints; use --hints 0 "
            "(assistance-policy.md)"
        )
    if phase in UNAIDED_PHASES and assistance not in UNAIDED_POLICIES:
        raise SystemExit(f"phase {phase} must use an unaided assistance policy")
    if assistance == "conventional_ai" and outcome == "independent":
        raise SystemExit(
            "assistance conventional_ai cannot pair with outcome independent; "
            "conventional AI is assistance, not an unaided result"
        )
    if assistance == "conventional_ai" and transfer is not None:
        raise SystemExit(
            "assistance conventional_ai cannot record an unaided transfer score"
        )


def cmd_init(args: argparse.Namespace) -> None:
    if args.state.exists() and not args.force:
        raise SystemExit(f"State file already exists: {args.state}; use --force to replace it")
    save_state(args.state, empty_state())
    print(f"Initialized {args.state}")


def cmd_record(args: argparse.Namespace) -> None:
    data = load_state(args.state, allow_missing=True)
    validate_score("hints", args.hints, 0, 6)
    validate_score("explain-back", args.explain_back, 0, 4)
    validate_score("confidence", args.confidence, 1, 5)
    if args.transfer is not None:
        validate_score("transfer", args.transfer, 0, 4)
    if args.minutes < 0:
        raise SystemExit("--minutes cannot be negative")
    validate_consistency(
        args.outcome,
        args.initial_result,
        args.hints,
        args.assistance,
        args.phase,
        args.transfer,
    )

    session_day = args.date or date.today()
    concept_id = args.concept_id or slugify(args.topic)
    validate_retention_gap(data, concept_id, args.phase, session_day)
    recall = initial_recall(args.outcome, args.initial_result, args.explain_back, args.transfer)
    session = {
        "date": session_day.isoformat(),
        "concept_id": concept_id,
        "topic": args.topic,
        "exercise": args.exercise,
        "mode": args.mode,
        "capability": args.capability,
        "phase": args.phase,
        "assistance": args.assistance,
        "evaluator": args.evaluator,
        "evaluator_context": args.evaluator_context,
        "package_id": args.package_id or "",
        "policy_deviations": args.policy_deviations or "",
        "initial_result": args.initial_result,
        "confidence_before_feedback": args.confidence,
        "confidence_calibration": calibration_label(args.initial_result, args.confidence),
        "outcome": args.outcome,
        "highest_hint": args.hints,
        "explain_back": args.explain_back,
        "transfer": args.transfer,
        "transfer_policy": args.transfer_policy if args.transfer is not None else None,
        "minutes": args.minutes,
        "notes": args.notes or "",
        "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    data["sessions"].append(session)
    card = find_card(data, concept_id)
    if card is None:
        card = new_card(concept_id, args.topic, session_day)
        if args.assistance not in UNAIDED_POLICIES:
            card["due"] = (session_day + timedelta(days=ASSISTED_FIRST_DUE_DAYS)).isoformat()
        data["cards"].append(card)
    scheduled = False
    if args.assistance in UNAIDED_POLICIES:
        update_schedule(card, session_day, recall, args.confidence)
        scheduled = True
    save_state(args.state, data)
    due_note = f" next_due={card['due']}" if card.get("due") else ""
    print(
        f"Recorded session {len(data['sessions'])}; concept={concept_id} "
        f"recall={recall}{due_note}"
        + ("" if scheduled else " (scheduler unchanged; assisted session)")
    )


def cmd_review(args: argparse.Namespace) -> None:
    data = load_state(args.state)
    validate_score("confidence", args.confidence, 1, 5)
    card = find_card(data, args.concept_id)
    if card is None:
        raise SystemExit(f"Unknown concept id: {args.concept_id}")
    if not has_unaided_session(data, args.concept_id):
        raise SystemExit(
            "review requires a recorded unaided session for this concept; "
            "do not grade recall from assisted practice alone"
        )
    review_day = args.on or date.today()
    previous_due = card["due"]
    update_schedule(card, review_day, args.recall, args.confidence)
    card.setdefault("history", []).append(
        {
            "date": review_day.isoformat(),
            "scheduled_for": previous_due,
            "recall": args.recall,
            "confidence_before_feedback": args.confidence,
            "next_due": card["due"],
        }
    )
    save_state(args.state, data)
    print(
        f"Reviewed concept={args.concept_id} recall={args.recall} "
        f"stability={card['stability_days']}d next_due={card['due']}"
    )


def cmd_due(args: argparse.Namespace) -> None:
    data = load_state(args.state)
    today = args.on or date.today()
    cards = sorted(
        (card for card in data["cards"] if require_iso_date(card["due"], "card due") <= today),
        key=lambda card: (card["due"], -float(card["difficulty"]), card["id"]),
    )
    if not cards:
        print("No reviews due.")
        return
    for card in cards:
        print(
            f"concept={card['id']} due={card['due']} topic={card['topic']} "
            f"stability={card['stability_days']}d difficulty={card['difficulty']} "
            f"calibration={card['calibration']}"
        )


def distribution(items: list[dict[str, Any]], field: str) -> str:
    values = [int(item[field]) for item in items if item.get(field) is not None]
    if not values:
        return "n=0"
    return (
        f"n={len(values)} median={statistics.median(values):.1f} "
        f"range={min(values)}-{max(values)}"
    )


def cmd_status(args: argparse.Namespace) -> None:
    data = load_state(args.state)
    sessions = data["sessions"]
    cards = data["cards"]
    print(f"Sessions: {len(sessions)}")
    print(f"Concept cards: {len(cards)}")
    if data.get("program"):
        program = data["program"]
        print(
            f"Program: {program['objective']} / {program['duration_weeks']} weeks / "
            f"baseline={program['baseline_policy']}"
        )
    if sessions:
        # rubric.md forbids pooling assisted and unaided attempts into one number.
        for label, policies in (("Unaided", UNAIDED_POLICIES), ("Assisted", ASSISTED_POLICIES)):
            items = [item for item in sessions if item.get("assistance") in policies]
            if not items:
                continue
            independent = sum(item.get("outcome") == "independent" for item in items)
            print(f"{label} sessions: {len(items)} (independent outcomes: {independent})")
            print(f"  Explain-back 0-4: {distribution(items, 'explain_back')}")
            print(f"  Highest hint 0-6: {distribution(items, 'highest_hint')}")
        # The transfer attempt is unaided even inside a coached session, so it is
        # never reported under the assistance policy of the session that hosted it.
        attempted = [item for item in sessions if item.get("transfer") is not None]
        skipped = len(sessions) - len(attempted)
        print(f"Transfer attempts (unaided by protocol): {distribution(attempted, 'transfer')}")
        for policy in sorted({str(item.get("transfer_policy")) for item in attempted}):
            items = [item for item in attempted if item.get("transfer_policy") == policy]
            print(f"  {policy}: {distribution(items, 'transfer')}")
        if skipped:
            print(f"  sessions without a transfer task: {skipped}")
        calibrated = [item.get("confidence_calibration") for item in sessions]
        print(f"Confident-wrong attempts: {calibrated.count('confident_wrong')}")
        print(f"Uncertain-correct attempts: {calibrated.count('uncertain_correct')}")
        deviations = sum(bool(item.get("policy_deviations")) for item in sessions)
        print(f"Sessions with policy deviations: {deviations}")
        for phase in sorted({str(item.get("phase", "practice")) for item in sessions}):
            items = [item for item in sessions if item.get("phase", "practice") == phase]
            leftover_independent = sum(item.get("evaluator") == "independent" for item in items)
            print(
                f"Phase {phase}: transfer {distribution(items, 'transfer')} "
                f"coach_scored={len(items) - leftover_independent}"
                + (
                    f" leftover_independent_labels={leftover_independent}"
                    if leftover_independent
                    else ""
                )
            )
        for capability in sorted({str(item.get("capability", "unclassified")) for item in sessions}):
            items = [item for item in sessions if item.get("capability", "unclassified") == capability]
            # capability-model.md requires at least two tasks before reading a weakness.
            note = "" if len(items) >= 2 else "  [insufficient: <2 tasks]"
            print(f"Capability {capability}: transfer {distribution(items, 'transfer')}{note}")
    if cards:
        stabilities = [float(card["stability_days"]) for card in cards]
        print(f"Median stability: {statistics.median(stabilities):.2f} days")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create an empty state file")
    init.add_argument("--state", type=Path, required=True)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    record = subparsers.add_parser("record", help="record a session and schedule its concept")
    record.add_argument("--state", type=Path, required=True)
    record.add_argument("--date", type=parse_day)
    record.add_argument("--concept-id")
    record.add_argument("--topic", required=True)
    record.add_argument("--exercise", required=True)
    record.add_argument("--mode", required=True)
    record.add_argument("--capability", choices=sorted(VALID_CAPABILITIES), required=True)
    record.add_argument("--phase", choices=sorted(RECORDABLE_PHASES), default="practice")
    record.add_argument("--assistance", choices=sorted(VALID_ASSISTANCE), default="coached")
    record.add_argument(
        "--evaluator",
        choices=sorted(VALID_EVALUATORS),
        default="coach",
        help="only coach is recordable; isolated independent scoring is deferred",
    )
    record.add_argument(
        "--evaluator-context",
        choices=sorted(VALID_EVALUATOR_CONTEXTS),
        default="coaching",
        help="only coaching context is recordable",
    )
    record.add_argument("--package-id")
    record.add_argument("--policy-deviations")
    record.add_argument("--initial-result", choices=sorted(VALID_INITIAL_RESULTS), required=True)
    record.add_argument("--confidence", type=int, required=True)
    record.add_argument("--outcome", choices=sorted(VALID_OUTCOMES), required=True)
    record.add_argument("--hints", type=int, required=True)
    record.add_argument("--explain-back", type=int, required=True)
    record.add_argument("--transfer", type=int, help="0-4; omit when no transfer task was given")
    record.add_argument(
        "--transfer-policy",
        choices=sorted(UNAIDED_POLICIES),
        default="standard_unaided",
        help="the transfer task is unaided by protocol; records which unaided policy applied",
    )
    record.add_argument("--minutes", type=int, required=True)
    record.add_argument("--notes")
    record.set_defaults(func=cmd_record)

    review = subparsers.add_parser(
        "review",
        help="grade unaided recall and adapt its next due date",
    )
    review.add_argument("--state", type=Path, required=True)
    review.add_argument("--concept-id", required=True)
    review.add_argument("--recall", choices=sorted(VALID_RECALL), required=True)
    review.add_argument("--confidence", type=int, required=True)
    review.add_argument("--on", type=parse_day)
    review.set_defaults(func=cmd_review)

    due = subparsers.add_parser("due", help="list concepts due on or before a date")
    due.add_argument("--state", type=Path, required=True)
    due.add_argument("--on", type=parse_day)
    due.set_defaults(func=cmd_due)

    status = subparsers.add_parser("status", help="summarize progress and calibration")
    status.add_argument("--state", type=Path, required=True)
    status.set_defaults(func=cmd_status)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
