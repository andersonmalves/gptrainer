#!/usr/bin/env python3
"""Compile and run local coding-challenge tests in a disposable directory."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


LANGUAGES = {
    "python": {"extensions": {".py"}, "tools": ("python3",)},
    "typescript": {"extensions": {".ts"}, "tools": ("node", "tsc")},
    "java": {"extensions": {".java"}, "tools": ("java", "javac")},
    "kotlin": {"extensions": {".kt"}, "tools": ("java", "kotlinc")},
}
ALIASES = {"py": "python", "ts": "typescript", "kt": "kotlin"}


@dataclass
class Result:
    status: str
    phase: str
    returncode: int | None
    stdout: str
    stderr: str


def normalize_language(value: str) -> str:
    language = ALIASES.get(value.lower(), value.lower())
    if language not in LANGUAGES:
        raise argparse.ArgumentTypeError(f"unsupported language: {value}")
    return language


def find_tool(name: str) -> str | None:
    return shutil.which(name)


def clean_environment(workspace: Path) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(workspace),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if os.name == "nt":
        for name in ("SYSTEMROOT", "WINDIR", "PATHEXT"):
            if name in os.environ:
                env[name] = os.environ[name]
    return env


def resource_limiter(timeout: int, memory_mb: int, limit_address_space: bool):
    if os.name != "posix":
        return None
    try:
        import resource
    except ImportError:
        return None

    def limit() -> None:
        try:
            os.setsid()
        except OSError:
            pass

        def apply(kind: int, soft: int, hard: int) -> None:
            try:
                _, current_hard = resource.getrlimit(kind)
                if current_hard != resource.RLIM_INFINITY:
                    hard = min(hard, current_hard)
                    soft = min(soft, hard)
                resource.setrlimit(kind, (soft, hard))
            except (OSError, ValueError):
                pass

        apply(resource.RLIMIT_CPU, timeout, timeout + 1)
        if limit_address_space:
            memory_bytes = memory_mb * 1024 * 1024
            apply(resource.RLIMIT_AS, memory_bytes, memory_bytes)
        apply(resource.RLIMIT_FSIZE, 16 * 1024 * 1024, 16 * 1024 * 1024)
        apply(resource.RLIMIT_NOFILE, 64, 64)
        if hasattr(resource, "RLIMIT_NPROC") and sys.platform != "darwin":
            apply(resource.RLIMIT_NPROC, 32, 32)

    return limit


def run_process(
    command: Sequence[str],
    workspace: Path,
    timeout: int,
    memory_mb: int,
    apply_limits: bool,
    limit_address_space: bool = False,
) -> Result:
    preexec = (
        resource_limiter(timeout, memory_mb, limit_address_space)
        if apply_limits
        else (getattr(os, "setsid", None) if os.name == "posix" else None)
    )
    try:
        proc = subprocess.Popen(
            list(command),
            cwd=workspace,
            env=clean_environment(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout + 1)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except OSError:
                    proc.kill()
            else:
                proc.kill()
            try:
                stdout, stderr = proc.communicate(timeout=1)
            except (subprocess.TimeoutExpired, ValueError):
                stdout, stderr = "", ""
            return Result(
                status="timeout",
                phase="run",
                returncode=None,
                stdout=stdout or "",
                stderr=stderr or f"Timed out after {timeout} seconds",
            )
        except Exception:
            if os.name == "posix":
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except OSError:
                    proc.kill()
            else:
                proc.kill()
            proc.wait()
            raise
    except OSError as exc:
        return Result(status="error", phase="run", returncode=None, stdout="", stderr=str(exc))

    cpu_signals = {-getattr(signal, "SIGXCPU", signal.SIGTERM)}
    status = "passed" if proc.returncode == 0 else "failed"
    if proc.returncode in cpu_signals:
        status = "timeout"
    return Result(
        status=status,
        phase="run",
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
    )


def compile_sources(command: Sequence[str], workspace: Path, timeout: int) -> Result:
    result = run_process(command, workspace, timeout, 2048, apply_limits=False)
    result.phase = "compile"
    if result.status == "passed":
        result.status = "compiled"
    return result


def copy_sources(paths: Sequence[Path], workspace: Path, extensions: set[str]) -> list[Path]:
    copied: list[Path] = []
    names: set[str] = set()
    for source in paths:
        source = source.resolve()
        if not source.is_file():
            raise SystemExit(f"Source file not found: {source}")
        if source.suffix.lower() not in extensions:
            raise SystemExit(f"Unexpected extension for selected language: {source.name}")
        if source.name in names:
            raise SystemExit(f"Duplicate source filename: {source.name}")
        names.add(source.name)
        target = workspace / source.name
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def build_commands(
    language: str,
    files: list[Path],
    test_file: Path,
    entry: str | None,
    memory_mb: int,
    workspace: Path,
) -> tuple[list[str] | None, list[str], bool]:
    names = [path.name for path in files]
    if language == "python":
        bootstrap = (
            "import runpy,sys; "
            "sys.path.insert(0, '.'); "
            "runpy.run_path(sys.argv[1], run_name='__main__')"
        )
        return None, [sys.executable, "-I", "-B", "-c", bootstrap, test_file.name], True

    if language == "typescript":
        tsc = find_tool("tsc")
        node = find_tool("node")
        if not tsc or not node:
            raise SystemExit("TypeScript runner requires both tsc and node on PATH")
        build = workspace / "build"
        compile_command = [
            tsc,
            "--pretty",
            "false",
            "--strict",
            "--target",
            "ES2022",
            "--module",
            "commonjs",
            "--moduleResolution",
            "node",
            "--skipLibCheck",
            "--outDir",
            str(build),
            *names,
        ]
        run_command = [
            node,
            "--disable-proto=throw",
            f"--max-old-space-size={memory_mb}",
            str(build / f"{test_file.stem}.js"),
        ]
        return compile_command, run_command, False

    if language == "java":
        javac = find_tool("javac")
        java = find_tool("java")
        if not javac or not java:
            raise SystemExit("Java runner requires both javac and java on PATH")
        build = workspace / "build"
        build.mkdir()
        class_name = entry or test_file.stem
        return (
            [javac, "-encoding", "UTF-8", "-d", str(build), *names],
            [java, f"-Xmx{memory_mb}m", "-cp", str(build), class_name],
            False,
        )

    kotlinc = find_tool("kotlinc")
    java = find_tool("java")
    if not kotlinc or not java:
        raise SystemExit("Kotlin runner requires both kotlinc and java on PATH")
    jar = workspace / "challenge.jar"
    return (
        [kotlinc, *names, "-include-runtime", "-d", str(jar)],
        [java, f"-Xmx{memory_mb}m", "-jar", str(jar)],
        False,
    )


ANSI_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    return ANSI_PATTERN.sub("", text)


def sanitize(result: Result, workspace: Path) -> Result:
    marker = str(workspace)
    result.stdout = strip_ansi(result.stdout.replace(marker, "<workspace>"))
    result.stderr = strip_ansi(result.stderr.replace(marker, "<workspace>"))
    return result


def emit(result: Result, as_json: bool) -> None:
    if as_json:
        print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))
        return
    print(f"status={result.status} phase={result.phase} returncode={result.returncode}")
    if result.stdout:
        print("stdout:")
        print(result.stdout.rstrip())
    if result.stderr:
        print("stderr:")
        print(result.stderr.rstrip())


def cmd_doctor(_: argparse.Namespace) -> None:
    for language, config in LANGUAGES.items():
        tools = (
            {"python": sys.executable}
            if language == "python"
            else {name: find_tool(name) for name in config["tools"]}
        )
        ready = all(tools.values())
        locations = ", ".join(f"{name}={path or 'missing'}" for name, path in tools.items())
        print(f"{language}: {'ready' if ready else 'unavailable'} ({locations})")


def cmd_run(args: argparse.Namespace) -> None:
    if not 1 <= args.timeout <= 60:
        raise SystemExit("--timeout must be between 1 and 60 seconds")
    if not 64 <= args.memory_mb <= 4096:
        raise SystemExit("--memory-mb must be between 64 and 4096")

    language = args.language
    extensions = LANGUAGES[language]["extensions"]
    sources = [args.solution, args.tests, *args.support]
    with tempfile.TemporaryDirectory(prefix="coding-reasoning-") as temporary:
        workspace = Path(temporary)
        copied = copy_sources(sources, workspace, extensions)
        copied_by_name = {path.name: path for path in copied}
        test_file = copied_by_name[args.tests.name]
        compile_command, run_command, limit_address_space = build_commands(
            language,
            copied,
            test_file,
            args.entry,
            args.memory_mb,
            workspace,
        )
        if compile_command:
            compile_result = sanitize(
                compile_sources(compile_command, workspace, max(15, args.timeout)), workspace
            )
            if compile_result.status != "compiled":
                emit(compile_result, args.json)
                raise SystemExit(1)
        result = sanitize(
            run_process(
                run_command,
                workspace,
                args.timeout,
                args.memory_mb,
                apply_limits=True,
                limit_address_space=limit_address_space,
            ),
            workspace,
        )
        emit(result, args.json)
        raise SystemExit(0 if result.status == "passed" else 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser("doctor", help="show available language toolchains")
    doctor.set_defaults(func=cmd_doctor)

    run = subparsers.add_parser("run", help="compile and execute a challenge test file")
    run.add_argument("--language", type=normalize_language, required=True)
    run.add_argument("--solution", type=Path, required=True)
    run.add_argument("--tests", type=Path, required=True)
    run.add_argument("--support", type=Path, action="append", default=[])
    run.add_argument("--entry", help="Java test class containing main; defaults to test filename")
    run.add_argument("--timeout", type=int, default=5)
    run.add_argument("--memory-mb", type=int, default=512)
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=cmd_run)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
