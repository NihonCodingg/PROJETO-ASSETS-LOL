# SPEC v1 — catálogo de assets visuais de League of Legends

> Etapa 4 das 7. Escrita a partir de [`KICKOFF.md`](KICKOFF.md), dos números reais de
> [`SPIKES.md`](SPIKES.md), dos nove [ADRs](adr/README.md) e do que o protótipo do bloco 3
> ensinou. **Esta Spec tem precedência sobre o KICKOFF** (regra 1 do
> [CLAUDE.md](../CLAUDE.md)); os ADRs têm precedência sobre ela nos pontos que decidem.
>
> Data: 03/09/2026 · patch de referência: 16.17.1 · contrato do índice: `1.1.0`
>
> **Revisão de 03/09/2026:** navegação e busca passam a operar em níveis diferentes —
> ver [ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md), que emenda o
> [ADR 0008](adr/0008-catalogo-de-skins-e-seletor.md). Os requisitos são numerados de
> forma incremental: RF-24 e RF-25 entram no fim para não invalidar as referências
> já feitas em [`TICKETS.md`](TICKETS.md).

---

## 1. Visão e não-objetivos

### 1.1 Visão

Um site estático onde um editor de vídeo de League of Legends acha e baixa qualquer asset
visual do jogo em segundos, sem login, sem instalar nada e sem saber o que é "ddragon".
Uso pessoal e de um pequeno grupo de amigos, custo de operação **zero**, sem monetização.

### 1.2 Não-objetivos da v1

| Fora | Por quê |
|---|---|
| Stats, builds, patch notes, dados de partida | Não é o job to be done (§A.3) |
| Contas, login, favoritos sincronizados | Exige back-end e estado; o site é estático ([ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md)) |
| Edição de imagem (recorte, remoção de fundo, resize) | O usuário já tem Photoshop aberto |
| Upload de assets pelo usuário | Sem back-end e sem moderação |
| Assets de TFT, Wild Rift, Valorant | 634 MB só de TFT, fora do escopo (SPIKES S1) |
| API pública documentada para terceiros | [ADR 0006](adr/0006-api-como-componente-opcional.md) |
| Monetização de qualquer forma | [ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md), regra 6 |
| Assets da wiki | Bloqueado até consentimento ([ADR 0004](adr/0004-consentimento-da-wiki-e-teto-de-resolucao.md)) |
| Splash, loading e tile de versões antigas | Fisicamente impossível: essas URLs do ddragon não são versionadas ([ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md)) |

---

## 2. Personas e jobs to be done

**Persona única: o editor.** Faz vídeo e thumbnail de LoL, usa Premiere/After
Effects/Photoshop, nível técnico variado. Está no meio de uma edição quando precisa do
asset. Não vai ler nada.

| # | Job to be done | O que a v1 entrega |
|---|---|---|
| J1 | "Preciso do square do Jax pro canto do vídeo" | Busca ou grade → campeão → baixar |
| J2 | "Preciso da splash da skin Jax Deus da Guerra em alta" | Busca pelo nome da skin → abre o painel do campeão já naquela skin → baixar |
| J7 | "Preciso das skins K/DA de vários campeões pra uma thumbnail temática" | Busca por termo transversal → skins de campeões diferentes ([ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md)) |
| J3 | "Preciso de todos os ícones de item pra uma build animada" | Zip da categoria `item`, pré-gerado |
| J4 | "Preciso do ícone de Diamante IV" | Categoria `rank` |
| J5 | "Esse vídeo é de patch antigo, preciso do square antigo do Aatrox" | Seletor de versão — **só tipos versionados** |
| J6 | "Preciso de tudo do Jax" | Seleção no cliente → zip com JSZip |

---

## 3. Requisitos funcionais

Cada RF tem critério de aceite testável. O identificador é citado pelo ticket que o
implementa e pelo teste que o prova.

### Catálogo e busca

| # | Requisito | Critério de aceite |
|---|---|---|
| **RF-01** | A home é a busca, com foco automático e resultados enquanto digita | Ao carregar, `document.activeElement` é o campo de busca; digitar 1 caractere já altera a lista |
| **RF-02** | A busca é tolerante a acento, maiúscula e apóstrofo | `kaisa`→Kai'Sa, `belveth`→Bel'Veth, `chogath`→Cho'Gath, `KAI'SA`→Kai'Sa, todos em 1º lugar |
| **RF-03** | A busca resolve apelidos da tabela mantida à mão | `mf`→Miss Fortune, `tf`→Twisted Fate, `j4`→Jarvan IV, `asol`→Aurelion Sol em 1º lugar |
| **RF-04** | **A navegação padrão é por campeão** — 173 entradas | Sem nada digitado, a grade tem 173 cartões, um por campeão, cada um com a arte da skin base e o número de skins |
| **RF-05** | **A busca opera no nível de skin e também casa campeão**; um campeão casado aparece **uma** vez | `jax` retorna 1 entrada de campeão, não 18 de skin; `deus da guerra` retorna a skin em 1º lugar |
| **RF-06** | Chromas não aparecem como resultado de primeiro nível | Nenhum dos 7.037 chromas aparece na lista; ficam atrás de um toggle dentro da skin, no painel do campeão |
| **RF-07** | Atalho `/` foca a busca sem inserir o caractere | Após `/`, o foco é o campo e o valor não mudou |
| **RF-08** | Navegação por categoria com filtros | Filtros de função, lane, comprável, mapa, árvore de runa e elo alteram a lista |
| **RF-24** | **Busca por termo transversal a vários campeões** | `kda` e `prestigio` retornam skins de ≥ 3 campeões distintos, cada resultado rotulado com o campeão de origem |
| **RF-25** | **O seletor de skin vive no painel do campeão** | Abrir um campeão lista as skins dele; clicar num resultado de skin abre o painel do campeão **já com aquela skin selecionada** |

### Asset e download

| # | Requisito | Critério de aceite |
|---|---|---|
| **RF-09** | O card mostra formato, resolução, tamanho e fonte **antes** do download | O card exibe `1280×720 · image/jpeg · 121 KB · ddragon` sem nenhum clique extra |
| **RF-10** | Download individual entrega os **bytes de origem**, sem re-encode | O `sha256` do arquivo baixado é igual ao `sha256` do índice |
| **RF-11** | O botão "Baixar PNG" converte no navegador, no clique | O arquivo salvo é `image/png` com as mesmas dimensões; nenhum PNG foi armazenado no bucket |
| **RF-12** | Asset com origem PNG não oferece conversão | O botão aparece desabilitado com rótulo "já é PNG" |
| **RF-13** | Nome de arquivo previsível | `Jax_004_splash_centered.jpg`, `Item_3031.png`, `Rank_Diamond_IV.png` — casa com `^[A-Za-z0-9_.-]+\.(png\|jpg)$` |
| **RF-14** | Copiar URL direta do arquivo | O clipboard recebe a URL pública que responde 200 |
| **RF-15** | Do carregamento ao arquivo salvo: no máximo 3 cliques | Teste e2e conta os cliques do fluxo J1 e J2 e falha em > 3 |

### Lote e versões

| # | Requisito | Critério de aceite |
|---|---|---|
| **RF-16** | Zip por categoria é pré-gerado e baixado direto do bucket | O download não executa JavaScript de compressão; o `Content-Length` bate com o manifesto |
| **RF-17** | Zip de seleção customizada é montado no cliente | Selecionar N assets e baixar produz um zip com N arquivos, sem nenhuma requisição a um servidor próprio |
| **RF-18** | "Tudo do Jax" é uma seleção pré-montada | Um clique seleciona todos os assets do campeão; o zip sai pelo caminho do RF-17 |
| **RF-19** | Seletor de versão, com a atual por padrão | O manifesto lista as versões; trocar recarrega o índice daquela versão |
| **RF-20** | Em versão anterior, tipos indisponíveis são explicitamente ausentes | Splash, loading e tile não aparecem; a UI diz por quê, em vez de servir a arte atual |

### Institucional

| # | Requisito | Critério de aceite |
|---|---|---|
| **RF-21** | Aviso legal da Riot visível | O texto está no rodapé de toda página; teste falha se sumir |
| **RF-22** | Página "Sobre" com créditos, licenças e fontes | Cita Riot, ddragon, cdragon e — se autorizado — a wiki/Weird Gloop |
| **RF-23** | O nome exibido não contém "Riot", "League of Legends" nem "LoL" | Teste já existente em `site-config.test.ts` |

---

## 4. Requisitos não funcionais

| # | Requisito | Meta mensurável | Como se mede |
|---|---|---|---|
| **RNF-01** | Busca responde rápido | < 50 ms do keystroke ao render, com 173 campeões e 2.149 skins no índice | `performance.measure` no e2e |
| **RNF-02** | Imagem abre rápido | < 1 s para a prévia da splash em conexão de banda larga | e2e com timing |
| **RNF-03** | Carga inicial enxuta | **Catálogo ≤ 150 KB comprimido** (é o único documento pesado da abertura); fatia de assets ≤ 1,5 MB comprimida e carregada **sob demanda** | Falha o build se qualquer um passar |
| **RNF-04** | Custo de operação | **R$ 0,00/mês**: Vercel Hobby + R2 free (10 GB) + Actions em repo público | Revisão mensal do painel |
| **RNF-05** | Armazenamento | ≤ 10 GB; uma versão medida em ~1,9 GB | O indexador falha se o total projetado passar de 8 GB |
| **RNF-06** | Atualização | Novo patch refletido em ≤ 24 h, sem intervenção | Workflow agendado + `status.json` |
| **RNF-07** | Resiliência | Se ddragon/cdragon caírem, o site continua com o último índice publicado | Nenhuma requisição do navegador vai às fontes |
| **RNF-08** | Etiqueta de rede | User-Agent identificado, concorrência ≤ 4, backoff em 429/5xx | Teste unitário do cliente HTTP |
| **RNF-09** | Wiki | Zero requisições enquanto `WIKI_CONSENT_GRANTED` for falso | Trava em código que levanta exceção |
| **RNF-10** | Legal | Aviso da Riot visível; produto registrado no Developer Portal antes do lançamento | Checklist de lançamento |
| **RNF-11** | Acessibilidade | Navegável por teclado, contraste AA, `alt` em toda imagem | axe no e2e |
| **RNF-12** | Qualidade | ruff, ruff format, mypy strict, pytest, eslint, tsc, vitest verdes em todo PR | CI |

---

## 5. Arquitetura

### 5.1 Visão geral

```mermaid
flowchart LR
    subgraph fontes["Fontes (só o indexador toca)"]
        DD[Data Dragon<br/>tarball por patch]
        CD[Community Dragon<br/>JSONs v1/]
        RS[Riot static<br/>ranked-emblems.zip]
        WK[Wiki / Weird Gloop<br/>DESLIGADO]
    end

    subgraph ci["GitHub Actions · agendado por patch"]
        IDX[packages/indexer<br/>adaptadores → fusão → publicação]
    end

    subgraph r2["Cloudflare R2 + CDN · estático"]
        MAN[manifest.json]
        CAT["catalog-hash.json<br/>173 campeões · 2.149 skins"]
        SHARD["index-*-hash.json<br/>assets · sob demanda"]
        ASSET[assets nos bytes de origem]
        ZIP[zips por categoria]
    end

    subgraph vercel["Vercel Hobby"]
        WEB[apps/web<br/>Next.js · busca no cliente]
    end

    USER([editor])

    DD --> IDX
    CD --> IDX
    RS --> IDX
    WK -. bloqueado .-> IDX
    IDX --> MAN & CAT & SHARD & ASSET & ZIP
    USER --> WEB
    WEB --> MAN & CAT
    WEB -. sob demanda .-> SHARD
    USER --> ASSET & ZIP

    API[apps/api · FastAPI<br/>opcional, local]
    API -.->|alternativa, fora do caminho crítico| SHARD
```

**A linha que define o projeto:** o tráfego do usuário nunca toca a Riot, e nunca toca um
servidor nosso.

### 5.2 Componentes

| Componente | Responsabilidade | Não faz |
|---|---|---|
| `packages/indexer` | Baixar, medir, fundir, nomear, publicar, gerar zips por categoria | Nunca converte imagem |
| `packages/schema` | JSON Schema do índice, tipos TS, modelos Pydantic, tabela de apelidos | Nada de runtime |
| `apps/web` | Busca, navegação, preview, download, conversão PNG, zip de seleção | Nunca chama a Riot nem exige a API |
| `apps/api` | Alternativa opcional de portfólio | Nada do que o site precisa ([ADR 0006](adr/0006-api-como-componente-opcional.md)) |

### 5.3 Fluxo de indexação

```mermaid
sequenceDiagram
    participant A as GitHub Actions
    participant D as ddragon
    participant C as cdragon
    participant P as Pillow
    participant R as R2

    A->>D: GET /api/versions.json
    A->>A: versão nova? senão encerra
    A->>D: GET dragontail-{v}.tgz (2,39 GB, 1 requisição)
    A->>A: extrai só data/{pt_BR,en_US} e os img/ do escopo
    A->>C: GET v1/champions/{key}.json (concorrência ≤ 4)
    Note over A,C: só caminhos declarados no JSON; nunca montados à mão
    A->>P: mede width, height, format, hasAlpha, sha256
    A->>A: fusão por (identidade, tipo) → nomes canônicos
    A->>A: projeta o catálogo: 173 campeões e 2.149 skins, sem asset
    A->>A: valida contra o JSON Schema; falha aborta tudo
    A->>R: publica assets, catálogo, fatias do índice e zips
    A->>R: publica manifest.json (último passo, commit atômico)
    A->>R: remove os assets do patch anterior
    A->>A: escreve status.json e o resumo do job
```

**Ordem importa:** o `manifest.json` é sempre o **último** a subir e o **primeiro** a ser
lido. Enquanto ele não muda, o site continua servindo a versão antiga, íntegra. A remoção
do patch anterior só acontece **depois** do manifesto novo estar publicado e verificado.

### 5.4 Fluxo de consulta

```mermaid
sequenceDiagram
    participant U as Editor
    participant W as apps/web (Vercel)
    participant R as R2 + CDN

    U->>W: abre o site
    W->>R: GET manifest.json (TTL curto)
    W->>R: GET catalog-{hash}.json (imutável, ~150 KB)
    W->>W: desenha 173 campeões e monta o índice de busca de 2.149 skins + apelidos
    U->>W: digita "mf" ou "kda"
    W->>W: busca no cliente (< 50 ms, sem rede)
    U->>W: clica no campeão (ou num resultado de skin)
    W->>R: GET index-champion-{hash}.json (sob demanda, uma vez)
    W->>U: painel do campeão, com o seletor de skin
    W->>R: GET dos assets da skin (bytes de origem)
    W->>U: mostra formato, resolução, tamanho, fonte
    U->>W: "Baixar original" → salva o blob
    U->>W: "Baixar PNG" → canvas → toBlob → salva
```

### 5.5 Fluxo de download em lote

```mermaid
flowchart TD
    A[usuário quer vários assets] --> B{categoria inteira?}
    B -->|sim| C[GET zip pré-gerado no R2]
    B -->|não| D[seleção no cliente]
    D --> E[fetch de cada asset já em cache do navegador]
    E --> F[JSZip monta em memória]
    F --> G[download do blob]
    C --> H([arquivo salvo])
    G --> H
```

**Limite prático:** acima de 300 arquivos ou 500 MB de seleção, a UI recomenda o zip por
categoria em vez de montar no cliente. É recomendação, não bloqueio.

---

## 6. Contrato do índice

Fonte de verdade: [`packages/schema/schemas/`](../packages/schema/schemas/).
Versão do contrato: **1.0.0**. Mudança exige ADR e nova versão.

| Arquivo | Papel |
|---|---|
| `index-manifest.schema.json` | O `manifest.json` — único arquivo de nome fixo no bucket |
| `catalog.schema.json` | **Projeção de navegação (173 campeões) e de busca (2.149 skins)**, sem nenhum asset. É o único documento pesado da abertura ([ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md)) |
| `index-shard.schema.json` | Uma fatia de **assets** por categoria e versão, com `$defs.asset`. Carregada sob demanda |
| `data/champion-aliases.json` | Apelidos de busca, mantidos à mão ([ADR 0009](adr/0009-apelidos-de-busca-mantidos-a-mao.md)) |

O registro de asset carrega `id`, `type` (nome canônico), `category`, as chaves de
identidade (`championKey`, `championId`, `skinId`, `skinNum`, `itemId`, `refId`), `names`
por idioma, `aliases`, `tags`, `source`, `sourceUrl`, `storageKey` (opcional), `fileName`,
`width`, `height`, `format`, `hasAlpha`, `bytes` e `sha256`.

Duas regras estão **no schema**, não só na prosa, e há teste que prova cada uma:

- `hasAlpha: true` obriga `format: "png"` — JPEG não carrega alfa ([ADR 0001](adr/0001-formato-de-entrega-dos-assets.md) regra 4).
- Assets de corte de splash exigem `skinId` e `skinNum`.

### 6.1 Ordem de carga e fatiamento

Três camadas, carregadas nesta ordem:

1. **`manifest.json`** — nome fixo, TTL curto. Diz qual é a versão atual e onde está tudo.
2. **`catalog-{hash}.json`** — as duas projeções do [ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md):
   `champions[]` para navegar e `skins[]` para buscar. Sem asset, sem hash de arquivo, sem
   URL de origem. É o que permite desenhar a home e ter busca funcionando **antes** de
   qualquer asset ser baixado.
3. **`index-{categoria}-{hash}.json`** — os assets, uma fatia por categoria, com hash no
   nome. Carregadas **sob demanda**: a de `champion` na primeira vez que um painel abre, as
   demais ao entrar na categoria.

A home não carrega fatia de asset nenhuma. Isso é o que sustenta o RNF-03.

### 6.2 Convenção de nomes de arquivo

| Categoria | Padrão | Exemplo |
|---|---|---|
| Campeão, por skin | `{championId}_{skinNum:03d}_{type}.{ext}` | `Jax_004_splash_centered.jpg` |
| Campeão, por campeão | `{championId}_{type}.{ext}` | `Jax_square.png` |
| Item | `Item_{itemId}.png` | `Item_3031.png` |
| Runa, feitiço, emote, ward | `{Type}_{refId}.png` | `Rune_8005.png` |
| Elo | `Rank_{tier}_{divisão}.png` | `Rank_Diamond_IV.png` |

A extensão é a do **formato de origem**. O PNG convertido no cliente troca só a extensão.

---

## 7. Contrato da API (opcional)

A API não está no caminho crítico. Quando o ticket dela for executado, o contrato é:

```yaml
openapi: 3.1.0
info: { title: lol-assets API, version: 0.1.0 }
paths:
  /health:
    get: { responses: { "200": { description: "status e versão" } } }        # já existe
  /versions:
    get: { responses: { "200": { description: "espelha o manifest.json" } } }
  /index/{gameVersion}/{category}:
    get: { responses: { "200": { description: "fatia do índice" }, "404": {} } }
  /zip:
    post:
      requestBody: { description: "lista de ids de asset" }
      responses: { "200": { description: "application/zip" }, "413": { description: "seleção grande demais" } }
```

Nenhum requisito funcional depende destes endpoints.

---

## 8. Modelo de dados e política de versões

**Dois níveis, de propósito** ([ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md)):

| Nível | Onde vive | Entradas | Serve a |
|---|---|---:|---|
| Campeão | `catalog.champions[]` | 173 | Navegação: a grade padrão |
| Skin | `catalog.skins[]` | 2.149 | Busca, inclusive por termo transversal ("K/DA") |
| Asset | `index-{categoria}` | ~20 mil | Download; carregado sob demanda |

**Identidade.** `championKey` numérico é a chave de fusão entre fontes;
`skinId = {championKey}{skinNum:03d}` é a chave natural da skin (Jax Deus da Guerra =
`24004`) e a junção entre os dois níveis. Chromas são identificados por `parentSkinNum` e
não são entradas de primeiro nível em nenhum dos dois.

**Fusão.** Para cada `(identidade, tipo canônico)`, vence a maior resolução; empate
favorece o ddragon. Os spikes mostraram que **para assets de campeão é sempre empate** — o
cdragon entra por cobertura (chromas, loading vintage), não por resolução.

**Versões** ([ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md)):

| | Versão atual | Versões anteriores |
|---|---|---|
| Assets no R2 | sim (~1,9 GB) | não |
| `storageKey` no índice | presente | ausente |
| Origem servida ao usuário | R2 | `sourceUrl` do ddragon |
| Tipos disponíveis | todos | **só os versionados**: square, item, spell, passive, profile_icon, map |
| Splash, loading, tile | sim | **não existem** — essas URLs não são versionadas |

---

## 9. Cache e CDN

| Recurso | Nome | Cache-Control | Por quê |
|---|---|---|---|
| `manifest.json` | fixo | `max-age=300, stale-while-revalidate=86400` | Único ponto de invalidação |
| Catálogo | com hash | `max-age=31536000, immutable` | Conteúdo novo = nome novo |
| Fatias do índice | com hash | `max-age=31536000, immutable` | Conteúdo novo = nome novo |
| Assets | `{versão}/{categoria}/{fileName}` | `max-age=31536000, immutable` | Nunca mudam dentro de uma versão |
| Zips por categoria | com hash | `max-age=31536000, immutable` | Idem |

Publicar um patch novo troca **um** arquivo de nome fixo. Nada precisa ser purgado.

---

## 10. Estratégia de testes

| Camada | O que prova | Onde roda |
|---|---|---|
| **Unitário (Python)** | Normalização de nomes, fusão, mapa fonte→canônico, cliente HTTP (User-Agent, concorrência, backoff), convenção de nome de arquivo | Todo PR |
| **Contrato de schema** | Os JSON Schema são válidos; um asset de exemplo passa; alfa em JPEG é rejeitado | Todo PR (já existe) |
| **Contrato de fonte** | Baixa 3 campeões conhecidos e valida que cada tipo existe **e tem a dimensão esperada** — 1280×720 para `splash_centered`, 1215×717 para `splash_wide` ([ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md)) | Agendado, **não** em PR; falha abre issue, não bloqueia deploy |
| **Contrato de apelidos** | Todo id da tabela existe no `champion.json` do patch atual | Agendado |
| **Unitário (TS)** | Busca normalizada, resolução de apelido, ranqueamento, conversão PNG | Todo PR |
| **e2e (Playwright)** | Fluxo buscar→baixar em ≤ 3 cliques; RF-02, RF-03, RF-09, RF-11, RF-13 | Todo PR |

Testes que tocam a rede **nunca** rodam em PR: são lentos, instáveis e barulhentos com as
fontes. Rodam agendados e o resultado vira issue.

---

## 11. Observabilidade sem servidor

Não há processo para instrumentar, mas a indexação pode falhar em silêncio — e é o único
jeito de o site apodrecer.

1. **`status.json` publicado no bucket** a cada execução: versão indexada, duração, assets
   por fonte, bytes publicados, falhas por tipo, dimensões inesperadas.
2. **Resumo do job no GitHub Actions** com a mesma tabela, legível sem baixar nada.
3. **Falha abre issue automaticamente** com o log — inclusive quando um teste de contrato
   de fonte quebra. É o alerta que a §0.3 pede.
4. **O site mostra a idade do índice.** Se `manifest.generatedAt` tem mais de 72 h, aparece
   um aviso discreto. É o detector de "parou de atualizar" que não custa nada.
5. **Logs estruturados** (JSON por linha) no indexador, com `gameVersion` e `source` em
   todo evento.

---

## 12. Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| cdragon muda caminhos | Assets somem do catálogo | Nunca montar caminho; partir do JSON. Teste de contrato agendado → issue |
| ddragon troca a resolução de publicação | Fusão escolhe errado | Teste de contrato valida **dimensão**, não só status |
| Grafia de `championId` muda entre patches | Apelidos e URLs quebram | Teste de contrato dos apelidos; `Fiddlesticks`×`FiddleSticks` já aconteceu |
| Estourar 10 GB do R2 | Publicação falha | O indexador aborta acima de 8 GB projetados; ícones de perfil (554 MB) são a primeira fatia a sair |
| Remoção do patch anterior apaga cedo demais | Site sem assets | Remoção só após manifesto novo publicado e verificado; teste cobre a ordem |
| Vercel Hobby proíbe uso comercial | Conta suspensa | Não monetizar ([ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md) regra 6) |
| Política da Riot | Take-down | Aviso legal visível, registro no Developer Portal, sem monetização |
| Zip no cliente trava o navegador | Frustração | Limite recomendado de 300 arquivos / 500 MB; empurra para o zip por categoria |
| Wiki sem consentimento | Sem arte acima de 1280×720 | v1 não depende; a UI é honesta sobre o teto ([ADR 0004](adr/0004-consentimento-da-wiki-e-teto-de-resolucao.md)) |
| Tabela de apelidos incompleta | Busca falha para alguém | Correção é uma linha; issue por busca sem resultado |

---

## 13. Decisões em aberto que precisam de você

| # | Decisão | Recomendação | Bloqueia |
|---|---|---|---|
| **D1** | Nome público do produto | Escolher antes do lançamento; não pode conter "Riot", "League of Legends" nem "LoL" | Lançamento |
| **D2** | Consentimento da Weird Gloop | Pedir agora — é o único caminho para arte acima de 1280×720 | Tier HD |
| ~~**D3**~~ | ~~Mover o repositório para caminho ASCII~~ | ✅ **Resolvida em 03/09/2026.** Repositório em `D:\PROJETOS\PROJETO-ASSETS-LOL`; `pnpm install` em exit 0 | — |
| **D4** | Emotes (2.347) e ward skins (265) entram na v1? | Sim, mas **medir os bytes primeiro** — é o único buraco no orçamento do RNF-05 | Fechar o orçamento |
| **D5** | Ícones de perfil (5.021, 554 MB) valem 32 % do armazenamento? | Manter na v1; se apertar, é a primeira fatia a sair | Nada |
| **D6** | Texto exato do aviso legal + registro no Developer Portal | Copiar literalmente da política e registrar antes de divulgar | Lançamento |
| **D7** | Domínio | Só depois de D1 | Lançamento |

---

## 14. Rastreabilidade

| ADR | Onde aparece nesta Spec |
|---|---|
| [0001](adr/0001-formato-de-entrega-dos-assets.md) formato de entrega | RF-10, RF-11, RF-12, §5.3, §6 |
| [0002](adr/0002-nomes-canonicos-de-corte-de-splash.md) nomes canônicos | §6.2, §10, §12 |
| [0003](adr/0003-nome-publico-do-produto.md) nome do produto | RF-23, D1 |
| [0004](adr/0004-consentimento-da-wiki-e-teto-de-resolucao.md) wiki | RNF-09, D2 |
| [0005](adr/0005-arquitetura-estatica-custo-zero.md) estático, custo zero | §1.2, §5, RNF-04 |
| [0006](adr/0006-api-como-componente-opcional.md) API opcional | §5.2, §7 |
| [0007](adr/0007-politica-de-versoes-e-orcamento.md) versões e orçamento | RF-19, RF-20, RNF-05, §8 |
| [0008](adr/0008-catalogo-de-skins-e-seletor.md) catálogo de skins | RF-06 — emendado pelo 0010 |
| [0010](adr/0010-navegacao-por-campeao-busca-por-skin.md) navegação × busca | RF-04, RF-05, RF-24, RF-25, RNF-03, §5.4, §6, §6.1, §8 |
| [0009](adr/0009-apelidos-de-busca-mantidos-a-mao.md) apelidos | RF-03, §6, §10 |
