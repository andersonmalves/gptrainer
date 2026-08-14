# Assistance policy

Define allowed resources before each timed attempt. Record one policy exactly; do not infer it afterward.

| Policy | Allowed | Disallowed | Use |
|---|---|---|---|
| `strict_unaided` | Editor, paper/notes, local compiler or deterministic tests supplied with the task | Documentation, web search, external AI, prior solutions, conceptual hints | Baseline or controlled checkpoint when recall itself matters |
| `standard_unaided` | Official language/API documentation, compiler, debugger, public tests, syntax lookup; record material lookups | External AI, same-problem solutions, conceptual hints, hidden tests, answer autocomplete | Default realistic engineering assessment |
| `coached` | Progressive hint ladder and incidental syntax/tool help | Unlabelled solution delivery | Training sessions |
| `conventional_ai` | Normal AI assistance | None beyond security and task constraints | Explicit comparison condition; never score as unaided |

## Operational rules

- Start the timer after the task and policy are understood.
- Pause only for infrastructure failure or genuine task ambiguity; record the pause.
- Count conceptual help from any person or system as assistance.
- Do not count clarification of ambiguous requirements, compiler diagnostics, or help with incidental syntax as conceptual hints under `standard_unaided`; record material use when it may affect interpretation.
- If the learner crosses the policy boundary, continue the exercise but relabel the result. Never discard the boundary crossing to preserve a good score.
- Do not expose withheld tests before confidence is recorded and the answer is committed.
- Do not compare attempts that used materially different policies without showing the difference.

Use this compact declaration:

```text
Política: standard_unaided
Permitido: documentação oficial, compilador/debugger e testes públicos
Não permitido: IA externa, solução do mesmo problema e pistas conceituais
Tempo: 25 min; pausas apenas por ambiguidade ou falha de ambiente
```
