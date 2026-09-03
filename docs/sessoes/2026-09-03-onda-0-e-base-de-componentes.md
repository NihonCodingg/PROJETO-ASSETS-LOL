# Sessão 03/09/2026 — Onda 0 executada; ingestão do design bloqueada

## Parte 1 — Onda 0 concluída

### T-02: orçamento fechado (commit `388ea0a`)

Emotes e ward skins eram os dois buracos do RNF-05. Medidos por amostragem aleatória com
semente fixa (`20260903`), 40 arquivos cada. De quebra fecharam-se os dois buracos menores.

| Categoria | Arquivos | Total | Como |
|---|---:|---:|---|
| Emotes | 2.338 | 156,5 MB | amostra de 40, todos 256×256 PNG |
| Ward skins | 530 | 7,7 MB | amostra de 40, 460×550 PNG |
| Loading vintage | 915 | 51,1 MB | proporção medida no S2 (42,6 % das skins) |
| Emblemas de elo | zip | 61,5 MB | `Content-Length` do zip oficial da Riot |

**Orçamento de uma versão: 26.346 arquivos, 2,0 GB — 20,1 % do tier gratuito de 10 GB.**
A condição de parada **não** foi disparada. A projeção do ADR 0007 era ~1,9 GB; o medido é
2,0 GB.

Três coisas que a medição corrigiu:

- **Ward skin tem duas imagens**, não uma: `wardImagePath` e `wardShadowImagePath`. São 530
  arquivos, não 265.
- **9 das 2.347 entradas de emote têm `inventoryIcon` vazio.** Sobram 2.338 reais.
- **O zip de emblemas de elo responde 200**, o que confirma §B.4 e dispensa o cdragon para
  a categoria.

Onde havia número exato (o tarball, medido em 100 % dos arquivos no S1), usei o exato;
extrapolação só onde não havia.

### T-01: protótipo removido (commit `4c4b788`)

O `prototype/` deixou de existir. As evidências foram para `docs/evidencias/spikes/`
**antes** de apagar — sem isso a base de tudo que a Spec decide teria sumido junto.

Também: `pnpm-workspace.yaml`, `pyproject.toml` (exclusões de ruff e mypy), `.gitignore`,
`CLAUDE.md`, `README.md`, a estrutura do KICKOFF, a seção "Como reproduzir" do `SPIKES.md`
(que agora ensina a recuperar os scripts do histórico) e o ADR 0004, cuja trava da wiki
vivia no cliente HTTP dos spikes e passa a ser recriada, com teste, no T-03.

Suíte verde: ruff, format, mypy e 12 testes Python; eslint, tsc e 3 de vitest;
`pnpm install --frozen-lockfile` em exit 0; nenhum link relativo quebrado.

## Parte 2 — o que deu para fazer e o que não deu

### 🚫 A ingestão do design está bloqueada

**`docs/design/` não existe.** Verifiquei de quatro formas: o diretório não está no
working tree; `origin/main` está no mesmo commit que o local; não há outra branch; e
`git log --all --diff-filter=A` não encontra nenhum `.dc.html`, nenhum `support.js` e
nenhum caminho sob `design/` em ponto nenhum do histórico. O commit das telas não chegou
ao repositório.

Além disso, **o MCP do Claude Design não está conectado a esta sessão**. O que existe aqui
é o `DesignSync`, que lê e escreve projetos de *design system* do claude.ai — coisa
diferente de importar um artboard `.dc.html` —, e um importador que manda um design para a
Vercel. Nenhum dos dois traz o arquivo para cá, e `/design-login` é um comando de terminal
interativo que esta sessão não roda.

Por isso **os itens 1, 2, 3, 4 e a parte de tokens do item 6 não foram feitos**. Extrair
"escala de cinzas, cor de destaque única, escala tipográfica" de arquivos que não consigo
ler seria inventar um sistema de design e chamar de leitura — exatamente o que a regra 2 do
CLAUDE.md proíbe. Preferi parar e avisar.

### ✅ Item 5 feito: ADR 0011

[`0011-base-de-componentes-do-front.md`](../adr/0011-base-de-componentes-do-front.md) não
depende das telas, então foi entregue inteiro:

- **shadcn/ui sobre Radix**, com os componentes copiados para o repositório. A
  acessibilidade do RNF-11 vem pronta e auditável, e o T-30 veste por token em vez de lutar
  contra estilos de biblioteca.
- **TanStack Virtual**, e a decisão de **onde**: os 173 campeões da grade padrão não
  virtualizam; os até 2.149 resultados de busca de skin e as categorias grandes (5.021
  ícones de perfil, 2.347 emotes) sim. RNF-01 é sobre buscar; virtualização é sobre
  desenhar — dois custos diferentes.
- **cmdk pela UI da paleta, com o filtro embutido desligado.** O algoritmo continua sendo o
  nosso. Deixar o cmdk filtrar quebraria `mf`, `j4` e `kda` em silêncio, então virou teste.
- **Fuse.js fora**, fechando o que a §0.3 ainda previa e que ADR 0009 e Spec já
  contradiziam.

Consequência que precisou de decisão explícita: **componente gerado pelo shadcn conta como
scaffold, não como lógica**, para o limite de 500 linhas da regra 5. Sem isso um ticket de
UI estoura o limite sem ter escrito 500 linhas de decisão.

**§0.3 do KICKOFF** reescrita: entra a base de componentes, sai o Fuse.js, e o JSZip passa
de "fallback offline" a caminho principal (o que o ADR 0005 já tinha decidido e a §0.3
ainda não refletia).

### ✅ Item 6, na parte que não depende das telas

- **T-34 novo** — "Base de componentes e tokens do design", marcado 🚧 **bloqueado** na
  ingestão. É o único lugar que traduz `TOKENS.md` para o tema do Tailwind.
- **T-14** ganha cmdk e o teste que falha se o filtro voltar.
- **T-19** ganha TanStack Virtual nos resultados, altura fixa por breakpoint e um teste que
  conta nós no DOM.
- **T-24** ganha virtualização nas categorias grandes.
- **T-30** passa a depender de T-34 e a conferir cada tela contra `docs/design/`.
- A nota de UI no topo do documento agora avisa que `TOKENS.md` não existe e que **só T-34
  e T-30 estão bloqueados** — os demais tickets de UI seguem executáveis, com a tela crua,
  que é o combinado.

São **34 tickets**; os 25 RF e 12 RNF continuam cobertos.

## O que foi assumido

- **Critério de aceite 3 do T-01 afrouxado, com o motivo escrito no ticket.** A redação
  original ("`grep prototype/` só em `docs/sessoes/`") não previa que o próprio
  `TICKETS.md` descreve o trabalho de apagar o `prototype/`. O critério agora é que não
  reste referência **operante** — nenhum caminho que alguém tente executar hoje.
- **T-34 é ticket novo**, não previsto na lista aprovada. Instalar a base e traduzir tokens
  é trabalho compartilhado por T-14, T-19 e T-24; smear isso em três tickets produziria
  três configurações divergentes.
- **A virtualização não é universal.** O ADR restringe a onde a contagem justifica, em vez
  de virtualizar tudo por reflexo.

## O que ficou pendente

1. **A ingestão do design.** Precisa das telas no repositório. Dois caminhos:
   (a) você comita e envia `docs/design/`; ou (b) você me autoriza a abrir o projeto do
   Claude Design no seu Chrome logado, ler o artboard de lá e commitar o HTML em
   `docs/design/` eu mesmo.
2. **T-34 e T-30** seguem bloqueados até isso.
3. As decisões **D1, D2, D5, D6 e D7** da §13 da Spec. **D4 saiu da lista** — foi fechada
   pelo T-02.

## Próximo passo sugerido

A **Onda 1** está liberada: o orçamento fechou com folga e nada nela depende do design.
Ela começa com T-03 e T-04 em paralelo. A ingestão do design pode acontecer a qualquer
momento sem atrapalhar, porque só T-34 e T-30 esperam por ela.
