# Role separation

Use four roles and keep their visibility distinct.

| Role | May see | Must not do |
|---|---|---|
| Generator | Capability target, difficulty specification, prior aggregate gaps | Coach or score the resulting attempt |
| Challenge validator | Full challenge package and rubric before release | Teach the learner or change criteria after seeing performance |
| Coach | Learner prompt, public examples/tests, learner attempts, hint ladder | See evaluator key or assign an “independent” score |
| Evaluator | Frozen learner submission, frozen rubric, withheld tests, allowed-resource log | See coaching transcript, provide hints, or repair the submission |

## Freeze a challenge package

Before the attempt, create:

1. learner prompt with capability ID, constraints, timebox, deliverable, public examples, and assistance policy;
2. evaluator brief with expected invariants, failure classes, scoring anchors, withheld tests, and acceptable alternatives;
3. package ID or content hash so post-hoc changes are detectable;
4. validator decision: `accepted`, `revise`, or `reject`, with reasons.

The validator must reject material ambiguity, inconsistent examples/tests, answer leakage, reliance on trivia outside the target, impossible constraints, or a difficulty mismatch.

## Evaluation isolation

Prefer, in order:

1. deterministic tests plus a separate human or agent evaluator with only the frozen submission and evaluator brief;
2. deterministic tests plus a separate conversation that never received the coaching transcript;
3. deterministic tests plus rubric scoring in the coaching context, labelled `coach_scored`.

Do not describe option 3 as independent. Context instructions cannot guarantee that one model forgets information already seen.

## Result provenance

Record:

- challenge package ID;
- assistance policy and deviations;
- evaluator type: `independent` or `coach`;
- deterministic test result;
- rubric scores and concise evidence;
- whether the evaluator saw coaching context.

Independence is a property of the evaluation process, not the evaluator label alone.
