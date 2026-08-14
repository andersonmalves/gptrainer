"""Tests for scripts/progress.py — stdlib only, no external dependencies."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import progress  # noqa: E402


COHERENT = {
    "concept_id": "payment-idempotency-race",
    "topic": "payment idempotency",
    "exercise": "race in idempotency guard",
    "mode": "debug",
    "capability": "invariants_failures",
    "phase": "practice",
    "assistance": "coached",
    "initial_result": "incorrect",
    "confidence": 4,
    "outcome": "lightly_assisted",
    "hints": 2,
    "explain_back": 3,
    "transfer": 2,
    "minutes": 28,
}


def record_args(**overrides) -> list[str]:
    fields = {**COHERENT, **overrides}
    args = []
    for key, value in fields.items():
        args += [f"--{key.replace('_', '-')}", str(value)]
    return args


class RecordValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = tempfile.TemporaryDirectory()
        self.state = Path(self.workspace.name) / "progress.json"
        self.addCleanup(self.workspace.cleanup)

    def run_command(self, argv: list[str]) -> None:
        parser = progress.build_parser()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            args = parser.parse_args(argv)
            args.func(args)

    def record(self, **overrides) -> None:
        self.run_command(["record", "--state", str(self.state), *record_args(**overrides)])

    def test_accepts_a_coherent_session(self) -> None:
        self.record()
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(len(state["sessions"]), 1)
        self.assertEqual(len(state["cards"]), 1)
        self.assertEqual(state["sessions"][0]["confidence_calibration"], "confident_wrong")

    def test_rejects_outcome_above_its_hint_range(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            self.record(outcome="independent", initial_result="correct", hints=6)
        self.assertIn("--hints between 0 and 1", str(caught.exception))

    def test_rejects_independent_outcome_after_a_wrong_answer(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            self.record(outcome="independent", initial_result="incorrect", hints=0)
        self.assertIn("--initial-result correct", str(caught.exception))

    def test_rejects_hints_under_an_unaided_policy(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            self.record(
                phase="retention_7d",
                assistance="standard_unaided",
                outcome="lightly_assisted",
                hints=2,
            )
        self.assertIn("forbids conceptual hints", str(caught.exception))

    def test_rejects_an_unaided_phase_with_a_coached_policy(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            self.record(phase="retention_7d", assistance="coached")
        self.assertIn("must use an unaided assistance policy", str(caught.exception))

    def test_rejects_incomplete_paired_with_a_correct_answer(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            self.record(outcome="incomplete", initial_result="correct", hints=0)
        self.assertIn("cannot pair with", str(caught.exception))

    def test_transfer_is_optional_and_defaults_to_no_attempt(self) -> None:
        argv = ["record", "--state", str(self.state)]
        for key, value in COHERENT.items():
            if key == "transfer":
                continue
            argv += [f"--{key.replace('_', '-')}", str(value)]
        self.run_command(argv)
        session = json.loads(self.state.read_text(encoding="utf-8"))["sessions"][0]
        self.assertIsNone(session["transfer"])
        self.assertIsNone(session["transfer_policy"])

    def test_transfer_carries_an_unaided_policy_inside_a_coached_session(self) -> None:
        self.record()
        session = json.loads(self.state.read_text(encoding="utf-8"))["sessions"][0]
        self.assertEqual(session["assistance"], "coached")
        self.assertEqual(session["transfer_policy"], "standard_unaided")

    def test_immediate_transfer_is_no_longer_a_recordable_phase(self) -> None:
        with self.assertRaises(SystemExit):
            self.record(phase="immediate_transfer")

    def test_accepts_a_clean_unaided_retention_session(self) -> None:
        self.record(
            phase="retention_7d",
            assistance="standard_unaided",
            outcome="independent",
            initial_result="correct",
            confidence=4,
            hints=0,
        )
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(state["sessions"][0]["phase"], "retention_7d")


class StateMigrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = tempfile.TemporaryDirectory()
        self.state = Path(self.workspace.name) / "progress.json"
        self.addCleanup(self.workspace.cleanup)

    def write(self, payload: dict) -> None:
        self.state.write_text(json.dumps(payload), encoding="utf-8")

    def test_v2_card_without_scheduler_fields_is_normalized(self) -> None:
        self.write(
            {
                "schema_version": 2,
                "sessions": [],
                "cards": [{"id": "c1", "topic": "t", "stability_days": 3.0, "due": "2026-01-01"}],
            }
        )
        data = progress.load_state(self.state)
        card = data["cards"][0]
        self.assertEqual(card["difficulty"], 5.0)
        self.assertEqual(card["calibration"], "unknown")

    def test_card_without_id_or_due_fails_loudly(self) -> None:
        self.write({"schema_version": 3, "program": None, "sessions": [], "cards": [{"id": "c1"}]})
        with self.assertRaises(SystemExit) as caught:
            progress.load_state(self.state)
        self.assertIn("missing required field 'due'", str(caught.exception))

    def test_v3_transfer_score_gains_an_explicit_unaided_policy(self) -> None:
        self.write(
            {
                "schema_version": 3,
                "program": {"objective": "improve_baseline"},
                "sessions": [{"topic": "t", "assistance": "coached", "transfer": 3}],
                "cards": [],
            }
        )
        data = progress.load_state(self.state)
        self.assertEqual(data["sessions"][0]["transfer_policy"], "standard_unaided")
        self.assertEqual(data["program"]["objective"], "improve_baseline")

    def test_v3_session_without_transfer_stays_unrecorded(self) -> None:
        self.write(
            {"schema_version": 3, "program": None, "sessions": [{"topic": "t"}], "cards": []}
        )
        session = progress.load_state(self.state)["sessions"][0]
        self.assertIsNone(session["transfer"])
        self.assertIsNone(session["transfer_policy"])

    def test_retired_immediate_transfer_phase_stays_readable(self) -> None:
        self.write(
            {
                "schema_version": 3,
                "program": None,
                "sessions": [{"topic": "t", "phase": "immediate_transfer", "transfer": 4}],
                "cards": [],
            }
        )
        self.assertEqual(progress.load_state(self.state)["sessions"][0]["phase"], "immediate_transfer")

    def test_unsupported_schema_is_rejected(self) -> None:
        self.write({"schema_version": 99, "sessions": [], "cards": []})
        with self.assertRaises(SystemExit):
            progress.load_state(self.state)


class SchedulerTest(unittest.TestCase):
    def card(self, **overrides) -> dict:
        return {**progress.new_card("c", "topic", date(2026, 1, 1)), **overrides}

    def test_confident_wrong_is_scheduled_for_the_next_day(self) -> None:
        card = self.card(stability_days=40.0)
        progress.update_schedule(card, date(2026, 1, 1), "again", 5)
        self.assertEqual(card["due"], "2026-01-02")
        self.assertEqual(card["calibration"], "confident_wrong")
        self.assertEqual(card["lapses"], 1)

    def test_failed_recall_reduces_stability_and_raises_difficulty(self) -> None:
        card = self.card(stability_days=10.0, difficulty=5.0)
        progress.update_schedule(card, date(2026, 1, 1), "again", 2)
        self.assertLess(card["stability_days"], 10.0)
        self.assertGreater(card["difficulty"], 5.0)

    def test_low_confidence_shrinks_a_good_interval(self) -> None:
        confident = self.card(stability_days=10.0)
        unsure = self.card(stability_days=10.0)
        progress.update_schedule(confident, date(2026, 1, 1), "good", 4)
        progress.update_schedule(unsure, date(2026, 1, 1), "good", 2)
        self.assertLess(unsure["stability_days"], confident["stability_days"])
        self.assertEqual(unsure["calibration"], "uncertain_correct")

    def test_interval_is_capped_at_one_year(self) -> None:
        card = self.card(stability_days=900.0, difficulty=1.0)
        progress.update_schedule(card, date(2026, 1, 1), "easy", 5)
        self.assertEqual(card["due"], (date(2026, 1, 1) + timedelta(days=365)).isoformat())

    def test_invalid_recall_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            progress.update_schedule(self.card(), date(2026, 1, 1), "sort-of", 3)


class StatusReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = tempfile.TemporaryDirectory()
        self.state = Path(self.workspace.name) / "progress.json"
        self.addCleanup(self.workspace.cleanup)
        parser = progress.build_parser()
        for overrides in (
            {},
            {
                "concept_id": "retention-check",
                "capability": "code_reading",
                "phase": "retention_7d",
                "assistance": "standard_unaided",
                "outcome": "independent",
                "initial_result": "correct",
                "hints": 0,
                "transfer": 4,
            },
        ):
            args = parser.parse_args(
                ["record", "--state", str(self.state), *record_args(**overrides)]
            )
            with contextlib.redirect_stdout(io.StringIO()):
                args.func(args)

    def status_output(self) -> str:
        parser = progress.build_parser()
        args = parser.parse_args(["status", "--state", str(self.state)])
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            args.func(args)
        return buffer.getvalue()

    def test_separates_unaided_from_assisted_sessions(self) -> None:
        output = self.status_output()
        self.assertIn("Unaided sessions: 1", output)
        self.assertIn("Assisted sessions: 1", output)

    def test_reports_medians_instead_of_a_pooled_mean(self) -> None:
        output = self.status_output()
        self.assertIn("median=", output)
        self.assertNotIn("Average immediate transfer", output)
        self.assertNotIn("Average highest hint", output)

    def test_flags_capabilities_with_a_single_task(self) -> None:
        self.assertIn("[insufficient: <2 tasks]", self.status_output())

    def test_transfer_is_reported_outside_the_assistance_blocks(self) -> None:
        output = self.status_output()
        assisted_block = output.split("Assisted sessions:")[1].split("Transfer attempts")[0]
        self.assertNotIn("Transfer", assisted_block)
        self.assertIn("Transfer attempts (unaided by protocol): n=2", output)
        self.assertIn("standard_unaided: n=2", output)


class DeferredProgramTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = tempfile.TemporaryDirectory()
        self.state = Path(self.workspace.name) / "progress.json"
        self.addCleanup(self.workspace.cleanup)

    def test_configure_program_is_no_longer_offered(self) -> None:
        parser = progress.build_parser()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["configure-program", "--state", str(self.state)])

    def test_a_legacy_program_stays_readable(self) -> None:
        self.state.write_text(
            json.dumps(
                {
                    "schema_version": 3,
                    "program": {
                        "objective": "improve_baseline",
                        "duration_weeks": 8,
                        "baseline_policy": "standard_unaided",
                    },
                    "sessions": [],
                    "cards": [],
                }
            ),
            encoding="utf-8",
        )
        parser = progress.build_parser()
        args = parser.parse_args(["status", "--state", str(self.state)])
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            args.func(args)
        self.assertIn("Program: improve_baseline", buffer.getvalue())


class LabelTest(unittest.TestCase):
    def test_calibration_labels(self) -> None:
        self.assertEqual(progress.calibration_label("incorrect", 4), "confident_wrong")
        self.assertEqual(progress.calibration_label("correct", 2), "uncertain_correct")
        self.assertEqual(progress.calibration_label("correct", 4), "calibrated")

    def test_initial_recall_mapping(self) -> None:
        self.assertEqual(progress.initial_recall("independent", "incorrect", 4, 4), "again")
        self.assertEqual(progress.initial_recall("walked_through", "partial", 1, 1), "hard")
        self.assertEqual(progress.initial_recall("independent", "correct", 3, 4), "easy")
        self.assertEqual(progress.initial_recall("independent", "correct", 2, 2), "good")


if __name__ == "__main__":
    unittest.main()
