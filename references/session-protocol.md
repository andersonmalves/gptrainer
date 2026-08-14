# Session protocol

Use this protocol to keep practice effortful, bounded, and measurable.

## Opening

State five items compactly:

1. Target skill.
2. Primary capability, exercise mode, and difficulty.
3. Assistance policy and timebox.
4. Deliverable.
5. What counts as success.

For an unaided measurement, read [assistance-policy.md](assistance-policy.md) and declare allowed resources before starting the timer.

Then present only the information a real engineer would reasonably have: context, observable behavior, constraints, and public examples. Avoid embedding the solution in the wording.

## Attempt gate

Before meaningful help, require an artifact that exposes reasoning. Accept one or more of:

- a restatement and assumptions;
- invariants or a state model;
- a prediction or execution trace;
- a hypothesis and diagnostic plan;
- pseudocode or a decomposition;
- code plus tests.

“Não sei” is not an attempt. Respond with a small observation task or concrete example to analyze, not the answer.

## Coaching loop

For each learner attempt:

1. Identify what is correct without generic praise.
2. Name the first consequential gap.
3. Ask the learner to test or revise it.
4. If blocked, release exactly one hint rung.
5. Require another attempt before advancing.

Keep feedback local. Do not enumerate every defect at once unless the timebox has ended.

### Hint ledger

Track hints internally during the session:

| Level | Help supplied | Example |
|---|---|---|
| 0 | No hint | Only task clarification |
| 1 | Diagnostic question | “Qual estado pode mudar entre essas duas operações?” |
| 2 | Constraint/invariant | “A mesma chave pode chegar em duas instâncias.” |
| 3 | Counterexample/trace | Interleaving with two requests |
| 4 | Concept name | “Compare-and-set” or “single-flight” |
| 5 | Partial pseudocode | One atomic sub-operation |
| 6 | Walkthrough/answer | Full reasoning or implementation |

Clarifying ambiguous requirements and fixing irrelevant syntax do not count as conceptual hints. State this distinction when scoring.

## Objective verification

Use tests, traces, counterexamples, or explicit acceptance criteria. Include normal, boundary, malformed, and adversarial cases as appropriate.

Before revealing correctness or running withheld tests, ask the learner to commit to an answer and report confidence from 1–5. Read [adaptive-review.md](adaptive-review.md) for the scale and calibration rules. Do not ask for confidence after test output is visible.

If the exercise runs in a repository:

- inspect existing conventions before scaffolding;
- avoid production mutations;
- keep learner and assistant artifacts distinguishable;
- run the narrowest relevant tests first;
- do not repair the learner's implementation.

For a standalone Python, TypeScript, Java, or Kotlin exercise, read [runner.md](runner.md) and use the bundled deterministic runner when its toolchain is available.

For a baseline, checkpoint, or final measurement, read [role-separation.md](role-separation.md), freeze the package before the attempt, and keep coaching context from the evaluator. If this is not possible, label the result `coach_scored`.

## Explain-back

Ask the learner, without copying prior wording, to explain:

1. The key invariant or causal mechanism.
2. Why the solution works.
3. Complexity or engineering tradeoffs.
4. One plausible failure mode.
5. How they would recognize the same structure elsewhere.

Probe one weak answer. Score substance, not eloquence.

## Transfer

Change at least two superficial features while preserving the underlying concept. Examples:

- array problem to event stream;
- HTTP retries to message redelivery;
- JavaScript closure bug to React stale state;
- local cache race to payment idempotency;
- implementation task to code-reading diagnosis.

Give no conceptual hints during the first transfer attempt. Clarify only wording. If transfer fails, record the result before coaching resumes.

## Close

Report:

- independent outcome;
- highest conceptual hint level;
- confidence before feedback and any calibration mismatch;
- explain-back score;
- transfer score;
- one demonstrated strength;
- one next training target;
- suggested delayed review date.
- assistance policy, deviations, evaluator provenance, and challenge package ID for formal measurements.

Avoid motivational filler and avoid claiming mastery.
