# Evidence and limits

Use these findings to justify the guardrails, not to overstate certainty.

## What the evidence supports

- A randomized controlled study of 52 **mostly junior** software engineers learning an unfamiliar Python library (Trio) found lower conceptual, code-reading, and debugging quiz performance for the AI-assisted group (50% vs 67%, Cohen's *d* = 0.738), without a statistically significant completion-time benefit. The quiz was **immediate**, not a delayed retention test. Interaction patterns centered on conceptual inquiry or generation followed by comprehension performed better than delegation-heavy patterns. This is not a study of senior engineers doing production work. Source: [Anthropic, 2026](https://www.anthropic.com/research/AI-assistance-coding-skills).
- A field experiment with nearly 1,000 high-school **mathematics** students found that unrestricted GPT improved assisted practice but reduced subsequent unassisted exam performance; a tutor with learning safeguards largely mitigated that harm. This is evidence for guarded tutoring, but it is not a programming study or a study of senior engineers. Source: [Bastani et al., PNAS, 2025](https://www.pnas.org/doi/10.1073/pnas.2422633122).
- A 2026 preprint meta-analysis of 23 studies reported a moderate positive effect of generative AI on **productivity** (Hedges' *g* = 0.33, 95% CI [0.09, 0.58]) with very high heterogeneity, and a small, statistically non-significant pooled effect on **programming learning** (*g* = 0.14, 95% CI [−0.18, 0.47]). The learning sample is **students** (university and K-12), not professional or senior engineers. When exams were taken without AI, the learning effect was indistinguishable from zero and slightly negative (*g* = −0.06); large gains appeared only when AI was allowed during the test (*g* = 0.76). Treat this as preliminary because it is a preprint. Source: [Maier et al., arXiv, 2026](https://arxiv.org/abs/2605.04779).

These results support separating assisted performance from unaided learning and constraining answer delivery. They do not prove that this exact skill prevents long-term skill decay, and they do not validate the protocol for senior engineers.

## How to speak about results

- Say “evidence suggests,” “this session demonstrated,” or “we do not yet know.”
- Do not claim that desirable difficulty, hints, transfer, or spaced review guarantee retention.
- Treat immediate transfer as stronger evidence than assisted completion, and delayed unaided review as stronger evidence than immediate transfer.
- Distinguish research populations and tasks from the learner's context.
