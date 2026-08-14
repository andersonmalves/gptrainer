# Adaptive review protocol

Use this protocol when recording confidence or running delayed reviews.

## Confidence before feedback

Ask for confidence **after the learner commits to an answer and before revealing correctness**:

> De 1 a 5, quão confiante você está nessa resposta?

Use the same scale consistently:

| Value | Meaning |
|---:|---|
| 1 | Guessing |
| 2 | Low confidence |
| 3 | Reasonably confident |
| 4 | High confidence |
| 5 | Certain |

Do not ask after revealing a test result or correction; that destroys the calibration measurement. Do not treat confidence as correctness.

Flag two useful mismatches:

- **Confident wrong**: incorrect or only partially correct at confidence 4–5. Review soon and diagnose the faulty mental model.
- **Uncertain correct**: correct at confidence 1–2. Reinforce the causal explanation and retest in a changed context.

## Recall ratings

The coach assigns the rating from observable unaided performance:

| Rating | Evidence |
|---|---|
| `again` | Cannot retrieve or applies the wrong model |
| `hard` | Partially correct, slow with a material gap, or correct only after minor scaffolding |
| `good` | Correct independently with an adequate explanation |
| `easy` | Immediate, accurate transfer plus a strong explanation |

Do not let the learner choose the rating based only on how the review felt.

## Scheduler limits

`scripts/progress.py` uses a deterministic interval heuristic with concept-level stability and difficulty. Growth constants are arbitrary. It is **not** FSRS and must not be described as FSRS-inspired in a way that implies Anki/FSRS validation.

- Only **unaided** sessions (`strict_unaided` or `standard_unaided`) update stability and difficulty.
- Assisted sessions may create a concept card due in 7 days; they do not count as recall evidence.
- `review` requires a recorded unaided session for that concept.
- `retention_7d` and `retention_21d` require a prior session for the concept and at least 7 or 21 days since that last session.
- Failed unaided recall reduces stability and increases difficulty.
- Confident-wrong recall is scheduled for the next day.
- Hard recall grows the interval slowly.
- Good and easy recall grow the interval increasingly as difficulty falls.
- Low-confidence correct recall receives a smaller interval increase.
- Intervals are capped at 365 days.

The state contains no solution text. Use stable concept IDs such as `payment-idempotency-race`, not one ID per exercise wording.

## Commands

Record a session only after asking for confidence before feedback:

```bash
python scripts/progress.py record --state .coding-reasoning/progress.json \
  --date 2026-01-01 --concept-id payment-idempotency-race --topic "payment idempotency" \
  --exercise "concurrent duplicate requests" --mode debug \
  --capability invariants_failures --phase practice \
  --assistance coached --evaluator coach \
  --initial-result incorrect --confidence 4 \
  --outcome lightly_assisted --hints 2 --explain-back 3 --transfer 2 --minutes 28
```

List due concepts. Grade recall only after an unaided session exists for that concept:

```bash
python scripts/progress.py due --state .coding-reasoning/progress.json
python scripts/progress.py record --state .coding-reasoning/progress.json \
  --date 2026-01-08 --concept-id payment-idempotency-race \
  --topic "payment idempotency" --exercise "redelivery of the same key" \
  --mode debug --capability invariants_failures --phase retention_7d \
  --assistance standard_unaided --evaluator coach \
  --initial-result correct --confidence 3 --outcome independent \
  --hints 0 --explain-back 3 --minutes 20
python scripts/progress.py review --state .coding-reasoning/progress.json \
  --concept-id payment-idempotency-race --recall good --confidence 3 \
  --on 2026-01-08
```

`record` rejects internally inconsistent sessions: the hint level must match the outcome band in [rubric.md](rubric.md), `independent` requires a correct first answer, a correct first answer cannot be `heavily_assisted` or `walked_through`, `conventional_ai` cannot be scored as `independent` or carry an unaided transfer score, and an unaided policy or phase forbids conceptual hints. Fix the field that is wrong rather than relabelling the session to satisfy the command.

`--transfer` is optional and carries its own `--transfer-policy`, because the transfer task is unaided even when the session was coached. Omit `--transfer` when no transfer task was given; do not record a zero.

When a version-1 state file is read, the script migrates its sessions in memory and creates conservative concept cards. Version-2 files retain their cards and receive explicit program/evaluation metadata defaults. Version-3 files keep their program and cards, and their transfer scores are labelled `standard_unaided` because that field predates the explicit policy. Sessions recorded under the retired `immediate_transfer` phase stay readable. The next writing command saves schema version 4.
