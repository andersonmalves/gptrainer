# train-coding-reasoning

A coaching skill that trains programming reasoning without doing it for you. It requires a genuine attempt before help, releases hints one rung at a time, asks for confidence before revealing correctness, and re-tests the concept on a changed surface once the hints are gone.

The design premise is that assisted completion and learning are different things. See [references/evidence.md](references/evidence.md) for the three studies behind that premise, with their limits stated.

## What it does not establish

- **No independent score.** Nothing here isolates an evaluator from the coaching context, so every score the skill produces is `coach_scored`.
- **No validated measurement of the method.** A session demonstrates performance on that task. Trends from a single learner are not causal evidence.
- **No validated challenge bank.** Tasks are generated per session, so difficulty is not equated across attempts.

The multiweek evaluation protocol and the four-role separation that would address these live in [references/deferred/](references/deferred/) as design input, not as procedures to run. [AUDIT.md](AUDIT.md) records why.

## Layout

| Path | Contents |
|---|---|
| `SKILL.md` | The skill itself: contract, capability targets, modes, hint ladder, leakage rules |
| `references/` | Protocols loaded on demand — session flow, rubric, assistance policies, challenge design, spaced review |
| `references/deferred/` | Drafted protocols that are backlog, not current capability |
| `scripts/runner.py` | Deterministic test runner for Python, TypeScript, Java, Kotlin |
| `scripts/progress.py` | Optional practice log with FSRS-inspired scheduling |
| `agents/openai.yaml` | Interface metadata and product policy for OpenAI-side clients |
| `tests/` | Test suite for both scripts |

## Use

Claude Code discovers skills placed in `~/.claude/skills/<name>/` (personal) or `.claude/skills/<name>/` (project), with `SKILL.md` at the root of that directory.

Run a challenge against deterministic tests:

```bash
python3 scripts/runner.py doctor
python3 scripts/runner.py run --language python --solution solution.py --tests challenge_test.py
```

The runner is not a security sandbox and does not block network access — see [references/runner.md](references/runner.md).

Track practice only if you want to; the skill never creates the file on its own:

```bash
python3 scripts/progress.py init --state .coding-reasoning/progress.json
python3 scripts/progress.py due --state .coding-reasoning/progress.json
python3 scripts/progress.py status --state .coding-reasoning/progress.json
```

The log stores metadata only — no solutions, no proprietary code. `record` refuses sessions whose fields contradict the rubric, such as an `independent` outcome after a hint or conceptual hints under an unaided policy.

## Tests

Standard library only, no dependencies:

```bash
python3 -m unittest discover -s tests
```

Requires Python 3.9 or newer; verified on 3.9 and 3.14. The Java, Kotlin and TypeScript runner paths are exercised only when their toolchains are installed.

## License

MIT — see [LICENSE](LICENSE).
