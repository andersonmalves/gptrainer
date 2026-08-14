#!/usr/bin/env python3
"""Track solution-free practice metadata with deterministic adaptive reviews."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 3
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
VALID_PHASES = {
    "baseline",
    "practice",
    "immediate_transfer",
    "retention_7d",
    "retention_21d",
    "final",
}
VALID_ASSISTANCE = {
    "strict_unaided",
    "standard_unaided",
    "coached",
    "conventional_ai",
}
VALID_EVALUATORS = {"coach", "independent"}
VALID_EVALUATOR_CONTEXTS = {"coaching", "isolated"}
VALID_OBJECTIVES = {"recover", "prevent_decline", "improve_baseline"}


def empty_state() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "program": None, "sessions": [], "cards": []}


def normalize_session(session: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(session)
    normalized.setdefault("capability", "unclassified")
    normalized.setdefault("phase", "practice")
    normalized.setdefault("assistance", "coached")
    normalized.setdefault("evaluator", "coach")
    normalized.setdefault("evaluator_context", "coaching")
    normalized.setdefault("package_id", "")
    normalized.setdefault("policy_deviations", "")
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
    migrated["sessions"] = [normalize_session(item) for item in data.get("sessions", [])]
    seen: set[str] = set()
    for session in migrated["sessions"]:
        topic = str(session.get("topic", "legacy concept"))
        concept_id = slugify(topic)
        if concept_id in seen:
            continue
        seen.add(concept_id)
        session_day = parse_day(str(session.get("date", date.today().isoformat())))
        reviews = session.get("reviews", [])
        pending = [review.get("due") for review in reviews if not review.get("completed")]
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
    migrated["sessions"] = [normalize_session(item) for item in data.get("sessions", [])]
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
        return migrate_v1(data)
    if data.get("schema_version") == 2 and isinstance(data.get("sessions"), list):
        return migrate_v2(data)
    if data.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit(f"Unsupported state schema in {path}")
    if not isinstance(data.get("sessions"), list) or not isinstance(data.get("cards"), list):
        raise SystemExit(f"Invalid state structure in {path}")
    data.setdefault("program", None)
    return data


def save_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def calibration_label(initial_result: str, confidence: int) -> str:
    if initial_result == "incorrect" and confidence >= 4:
        return "confident_wrong"
    if initial_result == "correct" and confidence <= 2:
        return "uncertain_correct"
    return "calibrated"


def initial_recall(outcome: str, initial_result: str, explain_back: int, transfer: int) -> str:
    if initial_result == "incorrect":
        return "again"
    if initial_result == "partial" or outcome in {"heavily_assisted", "walked_through", "incomplete"}:
        return "hard"
    if outcome == "independent" and explain_back >= 3 and transfer >= 4:
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


def cmd_init(args: argparse.Namespace) -> None:
    if args.state.exists() and not args.force:
        raise SystemExit(f"State file already exists: {args.state}; use --force to replace it")
    save_state(args.state, empty_state())
    print(f"Initialized {args.state}")


def cmd_configure(args: argparse.Namespace) -> None:
    data = load_state(args.state, allow_missing=True)
    if not 6 <= args.duration_weeks <= 8:
        raise SystemExit("--duration-weeks must be between 6 and 8")
    capabilities = args.capability or [
        "debugging_diagnosis",
        "code_reading",
        "decomposition_modeling",
        "invariants_failures",
        "ai_code_review",
    ]
    data["program"] = {
        "objective": args.objective,
        "duration_weeks": args.duration_weeks,
        "started_on": (args.started_on or date.today()).isoformat(),
        "baseline_policy": args.baseline_policy,
        "capabilities": capabilities,
        "success_rule": args.success_rule,
    }
    save_state(args.state, data)
    print(
        f"Configured {args.duration_weeks}-week program objective={args.objective} "
        f"capabilities={','.join(capabilities)}"
    )


def cmd_record(args: argparse.Namespace) -> None:
    data = load_state(args.state, allow_missing=True)
    validate_score("hints", args.hints, 0, 6)
    validate_score("explain-back", args.explain_back, 0, 4)
    validate_score("transfer", args.transfer, 0, 4)
    validate_score("confidence", args.confidence, 1, 5)
    if args.minutes < 0:
        raise SystemExit("--minutes cannot be negative")
    if args.evaluator == "independent" and args.evaluator_context != "isolated":
        raise SystemExit("independent evaluator requires --evaluator-context isolated")
    if args.evaluator == "independent" and not args.package_id:
        raise SystemExit("independent evaluator requires --package-id for the frozen challenge")
    if args.phase in {"baseline", "immediate_transfer", "retention_7d", "retention_21d", "final"}:
        if args.assistance not in {"strict_unaided", "standard_unaided"}:
            raise SystemExit(f"phase {args.phase} must use an unaided assistance policy")

    session_day = args.date or date.today()
    concept_id = args.concept_id or slugify(args.topic)
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
        "minutes": args.minutes,
        "notes": args.notes or "",
        "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    data["sessions"].append(session)
    card = find_card(data, concept_id)
    if card is None:
        card = new_card(concept_id, args.topic, session_day)
        data["cards"].append(card)
    update_schedule(card, session_day, recall, args.confidence)
    save_state(args.state, data)
    print(
        f"Recorded session {len(data['sessions'])}; concept={concept_id} "
        f"recall={recall} next_due={card['due']}"
    )


def cmd_review(args: argparse.Namespace) -> None:
    data = load_state(args.state)
    validate_score("confidence", args.confidence, 1, 5)
    card = find_card(data, args.concept_id)
    if card is None:
        raise SystemExit(f"Unknown concept id: {args.concept_id}")
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
        (card for card in data["cards"] if parse_day(card["due"]) <= today),
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
        independent = sum(item.get("outcome") == "independent" for item in sessions)
        transfers = [int(item.get("transfer", 0)) for item in sessions]
        hints = [int(item.get("highest_hint", 0)) for item in sessions]
        calibrated = [item.get("confidence_calibration") for item in sessions]
        print(f"Independent outcomes: {independent}/{len(sessions)}")
        print(f"Average highest hint: {sum(hints) / len(hints):.2f}/6")
        print(f"Average immediate transfer: {sum(transfers) / len(transfers):.2f}/4")
        print(f"Confident-wrong attempts: {calibrated.count('confident_wrong')}")
        print(f"Uncertain-correct attempts: {calibrated.count('uncertain_correct')}")
        deviations = sum(bool(item.get("policy_deviations")) for item in sessions)
        print(f"Sessions with policy deviations: {deviations}")
        for phase in sorted({str(item.get("phase", "practice")) for item in sessions}):
            items = [item for item in sessions if item.get("phase", "practice") == phase]
            average_transfer = sum(int(item.get("transfer", 0)) for item in items) / len(items)
            independent_evals = sum(item.get("evaluator") == "independent" for item in items)
            print(
                f"Phase {phase}: n={len(items)} transfer={average_transfer:.2f}/4 "
                f"independent_evals={independent_evals}"
            )
        for capability in sorted({str(item.get("capability", "unclassified")) for item in sessions}):
            items = [item for item in sessions if item.get("capability", "unclassified") == capability]
            average_transfer = sum(int(item.get("transfer", 0)) for item in items) / len(items)
            print(f"Capability {capability}: n={len(items)} transfer={average_transfer:.2f}/4")
    if cards:
        average_stability = sum(float(card["stability_days"]) for card in cards) / len(cards)
        print(f"Average stability: {average_stability:.2f} days")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create an empty state file")
    init.add_argument("--state", type=Path, required=True)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    configure = subparsers.add_parser(
        "configure-program", help="define a 6-8 week longitudinal evaluation program"
    )
    configure.add_argument("--state", type=Path, required=True)
    configure.add_argument("--objective", choices=sorted(VALID_OBJECTIVES), required=True)
    configure.add_argument("--duration-weeks", type=int, default=8)
    configure.add_argument("--started-on", type=parse_day)
    configure.add_argument(
        "--baseline-policy",
        choices=["strict_unaided", "standard_unaided"],
        default="standard_unaided",
    )
    configure.add_argument("--capability", action="append", choices=sorted(VALID_CAPABILITIES))
    configure.add_argument("--success-rule", required=True)
    configure.set_defaults(func=cmd_configure)

    record = subparsers.add_parser("record", help="record a session and schedule its concept")
    record.add_argument("--state", type=Path, required=True)
    record.add_argument("--date", type=parse_day)
    record.add_argument("--concept-id")
    record.add_argument("--topic", required=True)
    record.add_argument("--exercise", required=True)
    record.add_argument("--mode", required=True)
    record.add_argument("--capability", choices=sorted(VALID_CAPABILITIES), required=True)
    record.add_argument("--phase", choices=sorted(VALID_PHASES), default="practice")
    record.add_argument("--assistance", choices=sorted(VALID_ASSISTANCE), default="coached")
    record.add_argument("--evaluator", choices=sorted(VALID_EVALUATORS), default="coach")
    record.add_argument(
        "--evaluator-context", choices=sorted(VALID_EVALUATOR_CONTEXTS), default="coaching"
    )
    record.add_argument("--package-id")
    record.add_argument("--policy-deviations")
    record.add_argument("--initial-result", choices=sorted(VALID_INITIAL_RESULTS), required=True)
    record.add_argument("--confidence", type=int, required=True)
    record.add_argument("--outcome", choices=sorted(VALID_OUTCOMES), required=True)
    record.add_argument("--hints", type=int, required=True)
    record.add_argument("--explain-back", type=int, required=True)
    record.add_argument("--transfer", type=int, required=True)
    record.add_argument("--minutes", type=int, required=True)
    record.add_argument("--notes")
    record.set_defaults(func=cmd_record)

    review = subparsers.add_parser("review", help="grade recall and adapt its next due date")
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
