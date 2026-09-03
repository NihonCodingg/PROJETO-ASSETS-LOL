# Sessão 03/09/2026 — decisão A, ADRs e protótipo

Continuação de [2026-09-03-bootstrap-e-spikes](2026-09-03-bootstrap-e-spikes.md).
Fecha o bloco 3 da etapa 3.

## O que foi feito

**Decisão A aprovada com mudança de princípio** (commit `315943a`)

- §A.4 do KICKOFF reescrita: "PNG sempre" revogado; entra "melhor fonte disponível,
  sem re-encode, com PNG gerado no cliente sob demanda". Item 7 passa a exigir **formato**
  além de resolução. Novo item 8 separa `splash` e `centered` como cortes distintos, com
  `centered` (1280×720) como padrão.
- §A.5 ajustada nos pontos de custo e de nome do produto.
- Quatro ADRs, com índice em [`docs/adr/README.md`](../adr/README.md):
  - **0001** formato de entrega — as cinco regras aprovadas, com os números que as
    justificam e as alternativas descartadas.
  - **0002** nomes canônicos `splash_centered` e `splash_wide`, porque ddragon e cdragon
    usam os nomes trocados. O teste de contrato passa a validar **dimensão**, não só
    status HTTP, e os termos "centered"/"uncentered" ficam proibidos no código.
  - **0003** nome público [A DECIDIR], sem "Riot", "League of Legends" nem "LoL". O
    marcador vive só em `siteConfig.displayName`; repositório e pacotes ficam como estão.
    O teste `site-config.test.ts` agora falha se o nome exibido violar a regra.
  - **0004** consentimento da Weird Gloop vira prioridade, com o argumento medido: as duas
    fontes automatizáveis empatam em 1280×720, e a categoria HD da wiki é a única fonte
    conhecida acima disso.

**Protótipo** (commit `063ad3f`)

`prototype/web/` — uma página, sem back-end, falando direto com o ddragon. Roda em
`http://localhost:3100`.

Verificado no navegador, não só compilado:

| O que foi testado | Resultado |
|---|---|
| Busca por `kaisa` | Kai'Sa, 1 de 173 |
| Busca por `belveth` | Bel'Veth |
| Busca por `mf` (apelido) | Miss Fortune |
| Atalho `/` | foca a busca e não insere a barra no campo |
| `Esc` | fecha o painel |
| Ficha do square | 128×128 · image/png · 25 KB |
| Ficha da splash centralizada | 1280×720 · image/jpeg · 121 KB |
| Ficha da splash aberta | 1215×717 · image/jpeg · 167 KB |
| Ficha do loading | 308×560 · image/jpeg · 50 KB |
| Conversão PNG no canvas | funciona, canvas **não** contaminado |
| Botão PNG em asset já PNG | desabilitado, rotulado "já é PNG" |

As fichas batem exatamente com o que os spikes mediram — o protótipo é uma segunda
confirmação independente das dimensões.

**Regra dos 3 cliques:** o fluxo completo custa **2 cliques**. A busca já nasce focada,
então digitar não conta; 1 clique abre o campeão, 1 clique baixa. Sobra folga para o
seletor de skin que a v1 vai ter.

**Dois bugs que só o teste no navegador pegaria:**

1. `ImageBitmap.close()` rodava antes do updater do `setState`, e `close()` zera
   `width`/`height` — a ficha aparecia como `0×0`. Corrigido lendo as dimensões antes de
   fechar.
2. O painel ficava **atrás** da barra de busca, porque `.topo` é `sticky` com `z-index: 5`
   e o painel não tinha `z-index`. Corrigido.

**Medição nova, registrada em `docs/SPIKES.md`:** o encoder PNG do navegador é pior que o
do Pillow. A splash centralizada de Miss Fortune sai de 123 KB (JPEG) para 1,005 MB (PNG),
**8,14×** — contra 5,71× do Pillow. Isso reforça o ADR 0001: pré-gerar PNG custaria 5,7×
no bucket e o usuário receberia 8,1× mesmo assim.

## O que foi assumido

- **Nome exibido provisório.** Coloquei "Catálogo de Assets" como placeholder: é
  descritivo, obviamente temporário e já respeita a restrição do ADR 0003. Não inventei
  marca.
- **Escopo do protótipo.** Só a skin base, só o ddragon, sem seletor de skin e sem
  categorias além de campeão — é o que a §A.4 item 2 precisa para ser medida.
- **Tabela de apelidos mínima** (15 entradas) só para checar se o problema é real. É, e
  vale um ticket próprio.
- **O protótipo não entra na CI.** `prototype/web` não declara `lint`, `typecheck` nem
  `test`, então `pnpm -r --if-present` o ignora. Foi typecheckado à mão.
- **`allowJs: true`** nos dois tsconfig de web, porque o Next reescreve o arquivo sozinho
  no primeiro `next dev` e sujava a árvore de trabalho.

## O que ficou pendente

1. **Caminho com acento** continua bloqueando `pnpm install` localmente. Tudo que é JS
   nesta sessão foi instalado, typecheckado, testado e executado no espelho em
   `C:\…\lolassets-mirror`; o `pnpm-lock.yaml` commitado veio de lá e passa em
   `pnpm install --frozen-lockfile`, que é o que a CI roda. **Decisão sua** — mover o
   repositório resolve.
2. **Nome público** e **texto exato do aviso legal** seguem marcados no código.
3. **Consentimento da Weird Gloop:** tarefa humana, agora prioritária (ADR 0004).
4. **Spike S4** (wiki) e a conferência dos emblemas de elo (§B.4) seguem não executados.

## Próximo passo sugerido

Etapa 4 — escrever `docs/SPEC.md`. A base está pronta: os spikes deram os números, os
quatro ADRs deram as decisões estruturais e o protótipo mostrou que o fluxo cabe em
2 cliques. As perguntas que a Spec ainda precisa fechar e que dependem de você são o
seletor de skin na v1 e o corte do catálogo por versão.
