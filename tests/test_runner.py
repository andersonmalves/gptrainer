"""Tests for scripts/runner.py — stdlib only, Python toolchain only.

Java, Kotlin and TypeScript paths are skipped when their toolchains are absent so
the suite stays runnable on any machine.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "runner.py"

SOLUTION = "def allocate(total, parts):\n    return [total // parts] * parts\n"
PASSING_TEST = 'from solution import allocate\n\nassert allocate(10, 2) == [5, 5]\nprint("PASS")\n'
FAILING_TEST = "from solution import allocate\n\nassert allocate(10, 2) == [4, 6]\n"


class PythonRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        (self.root / "solution.py").write_text(SOLUTION, encoding="utf-8")

    def run_challenge(self, test_source: str, *extra: str) -> subprocess.CompletedProcess:
        test_file = self.root / "challenge_test.py"
        test_file.write_text(test_source, encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "run",
                "--language",
                "python",
                "--solution",
                str(self.root / "solution.py"),
                "--tests",
                str(test_file),
                "--timeout",
                "5",
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_passing_tests_exit_zero(self) -> None:
        result = self.run_challenge(PASSING_TEST)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("status=passed", result.stdout)

    def test_failing_tests_exit_nonzero(self) -> None:
        result = self.run_challenge(FAILING_TEST)
        self.assertEqual(result.returncode, 1)
        self.assertIn("status=failed", result.stdout)

    def test_json_output_is_machine_readable(self) -> None:
        result = self.run_challenge(PASSING_TEST, "--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["phase"], "run")

    def test_cpu_bound_hang_is_stopped(self) -> None:
        result = self.run_challenge("while True:\n    pass\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("status=timeout", result.stdout)

    def test_workspace_path_is_not_leaked(self) -> None:
        result = self.run_challenge(FAILING_TEST)
        self.assertNotIn("coding-reasoning-", result.stdout)


class ArgumentValidationTest(unittest.TestCase):
    def run_runner(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(RUNNER), *argv], capture_output=True, text=True, check=False
        )

    def test_unsupported_language_is_rejected(self) -> None:
        result = self.run_runner(
            "run", "--language", "cobol", "--solution", "s.cob", "--tests", "t.cob"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported language", result.stderr)

    def test_timeout_outside_bounds_is_rejected(self) -> None:
        result = self.run_runner(
            "run",
            "--language",
            "python",
            "--solution",
            "s.py",
            "--tests",
            "t.py",
            "--timeout",
            "600",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--timeout must be between 1 and 60", result.stderr)

    def test_doctor_reports_every_language(self) -> None:
        result = self.run_runner("doctor")
        self.assertEqual(result.returncode, 0)
        for language in ("python", "typescript", "java", "kotlin"):
            self.assertIn(language, result.stdout)


if __name__ == "__main__":
    unittest.main()
