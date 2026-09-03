# ADR 0011 — Base de componentes: shadcn/ui sobre Radix, TanStack Virtual, cmdk

- **Status:** aceito
- **Data:** 2026-09-03
- **Decidido por:** dono do projeto
- **Afeta:** §0.3 do [KICKOFF](../KICKOFF.md), que previa Fuse.js e não mencionava virtualização

## Contexto

A §0.3 fixou a stack do front antes de existir qualquer medição: *"Next.js 15+, TypeScript
strict, Tailwind, Fuse.js para busca no cliente, JSZip apenas como fallback offline"*.
Três coisas mudaram desde então:

1. **Fuse.js ficou sem função.** O protótipo mostrou que normalizar o texto (NFD, remover
   diacríticos, remover não-alfanuméricos) já acerta `kaisa`, `belveth` e `chogath`, e o
   [ADR 0009](0009-apelidos-de-busca-mantidos-a-mao.md) resolveu o resto com uma tabela de
   apelidos mantida à mão. A meta da §A.7 é **acertar em primeiro lugar**, e busca difusa
   tende a piorar exatamente isso.
2. **O JSZip deixou de ser fallback.** O [ADR 0005](0005-arquitetura-estatica-custo-zero.md)
   o promoveu a caminho principal da seleção customizada, porque não há servidor para zipar.
3. **Apareceu um problema de renderização que a §0.3 não previa.** O
   [ADR 0010](0010-navegacao-por-campeao-busca-por-skin.md) deixou a navegação com 173
   entradas — tranquilo —, mas a busca opera sobre **2.149 skins**, e as categorias do
   RF-08 chegam a **5.021 ícones de perfil** e **2.347 emotes**. Renderizar milhares de nós
   de uma vez trava a rolagem em qualquer máquina.

## Decisão

A base de componentes do `apps/web` passa a ser:

### 1. shadcn/ui sobre Radix

Primitivas acessíveis (diálogo, popover, tabs, tooltip, toggle) via Radix, com os
componentes do shadcn **copiados para dentro do repositório**, não instalados como
dependência.

Por quê:

- A acessibilidade do **RNF-11** (foco, `aria`, navegação por teclado, foco preso em
  diálogo) vem pronta e auditável, em vez de ser reimplementada a cada componente.
- Como o código fica no repositório, o **T-30** pode vestir tudo com os tokens do design
  sem lutar contra estilos de uma biblioteca — que é exatamente o critério de aceite dele:
  a suíte inteira continua passando, só a aparência muda.
- Radix é **sem estilo por padrão**. Nada nele carrega identidade visual de ninguém, o que
  mantém a conformidade com §B.5.1 (o produto não pode se parecer com o cliente do jogo).

### 2. TanStack Virtual para as listas grandes

Virtualização de janela onde a contagem justifica, e **só** onde justifica:

| Superfície | Itens | Virtualiza? |
|---|---:|---|
| Grade de campeões (padrão) | 173 | **Não** — não paga o custo |
| Resultados de busca de skin | até 2.149 | **Sim** |
| Skins dentro do painel do campeão | até ~90 | Não |
| Categorias grandes (perfil, emotes) | 5.021 / 2.347 | **Sim** |

O RNF-01 (< 50 ms) é sobre **buscar**; virtualização é sobre **desenhar**. São dois custos
diferentes e os dois precisam caber.

### 3. cmdk para a paleta de busca — a UI, não o algoritmo

cmdk entra pela lista acessível, a navegação por teclado e a semântica de combobox.

**O filtro embutido do cmdk fica desligado.** O algoritmo de busca continua sendo o nosso:
normalização + tabela de apelidos ([ADR 0009](0009-apelidos-de-busca-mantidos-a-mao.md)) +
o ranqueamento de duas classes do [ADR 0010](0010-navegacao-por-campeao-busca-por-skin.md)
(campeão casado aparece uma vez; skin casada vem rotulada com o campeão). Deixar o cmdk
filtrar sozinho quebraria `mf`, `j4` e `kda` sem avisar — por isso vira **teste**, não
convenção.

### 4. Fuse.js está fora

Não entra no `package.json`. Se algum dia aparecer caso real de busca sem resultado que a
normalização não resolva, isso vira ticket próprio com o caso concreto em mãos — não uma
dependência preventiva.

## Consequências

**Boas**

- RNF-11 deixa de ser trabalho manual em cada componente.
- A rolagem das categorias grandes fica viável sem paginação, que seria pior para quem
  procura um ícone específico.
- Ter os componentes no repositório significa que o design do T-30 é aplicado por tokens,
  em um lugar só.

**Ruins / custos aceitos**

- **shadcn copia código.** Os PRs de UI ganham linhas que não são lógica. Para efeito da
  regra 5 do [CLAUDE.md](../../CLAUDE.md), **componente gerado pelo shadcn conta como
  scaffold, não como lógica** — do mesmo jeito que lockfile e fixture. Sem isso, um ticket
  de UI estoura o limite de 500 sem ter escrito 500 linhas de decisão.
- Virtualização e altura de item variável brigam. A grade usa **altura fixa por
  breakpoint**; se o design pedir cartão de altura variável, isso vira conversa no T-30 e
  não uma gambiarra de medição.
- Mais três dependências no front. Todas com propósito nomeado aqui; qualquer quarta
  precisa de ADR.
- O filtro do cmdk desligado é uma armadilha silenciosa para quem mexer depois. Mitigado
  por teste que falha se ele voltar a filtrar.

## Alternativas descartadas

- **Fuse.js**, como a §0.3 previa: piora a precisão do primeiro resultado, que é a meta.
- **`react-window` / `react-virtuoso`** no lugar do TanStack Virtual: funcionam, mas o
  TanStack é headless, o que combina com aplicar os tokens depois no T-30.
- **MUI, Chakra ou qualquer kit com opinião visual forte:** brigariam com o design e
  arriscariam aproximar o visual de algo pronto, quando §B.5.1 pede o contrário.
- **Lista sem virtualização, com paginação:** 5.021 ícones de perfil em páginas obriga o
  usuário a caçar de página em página. Rolar é o gesto certo aqui.
- **Escrever as primitivas na mão:** é reimplementar acessibilidade já resolvida, num
  projeto de uma pessoa.
