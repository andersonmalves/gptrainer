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

- **Confident wrong**: incorrect at confidence 4–5. Review soon and diagnose the faulty mental model.
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

`scripts/progress.py` uses a deterministic, FSRS-inspired model with concept-level stability and difficulty. It is **not** the official FSRS algorithm and must not be described as one.

- Failed recall reduces stability and increases difficulty.
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
  --concept-id payment-idempotency-race --topic "payment idempotency" \
  --exercise "concurrent duplicate requests" --mode debug \
  --capability invariants_failures --phase practice \
  --assistance coached --evaluator coach \
  --initial-result incorrect --confidence 4 \
  --outcome lightly_assisted --hints 2 --explain-back 3 --transfer 2 --minutes 28
```

List due concepts and record an unaided review:

```bash
python scripts/progress.py due --state .coding-reasoning/progress.json
python scripts/progress.py review --state .coding-reasoning/progress.json \
  --concept-id payment-idempotency-race --recall good --confidence 3
```

`record` rejects internally inconsistent sessions: the hint level must match the outcome band in [rubric.md](rubric.md), `independent` requires a correct first answer, and an unaided policy or phase forbids conceptual hints. Fix the field that is wrong rather than relabelling the session to satisfy the command.

When a version-1 state file is read, the script migrates its sessions in memory and creates conservative concept cards. Version-2 files retain their cards and receive explicit program/evaluation metadata defaults. The next writing command saves schema version 3.
