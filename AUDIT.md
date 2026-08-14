# Auditoria — train-coding-reasoning

**Data:** 2026-08-14
**Escopo:** os 16 arquivos do pacote no commit `d945e30`
**Método:** leitura integral dos 12 documentos, execução dos dois scripts com casos de teste construídos, e verificação das três citações de `references/evidence.md` contra as fontes primárias.

---

## Veredicto

O pacote é bem escrito e intelectualmente honesto no texto — e desproporcional na engenharia. A parte que funciona de fato (`runner.py`) é ~20% do código; a parte que carrega as promessas fortes (medição longitudinal, avaliação independente, calibração) é prosa não aplicada por nada, mais um CLI que aceita dados incoerentes sem reclamar.

---

## O que foi verificado como verdadeiro

### Citações

As três referências de `references/evidence.md` existem e estão descritas com precisão.

| Citação | Verificação |
|---|---|
| Anthropic, 52 devs, biblioteca Trio | Confere. Quiz 50% (com IA) vs 67% (sem), *d* = 0.738; ~2 min mais rápido, não significativo; maior lacuna em debugging. |
| Bastani et al., PNAS 2025, doi 10.1073/pnas.2422633122 | Confere. "Generative AI without guardrails can harm learning"; ~1.000 alunos de matemática; GPT Base piorou o desempenho sem acesso, GPT Tutor mitigou. |
| Maier et al., arXiv 2605.04779 | Confere. Meta-análise, 23 estudos / 27 tamanhos de efeito; aprendizado *g* = 0.14, não significativo. |

Fontes: [Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills) · [PNAS](https://www.pnas.org/doi/10.1073/pnas.2422633122) · [arXiv](https://arxiv.org/abs/2605.04779)

### `runner.py`

Testado e funcional:

- Python end-to-end: passou.
- Java com o exemplo literal de `runner.md`: passou.
- Loop infinito com `--timeout 2`: morto por `RLIMIT_CPU` em 2,07s (`returncode=-24`, SIGXCPU).
- `time.sleep(30)` com `--timeout 2`: capturado pelo timeout do subprocess em 3,08s.

Os dois caminhos de parada (CPU-bound e bloqueado) funcionam. `runner.md:7` é honesto ao declarar que não é sandbox de segurança.

---

## Achados

### 1. O rigor todo é voluntário — nada o aplica

`role-separation.md:18` exige "package ID ou content hash para que alterações post-hoc sejam detectáveis". Nenhum script calcula hash; `progress.py` aceita `--package-id` como texto livre. Procedência não verificável é procedência decorativa.

O próprio arquivo admite (`role-separation.md:31`) que a opção realista — pontuar dentro do contexto do coach — **não** é independente. Um aprendiz solo cairá na opção 3 em 100% das sessões, e o aparato de quatro papéis colapsa em um rótulo `coach_scored`.

`future-improvements.md:8` reconhece que não existem evals para vazamento de resposta, qualidade de pista, sycophancy ou consistência de pontuação. A promessa central da skill — impedir que a IA faça o trabalho cognitivo — não é testada por nada dentro do pacote.

**Severidade:** alta. É uma limitação de arquitetura, não um bug.
**Status:** endereçado por rebaixamento. `role-separation.md` foi movido para `references/deferred/` com cabeçalho declarando que não é capacidade atual; a skill deixou de mandar segui-lo e passou a instruir que todo score produzido nela é `coach_scored`. A `description` do frontmatter não anuncia mais "independent evaluation".

### 2. `progress.py` grava dados que se contradizem

Sessão aceita sem qualquer aviso:

```
--phase retention_7d --assistance standard_unaided   # fase "sem ajuda"
--initial-result incorrect --outcome independent     # errou, mas "independente"
--hints 6 --confidence 5 --transfer 4                # com pista nível 6 (walkthrough)
→ Recorded session 1; concept=t1 recall=again
```

Quatro violações simultâneas das próprias regras do pacote. `rubric.md:7` define `independent` como "correto antes de pistas acima do nível 1"; `assistance-policy.md:8` proíbe pistas conceituais sob `standard_unaided`. `cmd_record` validava faixas numéricas e duas regras sobre avaliador, mas nunca `hints` × `outcome`, `initial_result` × `outcome` ou `assistance` × `hints`.

**Severidade:** alta. Para uma ferramenta cuja razão de existir é auditabilidade, é o defeito central.
**Status:** corrigido — ver [Correções aplicadas](#correções-aplicadas).

### 3. `status` agrega justamente o que a documentação proíbe

Saída original com as duas sessões de teste:

```
Independent outcomes: 1/2          ← a "independente" teve pista nível 6
Average highest hint: 6.00/6       ← mistura fase coached com fase unaided
Average immediate transfer: 4.00/4 ← inclui uma sessão walked_through
```

`longitudinal-evaluation.md:57` manda comparar distribuições e medianas e separar conclusão assistida de resultado sem ajuda. `rubric.md:57` proíbe agregar em percentual de maestria. O código imprimia apenas médias, sobre notas ordinais 0–4, misturando políticas de assistência.

**Severidade:** alta. A ferramenta contradizia o manual.
**Status:** corrigido.

### 4. O modelo de dados conflita transferência e fase

O exemplo canônico (`SKILL.md:147-153`) grava `--phase practice --assistance coached ... --transfer 2`. Mas `VALID_PHASES` contém `immediate_transfer`, que é obrigado a usar política sem ajuda. A mesma medida — transferência sem ajuda — pode viver em dois lugares incompatíveis: campo de uma sessão `coached`, ou sessão própria `immediate_transfer`.

Uma sessão real produz as duas coisas, e o schema só aceita um valor de `assistance`. Ou se subnotifica, ou se duplica a mesma tentativa como duas observações — e `capability-model.md:20` proíbe explicitamente contar uma tentativa como duas medições.

**Severidade:** média-alta. Exigiu decisão de modelagem, não correção pontual.
**Status:** corrigido. A transferência é atributo da sessão, não fase: `immediate_transfer` deixou de ser fase gravável (continua legível em estados legados), `--transfer` virou opcional e ganhou `--transfer-policy`, e o `status` reporta a transferência fora dos blocos de assistência — porque ela é sem ajuda mesmo dentro de uma sessão `coached`.

### 5. `independent` não significa "sem ajuda"

`rubric.md:7` tolera pista nível 1 (pergunta diagnóstica) dentro do rótulo `independent`. `session-protocol.md:100` exige zero pista conceitual na transferência. São duas réguas diferentes somadas no mesmo indicador.

**Severidade:** média. Ambiguidade de definição na documentação.
**Status:** corrigido. `independent` passou a exigir zero pista conceitual — a mesma régua da transferência — e a pergunta diagnóstica de nível 1 passou para `lightly_assisted`. As duas medidas voltaram a ser comparáveis. Sessões antigas não são reavaliadas: a validação roda no momento da gravação.

### 6. Crash em estado v2

```
python3 progress.py due --state v2.json
KeyError: 'difficulty'   (scripts/progress.py:355)
```

`migrate_v1` construía cards completos; `migrate_v2` repassava `data.get("cards", [])` sem normalizar. Ironia: `record` e `review` sobreviviam porque usam `.get()` com default — os comandos **somente-leitura** eram os frágeis.

**Severidade:** média.
**Status:** corrigido.

### 7. A régua é maior que o instrumento

O programa propõe 2–3 sessões/semana por 6–8 semanas sobre 5 capacidades: ~3–5 observações por capacidade, em escala ordinal 0–4, pontuadas pelo próprio coach. A regra de sucesso de exemplo (`longitudinal-evaluation.md:13`) — "melhorar a média de transferência em 0,75/4" — é apresentada como critério de decisão, mas com esse n a variação normal entre tarefas domina o efeito. Efeito de prática, regressão à média e deriva de dificuldade não têm mecanismo de controle.

O mecanismo que resolveria isso — banco de desafios validado e equiparado — está em `future-improvements.md:5` como backlog, com a admissão de que "comparações longitudinais só são tão críveis quanto a qualidade e equivalência das tarefas". O pacote sabe que sua fundação não existe.

**Severidade:** alta para as conclusões, baixa para o uso diário como treino.
**Status:** endereçado por rebaixamento. `longitudinal-evaluation.md` foi para `references/deferred/` e o subcomando `configure-program` foi removido. Os checks de retenção de 7 e 21 dias continuam — são prática legítima; o que saiu foi a moldura que os apresentava como medição controlada.

### 8. Zero testes

16 arquivos, 828 linhas de Python, nenhum teste, nenhum CI, nenhum README, nenhuma licença. Os achados 2, 3 e 6 seriam pegos por meia dúzia de asserts.

**Severidade:** média-alta.
**Status:** corrigido — suíte adicionada.

---

## Ressalva sobre as citações

`evidence.md:9` cita Maier et al. apenas pelo achado de aprendizado (*g* = 0.14, n.s.) e omite que o mesmo estudo encontrou efeito significativo em produtividade (*g* = 0.33). Não é falso, mas é seleção conveniente: a meta-análise diz "produz mais, não aprende mais", e o arquivo cita só a segunda metade.

A extrapolação de alunos de matemática do ensino médio para engenheiros seniores, por outro lado, está declarada honestamente em `evidence.md:8`.

---

## Correções aplicadas

Ver `tests/` e o diff de `scripts/progress.py`.

1. **Validação cruzada em `record`** — `hints` × `outcome` (faixas de `rubric.md`), `initial_result` × `outcome`, e política sem ajuda passa a exigir `--hints 0`. A regra de fase sem ajuda foi movida para a mesma função, eliminando a duplicação.
2. **`normalize_card` em `load_state`** — todo card recebe os campos do scheduler antes de ser usado, em qualquer versão de schema; `id` e `due` ausentes viram erro explícito em vez de `KeyError`.
3. **`status` reescrito** — separa sessões sem ajuda de assistidas, reporta mediana com n e amplitude em vez de média global, e marca capacidades com menos de duas tarefas como evidência insuficiente (`capability-model.md:17`).
4. **Suíte de testes** — `tests/test_progress.py` e `tests/test_runner.py`, stdlib apenas, executadas com `python3 -m unittest discover -s tests`.
5. **Transferência deixou de ser fase** (achado 4) — schema 4. `RECORDABLE_PHASES` exclui `immediate_transfer`; `--transfer` é opcional e não deve receber zero quando não houve tarefa; `--transfer-policy` registra sob qual política sem ajuda a transferência ocorreu; `migrate_v3` rotula scores antigos como `standard_unaided` e preserva sessões gravadas na fase aposentada.

6. **Aparato longitudinal rebaixado** (achados 1 e 7) — `longitudinal-evaluation.md` e `role-separation.md` movidos para `references/deferred/`, cada um com cabeçalho dizendo por que está adiado e o que precisaria existir antes; `configure-program` removido; `future-improvements.md` ganhou os dois itens com a dependência entre eles; `SKILL.md` trocou as duas seções por uma que declara o que uma sessão consegue e o que não consegue estabelecer. Nenhum conteúdo foi apagado.

7. **Definição de `independent` alinhada** (achado 5) — `rubric.md` e `HINT_RANGE_BY_OUTCOME` passaram a exigir nível 0; a faixa de `lightly_assisted` absorveu o nível 1.
8. **Higiene de repositório** — `README.md` com o escopo honesto do que a skill não estabelece, `.gitignore`, e workflow de CI rodando a suíte em Python 3.9 e 3.14.

Nenhum achado permanece em aberto. `LICENSE` (MIT) foi definida pelo autor após a auditoria.
