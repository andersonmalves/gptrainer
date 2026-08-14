# Challenge design

Choose tasks that expose a mental model and admit objective feedback.

## Matrix

| Skill family | Useful task forms | Increase difficulty by |
|---|---|---|
| Decomposition | plan, interfaces, dependency graph | ambiguity, interacting constraints |
| Tracing | predict output/state, event order | aliasing, async interleavings, hidden state |
| Debugging | reproduce, rank hypotheses, isolate cause | weak symptoms, multiple plausible causes |
| Invariants | state machine, consistency rule, proof sketch | concurrency, retries, partial failure |
| Testing | derive cases, properties, mutation targets | malformed input, nondeterminism, boundaries |
| Refactoring | preserve behavior while changing structure | broad call graph, compatibility constraints |
| Algorithms | select representation and strategy | scale, adversarial cases, memory limits |
| System design | compare options and failure modes | load, recovery, tenancy, compliance |
| Code reading | summarize flow and predict impact | unfamiliar style, indirection, side effects |

## Difficulty bands

- **Foundational**: one core concept, explicit inputs, short feedback loop.
- **Intermediate**: two interacting concepts, edge cases, some ambiguity.
- **Senior**: incomplete signals, competing tradeoffs, failure analysis, operational consequences.

Senior difficulty must not mean merely larger code. Prefer judgment under constraints.

## Good challenge properties

- Solvable within the declared timebox.
- Has a specific target skill and observable success criteria.
- Requires a choice or prediction before implementation.
- Contains at least one revealing edge case.
- Supports a transfer variant that is not a renaming exercise.
- Avoids obscure trivia unless trivia is explicitly requested.

## Domain examples

- Diagnose duplicate charges despite an idempotency key.
- Predict stale React state across queued updates.
- Find a cancellation leak in an asynchronous Node.js workflow.
- Design a Kotlin state transition that survives redelivery.
- Derive property tests for money rounding and allocation.
- Compare optimistic locking, a unique constraint, and a distributed lock.
- Trace an AWS retry path through SQS, Lambda, and a downstream API.

Do not reuse proprietary code in generated challenges. If grounding in a repository, abstract sensitive names and values when summarizing progress.
