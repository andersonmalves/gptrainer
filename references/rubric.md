# Learning rubric

Score evidence of unaided reasoning, not polish produced with assistance.

## Outcome labels

- **Independent**: correct with no conceptual hint at all.
- **Lightly assisted**: correct after hint level 1, 2, or 3.
- **Heavily assisted**: correct after hint level 4 or 5.
- **Walked through**: answer or decisive reasoning supplied at level 6.
- **Incomplete**: no correct result within the timebox.

Keep the highest hint level even if the final code is excellent.

A level-1 diagnostic question is a conceptual hint, so it costs the independent label. Only level 0 — task clarification and incidental syntax or toolchain help — preserves it. That is the same bar the transfer attempt uses in [session-protocol.md](session-protocol.md), so the two measures stay comparable.

## Explain-back score

| Score | Evidence |
|---:|---|
| 0 | Cannot explain the mechanism |
| 1 | Repeats steps without causal reasoning |
| 2 | Explains the core idea but misses an important edge or tradeoff |
| 3 | Explains invariant, correctness, and main tradeoff accurately |
| 4 | Also predicts failure modes and generalizes the pattern |

## Transfer score

| Score | Evidence |
|---:|---|
| 0 | No viable start without help |
| 1 | Recognizes pieces but applies the wrong model |
| 2 | Correct model with gaps or a significant bug |
| 3 | Correct unaided solution and explanation |
| 4 | Correct solution plus explicit comparison to the original pattern and tradeoffs |

## Session result

Use this compact template:

```text
Resultado independente: independent | lightly_assisted | heavily_assisted | walked_through | incomplete
Maior pista conceitual: 0–6
Confiança antes do feedback: 1–5
Calibração: calibrated | confident_wrong | uncertain_correct
Explicação de volta: 0–4
Transferência sem ajuda: 0–4 | não aplicada
Política da transferência: strict_unaided | standard_unaided
Tempo: N min
Capacidade: capability_id
Fase: baseline | practice | retention_7d | retention_21d | final
Política de ajuda: strict_unaided | standard_unaided | coached | conventional_ai
Avaliador: independent | coach_scored
Pacote do desafio: package_id
Evidência observada: ...
Próximo alvo: ...
Revisão sugerida: YYYY-MM-DD
```

The transfer attempt belongs to the session that produced it and is always unaided, even when the session itself was coached. Record it as a session field with its own policy; it is not a separate phase. Leave it unrecorded when no transfer task was given rather than entering a zero.

Do not aggregate a single session into a percentage of “mastery.” For trends, compare repeated unaided transfer and delayed-retention attempts on the same skill family.

Do not label an evaluator as independent unless it lacked the coaching transcript and used the frozen evaluator brief. Deterministic tests establish behavior for covered cases; they do not independently establish reasoning quality or complete correctness.
