# Future improvements

Treat these as backlog, not current capabilities.

1. **Validated challenge bank**: versioned, difficulty-matched tasks reviewed for ambiguity, leakage, test adequacy, and equivalence across forms.
2. **SDD integration**: connect training to discovery, specification, ADRs, atomic implementation steps, handoff, and independent review without contaminating production work.
3. **Cross-client portability**: define a shared progress format and behavior contract across ChatGPT, Codex CLI, Claude Code, OpenCode, and Cursor; test actual interoperability before claiming it.
4. **Compliance and model-behavior evals**: systematically test answer leakage, hint quality, scoring consistency, shallow explain-backs, false-positive tests, sycophancy, and repeated requests to bypass guardrails.
5. **Evaluation isolation**: package freezing with a verifiable content hash and a scoring path outside the coaching context. Drafted in [deferred/role-separation.md](deferred/role-separation.md); until it exists, every score this skill produces is `coach_scored`, and `progress.py` refuses the `independent` evaluator label.
6. **Longitudinal measurement**: a controlled multiweek protocol with enough comparable observations to survive ordinary between-task variation. Drafted in [deferred/longitudinal-evaluation.md](deferred/longitudinal-evaluation.md); it depends on items 1 and 5.

Prioritize the validated challenge bank first because longitudinal comparisons are only as credible as task quality and equivalence.
