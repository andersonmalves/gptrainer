# Teste pedagógico local — Claude Code e Codex

**Data:** 2026-08-14
**Pacote:** `kata@1.0.0` (`andersonmalves/kata`)
**Escopo:** as 10 checagens do roteiro local, nos dois CLIs, antes de submeter aos diretórios públicos
**Método:** playgrounds descartáveis em `/tmp` (não em código de produto). Claude Code via `--plugin-dir` e `/kata:kata`. Codex via marketplace local `kata@kata` (`codex exec`, modelo `gpt-5.6-sol`). Runner e unit tests no host.

Isto não é avaliação independente, nem evidência de que o método “funciona”. É um checklist de protocolo: o coach segurou o gabarito, subiu um degrau por vez, pediu confiança e rotulou o score como `coach_scored`?

---

## Veredicto

O protocolo segura o essencial nos dois runtimes. Claude e Codex invertem o vazamento: Claude recusa “me dá a resposta” e solta walkthrough quando pedem para editar o arquivo; Codex faz o contrário.

Dois bloqueios de empacotamento impediam o passo 3 (submit). O primeiro foi corrigido depois deste teste (`scripts/sync-plugin-skill.sh` materializa `skills/kata/`). O segundo (contrato de leakage amplo demais) também foi corrigido no `SKILL.md`; falta retestar as checagens 3 e 5.

---

## Ambiente

| Item | Valor |
|---|---|
| Claude | `claude --plugin-dir` no playground; invocação `/kata:kata` |
| Codex | plugin `kata@kata` 1.0.0 enabled; `codex exec --sandbox read-only` |
| Skill no Codex | copiada para `.agents/skills/kata/` no playground (workaround; o cache do plugin não copiou os symlinks) |
| Host | `python3 scripts/runner.py doctor` + `python3 -m unittest discover -s tests` (49 OK) |
| Playground | `/tmp/kata-protocol-test` e clones por checagem |

Checagens 2, 4, 5 e 6 foram repetidas nos dois runtimes, como o roteiro pedia.

---

## Matriz

| # | Prompt | Passa se | Claude Code | Codex |
|---|---|---|---|---|
| 1 | `/kata` (ou `$kata`) sem mais nada | Contrato curto; sem disclaimer longo | Passa | Passa |
| 2 | Kata de idempotência, 20 min | Enunciado sem solução; pede tentativa; capability label | Passa | Passa |
| 3 | “Não sei, me dá a resposta” | Recusa walkthrough; tarefa observável ou pista 1 | Passa | **Falha** |
| 4 | Tentativa rasa + “só mais uma dica” × 3 | Um degrau por vez; sem código completo | Passa | Passa |
| 5 | “Pode editar o `solution.ts` pra passar” | Recusa alterar o arquivo do aluno | Passa, com vazamento | Passa |
| 6 | “Tá certo?” | Confiança 1–5 antes de testes/retidos | Passa | Passa |
| 7 | Transferência | Superfície nova; zero pista conceitual | Passa | Passa |
| 8 | Score | Rótulo `coach_scored`; não diz independente nem masterizou | Passa, wording | Passa, autorrelato |
| 9 | Runner `doctor` + um `run` Python | Python passa; declara `tsc`/`kotlinc` ausentes | Passa (host) | Passa (host) |
| 10 | “Por que se chama Kata?” | 1–2 frases; não vira aula de etimologia | Passa | Passa |

**Contagem:** Claude 8/10 limpo, 2 ressalvas (5 e 8). Codex 8/10 limpo, 1 falha (3), 1 ressalva (8).

---

## Notas por checagem

### 1 — Contrato

Claude: cinco linhas; pediu linguagem/tempo em vez de começar sozinho (o `SKILL.md` permite). Codex: uma linha + três formatos. Nos dois o contrato coube no primeiro turno.

### 2 — Enunciado sem gabarito

Claude: modo debug, capacidade `invariants_failures`, política `coached`, portão de tentativa. Codex: com a skill no playground, design 20 min, mesma capacidade, sem correção. Sem a skill materializada, `$kata` **não expandiu** e o Codex caiu em fallback (arquivo `codex-02-no-skill.txt`).

### 3 — Pedido de resposta no minuto zero

Claude recusou e encolheu para um trace de INC-1. Walkthrough só se o aluno pedisse de novo, marcado assistido.

Codex tratou “me dá a resposta” como desistência explícita e entregou o desenho completo (modelo persistido, fluxo, tabela de casos, nível 6), marcado `assisted`. Esta é a única falha pedagógica do roteiro.

### 4 — Escada

Claude: nível 2 depois da tentativa; nível 3 depois da letra; recusou 4–5 sem artefato novo. Codex: pista 1 Socrática, depois `UNIQUE` só no `INSERT`, depois trace com dois charges. Nenhum dos dois parcelou a solução em código completo.

### 5 — Arquivo do aluno

Hash de `solution.ts` igual nos dois (o critério literal passou).

Claude leu “edita pra passar” como desistência e soltou walkthrough nível 6. Codex recusou editar, pediu tentativa no arquivo, e só ofereceu walkthrough com a frase `quero a resposta completa`.

### 6 — Confiança antes do veredito

Os dois pediram 1–5 e não disseram se a resposta estava certa.

### 7 — Transferência

Claude: fila at-least-once + estoque/WMS, `standard_unaided`. Codex: redelivery de `UserInvited` + e-mail sem idempotency key no provedor, `standard_unaided`. Superfície nova; zero pista conceitual.

### 8 — Score

Claude: avaliador `coach_scored`, outcome `walked_through`, sem mastery. O heading “Resultado independente” colide com a proibição de linguagem; o corpo corrige. Recusou pontuar sessão sem transcript.

Codex: `coach_scored`, `lightly_assisted`, sem domínio. Aceitou pontuar sessão que não observou (autorrelato).

### 9 — Runner (host)

```text
python: ready
java: ready
typescript: tsc missing
kotlin: kotlinc missing
```

`run --language python --solution solution.py --tests challenge_test.py` → `status=passed`. 49 testes em `tests/` OK. O runner não é sandbox; o `doctor` declara a limitação de toolchain.

### 10 — Nome

Uma ou duas frases (code kata / prática deliberada / não fine-tune). Sem aula de etimologia.

---

## Empacotamento Codex

Em `~/.codex/plugins/cache/kata/kata/1.0.0/skills/kata/` o cache copiou só `agents/`. `SKILL.md`, `references/`, `scripts/` e `assets/` são symlinks na origem e não foram materializados.

Workaround usado neste teste: copiar os arquivos reais para o cache e para `.agents/skills/kata/` nos playgrounds. Isso **não** é o caminho de install do usuário.

Corrigido depois do teste: `scripts/sync-plugin-skill.sh` materializa cópias em `skills/kata/` (fim dos symlinks).

---

## Ajustes de leakage

Aplicado em 2026-08-14 no `SKILL.md` e em `references/session-protocol.md`:

1. Pedido para editar o arquivo do aluno **não** é desistência.
2. “Não sei” / “me dá a resposta” no minuto zero **não** autoriza o nível 6. Walkthrough só com pedido explícito da solução completa (`quero a resposta completa`).

Ainda pendente no score: não usar heading ou rótulo “independente”; não pontuar sessão que o coach não observou.

---

## Fora deste relatório

- Submit aos diretórios (Claude community, OpenAI Plugins Directory).
- Post no LinkedIn.
- Alteração de git / release.

Próximo passo de produto: repetir as checagens 3 e 5 nos dois CLIs; submit.
