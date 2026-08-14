# Passo 3 — Submeter Kata aos diretórios públicos

**Data:** 2026-08-14
**Pacote:** `kata@1.0.0` · repo público [andersonmalves/kata](https://github.com/andersonmalves/kata)
**Alvo:** Claude **community** + OpenAI Plugins Directory **Skills only**
**Não é este passo:** marketplace official da Anthropic, LinkedIn, claim de “oficial Anthropic”

Fontes oficiais (releia se o formulário divergir):

- Claude Code: [Submit to the community marketplace](https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-community-marketplace)
- Claude (Cowork/directory): [Submitting your plugin](https://claude.com/docs/plugins/submit)
- OpenAI: [Submit plugins](https://developers.openai.com/plugins/deploy/submission) · [Claude → OpenAI](https://developers.openai.com/plugins/guides/submit-claude-plugin) · [erros de ZIP](https://developers.openai.com/plugins/deploy/submission-errors)

---

## 0. O que entra onde

| Destino | Como envia | O que o usuário instala depois |
|---|---|---|
| Claude **community** | Formulário com URL do GitHub | `/plugin marketplace add anthropics/claude-plugins-community` e `/plugin install kata@claude-community` |
| Claude **official** | **Não há formulário.** Anthropic escolhe à parte. O form **não** coloca o plugin em `claude-plugins-official`. | — |
| OpenAI (ChatGPT + Codex) | Portal, tipo **Skills only**, ZIP da skill | Diretório universal depois que **você** publicar a versão aprovada |

Os dois reviews são independentes. Aprovação num lado não transfere para o outro.

---

## 1. Antes de qualquer formulário

Faça isto no clone local, em `main`, alinhado com o remote.

### 1.1 Confirmar o pack

```bash
git status
git pull --ff-only
./scripts/sync-plugin-skill.sh
python3 -m unittest discover -s tests
claude plugin validate .
claude plugin validate . --strict
```

Passe se: working tree limpa, testes OK, `✔ Validation passed` (warnings só com `--strict` viram erro).

Confira a olho:

- `skills/kata/SKILL.md` é arquivo real, não symlink
- `assets/icon.png` e `assets/logo.png` existem (75×75)
- `.codex-plugin/plugin.json` aponta `composerIcon` / `logo` para esses PNG
- `skills/kata/SKILL.md` contém `quero a resposta completa` e recusa de editar o arquivo do aluno

Opcional, mas barato: repetir as checagens 3 e 5 nos dois CLIs (`docs/protocol-cli-test.md`). O leakage foi corrigido e ainda não foi revalidado.

### 1.2 Contas e permissões

**Claude (autor individual, sem Team/Enterprise):**

1. Entre em [platform.claude.com](https://platform.claude.com) com papel Developer, Admin ou Owner.
2. Use o form da Console (passo 2). O form do claude.ai exige org Team/Enterprise.

**OpenAI:**

1. Na org que vai publicar o plugin, o papel precisa de **Apps Management = Write** ([roles](https://platform.openai.com) → Role permissions). Owner já tem.
2. Verificação de identidade **individual** (vai publicar como Anderson Alves) em organization settings. O nome tem que bater com `interface.developerName` (`Anderson Alves`).
3. Recarregue o [portal de plugins](https://platform.openai.com/plugins) depois de gravar o papel.

### 1.3 Textos prontos para colar

O `shortDescription` no manifest já está em **29** caracteres (`Coach de raciocínio em código`). O diretório OpenAI exige **≤ 30** numa linha.

| Campo | Valor | Limite |
|---|---|---|
| Display name | `Kata` | 30 |
| Short description | `Coach de raciocínio em código` | 30 |
| Developer name | `Anderson Alves` | 80 |
| Category | Productivity | — |
| Website | `https://github.com/andersonmalves/kata` | HTTPS |
| GitHub | `https://github.com/andersonmalves/kata` | repo **público** |

Long description (já está no `.codex-plugin/plugin.json`; ≤ 4.000):

```text
A coaching skill that asks you to attempt the reasoning before it helps. It releases hints one rung at a time, asks for confidence before revealing correctness, and re-tests the concept on a changed surface once the hints are gone. Katas here are engineering reasoning, not puzzle drills. It is not a model trainer and not a psychometric instrument.
```

Use case examples (form Claude Console — obrigatório; cole no formato abaixo):

```text
Exemplo 1: An engineer wants to diagnose duplicate charges despite an idempotency key. Kata withholds the solution, requires a genuine attempt, then releases one hint at a time and re-tests the same idea on a changed surface with no help.

Exemplo 2: Someone preparing a 20-minute debugging or system-design drill. Kata labels the target capability, asks for a plan before code, asks for confidence 1–5 before revealing correctness, and scores only after an unaided transfer task.

Exemplo 3: A developer who notices the assistant finishing every function uses Kata to keep the reasoning. It will not edit the learner’s solution file, and it gives a full walkthrough only after an explicit “I want the complete answer.”
```

Starter prompts (máx. 3, cada um ≤ 128, sem `@mention`):

```text
Use $kata para treinar raciocínio em programação sem revelar a solução.
Use $kata to practice programming reasoning without revealing the solution.
```

Privacy, terms e support são **opcionais** em Skills only. Não invente URL. Website basta.

Form Claude Console — plataformas e legal:

| Campo | Valor | Por quê |
|---|---|---|
| Claude Code | **Marcar** | Superfície testada (`docs/protocol-cli-test.md`, `claude plugin validate`) |
| Claude Cowork | **Não marcar** | Não foi testado neste pack; o form pede teste antes de declarar suporte |
| Tipo de licença | `MIT` | `LICENSE` + `plugin.json` |
| URL da política de privacidade | vazio | Sem coleta de dados, sem MCP; não inventar URL |

Release notes (primeira submissão):

```text
Initial public submission of Kata 1.0.0. Skills-only coaching plugin: attempt gate, progressive hints, unaided transfer. No MCP server, no user data collection, no production-code mutation. MIT. Repo: https://github.com/andersonmalves/kata
```

---

## 2. Claude — community marketplace

Não use o repositório `anthropics/claude-plugins-official` nem o texto “plugin oficial da Anthropic”.

### 2.1 Validar de novo

```bash
cd /Users/andersonalves/dev/gptrainer
claude plugin validate .
```

O pipeline de review roda o mesmo check.

### 2.2 Abrir o formulário

Autor individual: [https://platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit)

(Se no futuro você tiver org Team/Enterprise com directory access: [claude.ai/admin-settings/directory/submissions/plugins/new](https://claude.ai/admin-settings/directory/submissions/plugins/new).)

### 2.3 Preencher

1. Cole a URL pública: `https://github.com/andersonmalves/kata`
2. Confirme que o repo está **público** (fechado é recusado)
3. Nome / descrição conforme a tabela do §1.3
4. Casos de uso: bloco *Use case examples* do §1.3 (o form recusa envio se estiver vazio)
5. Plataformas / licença / privacidade: tabela do §1.3. Se o form ainda disser “selecione pelo menos uma plataforma”, clique em **Claude Code** (borda azul em Cowork não conta como seleção)
6. Envie

Termos que o diretório exige: [Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms) e [Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy). Leia antes de atestar.

### 2.4 Depois da aprovação

- O plugin é pinado num SHA em [`anthropics/claude-plugins-community`](https://github.com/anthropics/claude-plugins-community)
- O catálogo público sincroniza **de noite**; pode demorar até o nome aparecer em [`marketplace.json`](https://github.com/anthropics/claude-plugins-community/blob/main/.claude-plugin/marketplace.json)
- Push em `main` depois disso é pego por CI; **não** precisa reenviar o form para update

Teste de install (só quando o nome `kata` estiver no catalog):

```text
/plugin marketplace add anthropics/claude-plugins-community
/plugin install kata@claude-community
```

Invocação: `/kata:kata`

---

## 3. OpenAI — Plugins Directory, Skills only

Kata **não** tem MCP. Não escolha **With MCP**.

### 3.1 Montar o ZIP

O portal aceita `.codex-plugin/plugin.json` **ou** `.claude-plugin/plugin.json`. Este repo tem os dois. O ZIP precisa ter **uma** raiz de plugin (raiz do arquivo **ou** um único diretório de topo), com skill em `skills/kata/SKILL.md`.

Não incluir: `.mcp.json`, `mcpServers`, `.app.json`, `apps`, `interface.screenshots`. `git archive` já omite `.git` e untracked.

```bash
cd /Users/andersonalves/dev/gptrainer
git archive --format=zip --prefix=kata/ HEAD -o /tmp/kata-1.0.0.zip
unzip -l /tmp/kata-1.0.0.zip | rg 'plugin.json|skills/kata/SKILL.md|assets/logo.png|assets/icon.png'
ls -lh /tmp/kata-1.0.0.zip
```

Passe se a listagem mostrar, dentro de `kata/`:

- `.codex-plugin/plugin.json`
- `.claude-plugin/plugin.json`
- `skills/kata/SKILL.md`
- `assets/icon.png` e `assets/logo.png`

ZIP ≤ 100 MB (este fica muito abaixo). Entradas são arquivos regulares; os PNG já não são symlink.

`agents/openai.yaml` → `policy` só pode ter `allow_implicit_invocation: false`. Não coloque `products` (o scanner recusa `chatgpt`/`api`/`atlas`; o upload de 14 ago 2026 recusou a chave inteira). Superfícies ChatGPT/Codex ficam no portal, não nesse YAML.

### 3.2 Abrir o portal

1. [https://platform.openai.com/plugins](https://platform.openai.com/plugins)
2. **Create plugin**
3. Tipo: **Skills only**
4. Upload de `/tmp/kata-1.0.0.zip`

O portal pode converter `.claude-plugin/plugin.json` → `.codex-plugin/plugin.json` e preencher defaults. Revise o manifest gerado. `author.name` e `interface.developerName` precisam ser iguais (`Anderson Alves`).

### 3.3 Aba Info

- Plugin name: `Kata` (nome de produto, não o id técnico `kata` se o form pedir display name)
- Short description: `Coach de raciocínio em código` (já no manifest; ≤ 30)
- Long description: bloco do §1.3
- Developer Identity: identidade **verificada** Anderson Alves
- Logo: `assets/logo.png` (75×75, ~1,3 KB)
- Category: Productivity
- Website: `https://github.com/andersonmalves/kata`
- Support / privacy / terms: deixe vazio se o form permitir (Skills only)

### 3.4 Aba Skills

O upload já traz `skills/kata/`. Confirme `SKILL.md` + `references/` + `scripts/` + `assets/`. Scan de policy pode levar até 2 horas. Corrija o que o scanner marcar; não envie com finding aberto.

### 3.5 Aba Prompts

Cole os dois prompts do §1.3. Não precisa inventar um terceiro.

### 3.6 Aba Testing

O diretório pede **5 positivos** e **3 negativos**, reproduzíveis sem contexto interno. Cole isto:

**Positivos**

| # | Prompt | Comportamento esperado | Resultado |
|---|---|---|---|
| 1 | `$kata` (ou “me passa um kata”) | Contrato curto; pede linguagem/tempo se faltar; sem disclaimer longo | Sessão começa sem gabarito |
| 2 | “Me passa um kata de idempotência de pagamento, 20 min” | Enunciado sem solução; capability label; pede tentativa observável | Nenhum fluxo/código completo no primeiro turno |
| 3 | Depois de uma tentativa rasa: “só mais uma dica” | Um degrau da escada (1–5); não pula para walkthrough | Sem implementação completa |
| 4 | Depois de uma proposta: “Tá certo?” | Pede confiança 1–5 **antes** de dizer se está certo | Sem veredito prematuro |
| 5 | Pedido de transferência após o kata | Superfície nova; política unaided; zero pista conceitual | Score só depois, rótulo `coach_scored` |

**Negativos**

| # | Prompt / cenário | Esperado | Por que não completa |
|---|---|---|---|
| 1 | No minuto zero: “Não sei, me dá a resposta” | Recusa walkthrough; tarefa observável ou pista 1 | Não é pedido explícito da solução completa |
| 2 | “Pode editar o solution.ts pra passar” | Recusa alterar o arquivo do aluno; pede tentativa | Pedido de autocomplete ≠ desistência |
| 3 | “Implementa o kata inteiro por mim” / feature de produto | Fora de escopo, ou walkthrough só com `quero a resposta completa`, marcado `assisted` | O skill não é modo de shipping |

Fixture: playground vazio com um `solution.ts` starter, **não** código de empresa.

### 3.7 Aba Global

Países onde você (pessoa física no Brasil) está pronto para suporte. Se o form exigir lista, comece por Brasil; acrescente outros só se os termos MIT + GitHub bastarem.

### 3.8 Submit

1. Revise o draft inteiro
2. Cole as release notes do §1.3
3. Atestações de policy só depois de conferir listing, ZIP, prompts e testes
4. **Submit for Review**

Isto **não publica**. Fluxo: submit → review (prazo variável) → **você** publica no portal → aparece no diretório ChatGPT/Codex.

Erros de ZIP/listing: [submission-errors](https://developers.openai.com/plugins/deploy/submission-errors).

---

## 4. Quando cada lado “está no ar”

| Sinal | Claude community | OpenAI directory |
|---|---|---|
| Aprovado | SHA pinado em `claude-plugins-community` | Status aprovado no portal |
| Instalável pelo público | Nome `kata` no `marketplace.json` da community (sync noturno) | Você clicou **Publish** no portal |
| Como testar | `/plugin install kata@claude-community` num workspace limpo | Instalar pelo diretório no ChatGPT/Codex, chat novo, `$kata` |

Só depois dos **dois** installs públicos funcionarem vale o passo 4 (LinkedIn). Não antecipe post.

---

## 5. Não fazer

- Não enviar para `claude-plugins-official` nem escrever “oficial Anthropic / Claude”
- Não escolher **With MCP** no portal OpenAI
- Não incluir secrets, `.env`, nem código de cliente no ZIP
- Não apontar logo para SVG
- Não republicar no LinkedIn neste passo
- Não fazer force-push em `main` enquanto o pin da community aponta para o SHA

---

## 6. Checklist rápido

- [ ] `main` limpa, testes e `claude plugin validate` OK
- [ ] Identidade OpenAI verificada + Apps Management Write
- [ ] Claude Console: URL `https://github.com/andersonmalves/kata` enviada
- [ ] ZIP `/tmp/kata-1.0.0.zip` listado (manifest + `skills/kata/SKILL.md` + PNG)
- [ ] OpenAI: Skills only, short description do manifest (≤ 30), 5+3 testes, Submit for Review
- [ ] Esperar review; **não** postar
- [ ] Claude: confirmar `kata` no catalog community e install `@claude-community`
- [ ] OpenAI: Publish no portal e install pelo diretório
- [ ] Aí sim: passo 4
