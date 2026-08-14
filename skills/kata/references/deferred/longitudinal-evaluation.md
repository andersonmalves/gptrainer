# Longitudinal evaluation

> **Deferred — not a current capability.** Nothing in the package implements or enforces this protocol, and the skill does not instruct the coach to run it. Kept as design input for [future-improvements.md](../future-improvements.md).
>
> **Why it is deferred.** Two sessions per week over eight weeks across five capabilities yields roughly three to five observations per capability, scored by the coach on an ordinal 0–4 scale. That cannot support the threshold decision rules below: ordinary variation between non-equivalent tasks dominates any effect that size, and practice effects and regression to the mean have no control here. Difficulty equivalence across tasks depends on the validated challenge bank, which does not exist yet.
>
> **What would have to exist first.** The validated challenge bank, a scoring path isolated from the coaching context, and a pre-registered analysis that reports uncertainty rather than a threshold verdict.

Use this protocol to estimate whether the trainer helps this learner. It is an N-of-1 evaluation unless multiple participants are enrolled; it can guide decisions but does not establish general efficacy.

## Define the claim

Choose one objective before baseline:

- `recover`: regain previously demonstrated unaided performance;
- `prevent_decline`: maintain performance while AI use continues;
- `improve_baseline`: exceed current unaided performance.

Write a falsifiable success rule. Example: “At week 8, improve mean unaided transfer by at least 0.75/4, reduce highest hint by at least one level in practice, and show no regression in median completion time greater than 20%.” Treat thresholds as learner-defined decision rules, not scientifically universal cutoffs.

## Schedule: 6–8 weeks

| Phase | Timing | Assistance | Purpose |
|---|---|---|---|
| Baseline | Week 0 | `standard_unaided` or `strict_unaided` | Estimate starting performance with 3–5 tasks |
| Practice | Weeks 1–6/8 | `coached` | Train demonstrated gaps, 2–3 short sessions/week |
| Immediate transfer | Each practice session | Same unaided policy | Test a structurally related novel task after hints are removed |
| Retention | 7 days after target concept | Same unaided policy | Test delayed retrieval with a novel surface form |
| Retention | 21 days after target concept | Same unaided policy | Test more durable retention |
| Final | Last week | Same baseline policy | Re-sample capability families with matched, non-identical tasks |

Avoid retesting the same wording or answer. Match difficulty using constraints, expected reasoning steps, timebox, and scoring anchors rather than subjective labels alone.

## Comparison conditions

When feasible, rotate matched tasks across:

1. no AI (`standard_unaided` or `strict_unaided`);
2. conventional AI (`conventional_ai`);
3. guarded trainer (`coached`, followed by unaided transfer/retention).

Counterbalance task families when possible so one condition does not always receive easier or later tasks. With a single learner and few observations, report descriptive differences and uncertainty; do not call them causal effects.

Follow every assisted condition with a matched unaided probe. A comparison of no-AI work against work completed with conventional AI measures assisted performance, not learning. For `prevent_decline`, require repeated baseline-quality probes over time; one pre/post difference cannot distinguish prevention from ordinary variation.

## Outcomes

Primary:

- unaided immediate-transfer score;
- unaided 7-day and 21-day retention score;
- debugging/diagnosis accuracy on the selected capability mix;
- highest conceptual hint during practice;
- confidence calibration, especially confident-wrong rate.

Secondary:

- completion time;
- explain-back score;
- incomplete/abandoned attempts;
- policy deviations and environment failures.

Do not combine these into a single mastery percentage. Compare distributions, medians, and task-level evidence. Separate assisted completion from every unaided outcome.

## Minimum interpretation

- Fewer than two comparable tasks per capability: insufficient capability-level evidence.
- Improvement only on practiced wording: possible memorization, not transfer.
- Immediate gain without 7/21-day retention: short-term performance, not durable learning.
- Better scores with much greater time: report the tradeoff.
- Coach-scored checkpoints: potentially contaminated; require independent confirmation before a strong claim.
