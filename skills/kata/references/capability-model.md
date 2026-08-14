# Capability model

Use one primary capability label per exercise so progress remains interpretable.

| ID | Capability | Observable evidence |
|---|---|---|
| `debugging_diagnosis` | Debugging and causal diagnosis | Reproduce, rank hypotheses, isolate cause, predict the effect of a fix |
| `code_reading` | Code reading and behavioral prediction | Trace state/control flow, state invariants, predict outputs and side effects |
| `decomposition_modeling` | Decomposition and system/data modeling | Define boundaries, interfaces, state, dependencies, and tradeoffs |
| `invariants_failures` | Invariants, concurrency, retries, and failure handling | Identify safety/liveness rules, interleavings, duplicate delivery, partial failure |
| `ai_code_review` | Critical review of AI-generated code | Detect plausible but wrong assumptions, missing cases, security/reliability defects |
| `algorithms_data` | Algorithms and data structures | Select representations, reason about correctness and complexity, handle adversarial cases |

## Selection rules

- For experienced engineers, sample the first five capabilities before making algorithms the center of the program.
- Use a minimum of two distinct tasks before interpreting a capability-level weakness.
- Keep surface familiarity from masking reasoning: use unfamiliar but documented APIs only when API recall is not the target.
- Do not raise difficulty by code volume alone. Add ambiguity, interacting constraints, incomplete evidence, concurrency, or operational consequences.
- Record secondary capabilities in notes only; do not double-count one attempt as multiple independent measurements.

## Baseline coverage

Use three to five short tasks. Cover at least:

1. `debugging_diagnosis` or `code_reading`;
2. `decomposition_modeling` or `invariants_failures`;
3. `ai_code_review`;
4. `algorithms_data` only when relevant to the learner's goals or suspected gap.

Choose later practice from errors demonstrated in the baseline. Do not train every family equally by default.
