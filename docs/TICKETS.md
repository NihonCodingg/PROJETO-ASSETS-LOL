# TICKETS v1

> Etapa 5. Quebra de [`SPEC.md`](SPEC.md) em unidades executáveis, uma por sessão.
> Cada ticket cabe em **≤ 500 linhas de lógica** (exclui lockfiles, fixtures e snapshots).
> Se não couber, divide-se o ticket — nunca se infla o PR (regra 5 do [CLAUDE.md](../CLAUDE.md)).
>
> Data: 03/09/2026 · 37 tickets · 7 ondas
>
> **Revisão de 07/09/2026:** o projeto passa a operar **sem storage próprio** —
> [ADR 0012](adr/0012-onde-guardar-os-assets.md). Afeta T-06 (vira componente inativo),
> T-10, T-11, T-12, T-13, T-22, T-23 (suspenso), T-25 e T-26. Nenhum ticket foi apagado.
>
> **Revisão de 03/09/2026:** navegação passa a ser por campeão e busca por skin
> ([ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md)). Afeta T-04, T-07,
> T-08, T-10, T-14, T-19 e T-20. Nenhum ticket foi criado ou removido.

## Como ler

- **Onda** = bloco de execução. Uma onda só começa quando a anterior fecha.
- Dentro da onda, `∥` marca o que pode rodar **em paralelo**; `→` marca dependência.
- **Effort** é o que a sessão que executa o ticket deve declarar.
- **Estimativa** é linha de lógica, não linha de diff.
- Todo ticket herda a Definição de Pronto da §0.4 do KICKOFF: CI verde, sem `TODO` órfão,
  doc atualizada se o comportamento observável mudou, relatório em `docs/sessoes/`.

## Nota sobre os tickets de interface

O desenho da UI está sendo feito em paralelo no Claude Design. Por isso os tickets de
interface especificam **comportamento e critério de aceite**, nunca decisão visual.
Espaçamento, cor, tipografia, grid e ilustração **não** aparecem em critério de aceite —
chegam depois, como referência, em **T-30**. Um ticket de UI está pronto quando o
comportamento passa nos testes, mesmo que a tela ainda esteja crua.

**Base de componentes** ([ADR 0011](adr/0011-base-de-componentes-do-front.md)): shadcn/ui
sobre Radix, TanStack Virtual nas listas grandes e cmdk na paleta de busca — com o filtro
embutido do cmdk **desligado**, porque o algoritmo de busca é o nosso. Fuse.js está fora.
Componente gerado pelo shadcn conta como **scaffold, não como lógica**, para efeito do
limite de 500 linhas.

> ⚠️ **`docs/design/TOKENS.md` ainda não existe.** A ingestão do design não aconteceu —
> nenhum arquivo de tela chegou ao repositório. **T-34** e **T-30** estão bloqueados nisso;
> os demais tickets de UI seguem executáveis, porque não dependem de decisão visual.

---

# Onda 0 — fechar pendências antes de escrever produto

**Execução: T-02 → T-01** (sequencial, não paralelo).

> **Desvio deliberado da ordem sugerida.** T-02 reaproveita
> `prototype/spikes/common.py`, que já tem o cliente HTTP com a etiqueta da regra 4 e a
> trava da wiki — e é exatamente esse diretório que T-01 apaga. Rodar T-01 primeiro
> obrigaria a reescrever o cliente antes de existir o ticket dele (T-03). Invertendo,
> T-02 custa ~120 linhas descartáveis e T-01 leva o resultado junto para a evidência.

### ✅ T-02 — Spike D4: fechar o orçamento de armazenamento

> **Concluído em 03/09/2026** (commit `388ea0a`). Resultado: **2,0 GB**, 20,1 % do tier
> gratuito de 10 GB. A condição de parada **não** foi disparada. Ver a seção S4 de
> [`SPIKES.md`](SPIKES.md).

| | |
|---|---|
| **Objetivo** | Medir os bytes reais de emotes e ward skins, os dois únicos buracos do orçamento do RNF-05, e dizer se o catálogo completo cabe em 10 GB |
| **Dependências** | nenhuma |
| **Estimativa** | ~120 linhas |
| **Effort** | baixo |
| **Cobre** | RNF-05, decisão D4 da §13 da Spec, [ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md) |

**Entra**
- Script em `prototype/spikes/s4_orcamento.py`, no mesmo molde de S1–S3, usando
  `common.py` (User-Agent, concorrência ≤ 4, backoff).
- Medição por amostragem de **emotes** (2.347, `v1/summoner-emotes.json`) e **ward skins**
  (265, `v1/ward-skins.json`): amostra de ≥ 30 de cada, mediana de bytes, dimensão e
  formato, extrapolada para o total.
- Recálculo do orçamento completo de uma versão somando as medições de S1/S3 já existentes.
- Resultado em `prototype/spikes/results/s4-orcamento.json` e uma seção nova em
  `docs/SPIKES.md`.

**NÃO entra**
- Baixar os 2.612 arquivos. Amostra + mediana basta para uma decisão de orçamento.
- Qualquer código de produção. É spike, é descartável.
- Medir categorias já medidas em S1/S3.

**Critérios de aceite**
1. `docs/SPIKES.md` ganha o total projetado da versão completa, em bytes e em % dos 10 GB.
2. O JSON de resultado traz `n`, mediana, mínimo e máximo por categoria.
3. Nenhuma requisição à wiki (a trava de `common.py` continua ativa).
4. **Condição de parada:** se o total projetado passar de **10 GB**, o ticket termina com
   o número na mão e **para**. Nada da Onda 1 começa até o dono do projeto decidir o que
   cortar. A recomendação padrão, se isso acontecer, é remover os ícones de perfil
   (554 MB, 32 % do total, e a categoria que menos serve a um editor).

**Testes que provam**
- Nenhum teste automatizado — é spike. A prova é o número em `docs/SPIKES.md` com o JSON
  bruto versionado ao lado.

---

### ✅ T-01 — Remover o protótipo e preservar a evidência

> **Concluído em 03/09/2026.** As evidências foram para
> [`docs/evidencias/spikes/`](evidencias/spikes/) e o `prototype/` deixou de existir.

| | |
|---|---|
| **Objetivo** | Apagar `prototype/` sem perder as medições que sustentam a Spec |
| **Dependências** | T-02 |
| **Estimativa** | ~30 linhas (configuração) |
| **Effort** | baixo |
| **Cobre** | §A.10 e §0.3 do KICKOFF |

**Entra**
- Mover `prototype/spikes/results/*.json` (incluindo o de T-02) para
  `docs/evidencias/spikes/` e corrigir os links em `docs/SPIKES.md`.
- Apagar `prototype/` inteiro.
- Remover `prototype/*` de `pnpm-workspace.yaml`.
- Remover `prototype` das exclusões de ruff e mypy em `pyproject.toml`.
- Atualizar `CLAUDE.md`, `README.md` e o índice de `docs/` onde citam `prototype/`.

**NÃO entra**
- Aproveitar código do protótipo em `apps/web`. A busca e o painel são reescritos com
  testes em T-14 e T-15. O protótipo foi instrumento de medição, não rascunho de produto.
- Reescrever os relatórios de sessão que citam o protótipo — são registro histórico.

**Critérios de aceite**
1. `prototype/` não existe.
2. `docs/SPIKES.md` aponta para `docs/evidencias/spikes/` e todos os links resolvem.
3. `grep -r "prototype/"` só encontra ocorrências **históricas**: relatórios em
   `docs/sessoes/`, a descrição destes dois tickets, os prompts originais da Parte C do
   KICKOFF e os `git show` que apontam para o código apagado. Nenhuma referência
   operante — nenhum caminho que alguém possa tentar executar hoje.
   *(Critério afrouxado na execução: a redação original — "só em `docs/sessoes/`" — não
   previa que o próprio `TICKETS.md` descreve o trabalho de apagar o `prototype/`.)*
4. `pnpm install`, `uv sync --all-packages` e a suíte inteira continuam verdes.

**Testes que provam**
- CI verde (é o teste: se o workspace ou as exclusões ficarem quebrados, ela falha).
- Teste de link em `docs/` verificando que todo caminho relativo citado existe.

---

# Onda 1 — esqueleto andante

> **Objetivo desta onda é validar a arquitetura inteira, não entregar funcionalidade.**
> Ao fim dela existe: um campeão indexado do ddragon, um índice publicado no R2, e um
> front que carrega esse índice, mostra o asset e baixa o arquivo — original e PNG.
> Um campeão, dois tipos de asset. Nada mais.

**Execução: (T-03 ∥ T-04) → (T-05 ∥ T-06) → T-07**, com **T-08 ∥ tudo** (usa a fixture de T-04).

> ✅ **Onda concluída em 04/09/2026**, um PR por ticket, CI verde antes de cada merge.
> Executada em sequência em vez de em paralelo — uma sessão só, sem ganho em paralelizar.
> **Pendente:** a publicação real no R2, que precisa de credencial. Tudo o mais foi
> verificado ao vivo: a CLI contra o ddragon e o front contra a saída dela.

### ✅ T-03 — Cliente HTTP com a etiqueta de rede

> **Concluído em 04/09/2026** (PR #2).

| | |
|---|---|
| **Objetivo** | Um único lugar por onde toda requisição a fonte externa passa, com a etiqueta da regra 4 imposta por código |
| **Dependências** | nenhuma |
| **Estimativa** | ~150 linhas |
| **Effort** | médio |
| **Cobre** | RNF-08, RNF-09, regras 3 e 4 do CLAUDE.md |

**Entra**
- `packages/indexer/src/lol_assets_indexer/http.py`: cliente `httpx` assíncrono com
  User-Agent `lol-assets-indexer/{versão} (+{repo}; {contato})`, concorrência ≤ 4 por host,
  backoff exponencial com jitter em 429 e 5xx, respeito a `Retry-After`, timeout.
- Trava de host: qualquer URL de `wiki.leagueoflegends.com` levanta exceção enquanto
  `WIKI_CONSENT_GRANTED` for falso.
- Configuração por `pydantic-settings`, lendo as variáveis do `.env.example`.

**NÃO entra**
- Cache em disco. Chega quando um adaptador precisar.
- Qualquer conhecimento sobre ddragon ou cdragon. Este módulo não sabe o que baixa.

**Critérios de aceite**
1. Toda resposta 429 e 5xx é repetida com espera crescente, até `INDEXER_MAX_RETRIES`.
2. `Retry-After` numérico é respeitado quando presente.
3. Nunca mais de `INDEXER_MAX_CONCURRENCY` requisições simultâneas ao mesmo host.
4. URL da wiki levanta exceção com mensagem citando a regra 3.
5. O User-Agent nunca contém dado pessoal: o contato vem de `INDEXER_CONTACT`, cujo padrão
   é a URL de issues do repositório.

**Testes que provam** — `respx`, sem rede
- 429 seguido de 200 → uma repetição, resultado final 200.
- 500 três vezes → backoff crescente medido, exceção depois do limite.
- `Retry-After: 2` → espera ≥ 2 s (relógio fake).
- 12 requisições concorrentes → o pico observado é ≤ 4.
- URL da wiki → `pytest.raises`.
- O header `User-Agent` casa com o formato da regra 4.

---

### ✅ T-04 — Contrato em código: modelos, validação e fixture

> **Concluído em 04/09/2026** (PR #3).

| | |
|---|---|
| **Objetivo** | Transformar o JSON Schema em tipos que o indexador usa e em uma fixture que o front consome, para as duas pontas andarem em paralelo |
| **Dependências** | nenhuma |
| **Estimativa** | ~200 linhas |
| **Effort** | médio |
| **Cobre** | §6 da Spec, [ADR 0001](adr/0001-formato-de-entrega-dos-assets.md), [ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md) |

**Entra**
- Modelos Pydantic v2 em `packages/schema/src/lol_assets_schema/models.py`: `Asset`,
  `IndexShard`, `IndexManifest`, `Catalog`, `CatalogChampion` e `CatalogSkin`, com os
  mesmos enums e as mesmas obrigatoriedades do schema.
- `validate_shard()`, `validate_manifest()` e `validate_catalog()` que validam **contra o
  JSON Schema**, não só contra o Pydantic — o schema continua sendo a fonte de verdade.
- Fixture versionada `packages/schema/examples/`: um `manifest.json`, um
  `catalog-*.json` (com campeões e skins) e uma fatia `index-champion-*.json` com um
  punhado de assets reais (medidos, não inventados).
- Exportar a fixture pelo pacote TS para o front importar nos testes.

**NÃO entra**
- Gerador automático de modelos a partir do schema. Vira ticket quando o schema estabilizar;
  por ora um teste garante que modelo e schema não divergem.
- Modelos para a API. Ela é opcional (T-32).

**Critérios de aceite**
1. Um `Asset` com `hasAlpha=True` e `format="jpeg"` é rejeitado pelas duas validações.
2. Um corte de splash sem `skinId` é rejeitado.
3. As três fixtures validam contra os respectivos JSON Schema.
3b. Uma skin do catálogo sem `championKey` é rejeitada — sem ela não dá para rotular o
   resultado de busca com o campeão ([ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md)).
4. Serializar um modelo e validar contra o schema produz documento válido (ida e volta).
5. Todo campo obrigatório do schema existe no modelo, e vice-versa — teste que compara as
   duas listas e falha quando divergem.

**Testes que provam**
- Positivos e negativos das regras acima, incluindo o par ida/volta.
- Teste de paridade schema × modelo (é o que impede o modelo de envelhecer sozinho).

---

### ✅ T-05 — Adaptador ddragon mínimo: um campeão, dois tipos

> **Concluído em 04/09/2026** (PR #4).

| | |
|---|---|
| **Objetivo** | Provar o caminho fonte → registro de asset com medição real, no menor recorte possível |
| **Dependências** | T-03, T-04 |
| **Estimativa** | ~220 linhas |
| **Effort** | médio |
| **Cobre** | RF-10, RF-13, §5.3 da Spec |

**Entra**
- `adapters/ddragon.py`: descobrir a versão mais recente, ler `champion/{Id}.json` em
  `pt_BR` e `en_US`, e produzir registros de `square` e `splash_centered` para **um**
  campeão passado por parâmetro.
- Medição com Pillow: `width`, `height`, `format`, `hasAlpha`. `sha256` e `bytes` dos
  bytes de origem. **Nada é reencodado.**
- Nome canônico e `fileName` conforme §6.2 da Spec.
- Mapa fonte → canônico isolado: `centered/` → `splash_centered` ([ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md)).

**NÃO entra**
- Tarball (T-09), demais tipos de asset (T-09), demais campeões (T-09).
- cdragon (T-16), fusão (T-17).
- Filtragem de chroma — com um campeão e dois tipos, não aparece.

**Critérios de aceite**
1. Rodando para Jax, produz exatamente 2 registros válidos contra o JSON Schema.
2. `splash_centered` mede **1280×720** e vem de `img/champion/centered/`, não de `splash/`.
3. `square` mede **128×128**, `format="png"`, `hasAlpha=false`.
4. `sha256` bate com o hash dos bytes baixados.
5. `fileName` é `Jax_square.png` e `Jax_000_splash_centered.jpg`.
6. Nenhuma chamada a `Image.save` no módulo — garantia do ADR 0001.

**Testes que provam**
- Unitários com `respx` e imagens de fixture: mapa de nomes, medição, hash, `fileName`.
- Teste que falha se `splash/` for mapeado para `splash_centered` (a inversão do ADR 0002).
- Teste que varre o módulo procurando `Image.save` / `.save(` e falha se achar.

---

### ✅🔌 T-06 — Publicador no R2 com manifesto atômico

> **Concluído em 04/09/2026** (PR #5).
>
> 🔌 **Componente inativo desde 07/09/2026** ([ADR 0012](adr/0012-onde-guardar-os-assets.md)).
> O código **não foi revertido**: `publish/storage.py` e `publish/bucket.py` continuam no
> repositório, com os 17 testes passando na CI. O que mudou é que a CLI não os usa mais para
> publicar assets — o `LocalObjectStore` e a trava de ordem seguem em uso para escrever o
> índice.
>
> **O caminho de volta para a opção A é preencher `storageKey`**: criar o bucket, preencher
> as cinco variáveis já documentadas no `.env.example` e voltar a chamar `publish_asset` no
> `_publish_assets` da CLI. Os bytes já viajam junto do registro desde o T-07
> (`FetchedAsset`), justamente por isso. O front não muda uma linha — `assetUrl()` já
> prefere `storageKey` quando ele existe. Passo a passo completo na §"Como voltar para A"
> do [ADR 0012](adr/0012-onde-guardar-os-assets.md).

| | |
|---|---|
| **Objetivo** | Escrever no bucket na ordem que torna a publicação atômica sem transação |
| **Dependências** | T-04 |
| **Estimativa** | ~200 linhas |
| **Effort** | médio |
| **Cobre** | §5.3 e §9 da Spec, [ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md) |

**Entra**
- `publish/storage.py`: cliente S3 (boto3 ou aiobotocore) contra R2, com endpoint,
  credenciais e bucket vindos do ambiente.
- Upload de asset, de fatia de índice e do manifesto, cada um com o `Cache-Control` da
  §9 da Spec.
- Nome com hash para fatias e zips; `manifest.json` é o único nome fixo.
- **Ordem imposta por código:** manifesto só sobe depois de todas as fatias e assets
  confirmados. Tentar publicar o manifesto antes levanta exceção.
- `--dry-run` que escreve num diretório local em vez do bucket.

**NÃO entra**
- Remoção do patch anterior (T-11). Publicar e remover são responsabilidades separadas
  justamente porque a segunda é destrutiva.
- Geração de zip (T-23).
- Configuração de CDN e de domínio — infra manual, fora de ticket.

**Critérios de aceite**
1. Publicar uma versão completa e depois ler o manifesto devolve exatamente o que foi escrito.
2. Chamar `publish_manifest()` antes de todas as fatias levanta exceção.
3. Fatias e assets sobem com `max-age=31536000, immutable`; o manifesto com `max-age=300`.
4. `--dry-run` não faz nenhuma chamada de rede e produz a mesma árvore em disco.
5. Nenhuma credencial aparece em log.

**Testes que provam**
- `moto` (ou stub de S3) para o caminho feliz e para a ordem.
- Teste da exceção de ordem.
- Teste dos headers de cache por tipo de objeto.
- Teste que roda `--dry-run` e compara a árvore gerada com um snapshot.

---

### ✅ T-07 — CLI do indexador ligando as pontas

> **Concluído em 04/09/2026** (PR #6).

| | |
|---|---|
| **Objetivo** | Um comando que faz o caminho inteiro e é o que o Actions vai chamar |
| **Dependências** | T-05, T-06 |
| **Estimativa** | ~180 linhas |
| **Effort** | médio |
| **Cobre** | §5.3 e §6.1 da Spec, [ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md) |

**Entra**
- `lol-assets-indexer index --champion Jax [--game-version X] [--dry-run]`: descobre a
  versão, roda o adaptador, projeta o **catálogo** (um campeão e as skins dele), valida
  tudo contra o schema, publica.
- A projeção do catálogo vive num módulo próprio, para T-10 escalá-la sem reescrever.
- Falha ruidosa: qualquer registro inválido aborta **antes** de publicar qualquer coisa.
- Log estruturado em JSON por linha, com `gameVersion` e `source` em todo evento.
- Código de saída ≠ 0 em qualquer falha.

**NÃO entra**
- Agendamento (T-13), `status.json` (T-12), rotação de versão (T-11).
- Catálogo completo (T-09).

**Critérios de aceite**
1. `--dry-run` produz a árvore local completa — manifesto, catálogo e fatia — e sai com 0.
1b. O catálogo publicado tem 1 campeão em `champions[]` e as skins dele em `skins[]`, com
   `skinCount` conferindo.
2. Um asset inválido injetado aborta com saída ≠ 0 e **nada** é publicado.
3. O log tem uma linha JSON por evento, com `gameVersion` presente.
4. `--help` descreve todas as opções em português.

**Testes que provam**
- `CliRunner` com adaptador e publicador falsos: caminho feliz, caminho de validação
  falhando, verificação de que o publicador não foi chamado nesse caso.

---

### ✅ T-08 — Front: carregar o índice, listar e baixar um asset

> **Concluído em 04/09/2026** (PR #7).

| | |
|---|---|
| **Objetivo** | Provar o outro lado do esqueleto: manifesto → fatia → tela → arquivo no disco, com PNG convertido no navegador |
| **Dependências** | T-04 (fixture) |
| **Estimativa** | ~250 linhas |
| **Effort** | alto |
| **Cobre** | RF-09, RF-10, RF-11, RF-12, RF-13, RNF-07, [ADR 0001](adr/0001-formato-de-entrega-dos-assets.md) |

**Entra**
- Carregar `manifest.json`, escolher `currentVersion`, carregar o **catálogo**.
- Desenhar a grade a partir de `catalog.champions[]` (nível de navegação).
- Ao abrir um campeão, carregar a fatia `champion` **sob demanda**, uma única vez, e
  mostrar os assets.
- Exibir formato, resolução, tamanho e fonte **antes** de qualquer download.
- "Baixar original" (bytes de origem) e "Baixar PNG" (canvas no clique). Asset de origem
  PNG mostra o botão desabilitado.
- Resolver a URL: `storageKey` quando existe, `sourceUrl` quando não.
- Módulo de download testável, separado do componente.

**NÃO entra**
- Busca (T-14), catálogo de skins (T-19), filtros (T-24), lote (T-25).
- Qualquer decisão visual — ver a nota no topo. Tela crua é aceitável.

**Critérios de aceite**
1. Com a fixture servida, a grade renderiza a partir do catálogo, sem erro e sem tocar
   ddragon ou cdragon.
1b. A fatia de assets **não** é buscada no carregamento da página; só ao abrir o primeiro
   campeão, e só uma vez ([ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md)).
2. A ficha mostra os quatro dados antes do primeiro clique de download.
3. O arquivo baixado como original tem `sha256` igual ao do índice.
4. O PNG convertido tem as mesmas dimensões e MIME `image/png`.
5. Asset com `format: "png"` não oferece conversão.
6. Asset sem `storageKey` usa `sourceUrl` e funciona igual.
7. O nome do arquivo salvo é o `fileName` do índice.

**Testes que provam**
- Vitest no módulo de download: resolução de URL, nome do arquivo, conversão canvas→PNG
  com blob de fixture, caminho do "já é PNG".
- Teste de que nenhum host externo é chamado no carregamento.
- Teste de rede que conta as requisições: catálogo na abertura, fatia só depois do primeiro
  clique em campeão, e não mais de uma vez.

---

# Onda 2 — catálogo de campeões completo

**Execução: T-09 → (T-10 ∥ T-11 ∥ T-12) → T-13**, com **(T-14 ∥ T-15)** em paralelo a tudo.

### ✅ T-09 — Adaptador ddragon completo pelo tarball

> **Concluído em 07/09/2026.** Três desvios do escopo escrito, todos por causa do
> [ADR 0012](adr/0012-onde-guardar-os-assets.md):
>
> 1. **`--champion` morreu.** O tarball traz o patch inteiro; indexar um campeão só
>    deixou de fazer sentido. O que sobrou de recorte é `--game-version`.
> 2. **`--dry-run` mudou de sentido.** Era "escreve local em vez do bucket"; sem
>    bucket, virou "mede e valida sem escrever nada".
> 3. **O adaptador mínimo do T-05 foi removido**, não deixado ao lado. Ele montava
>    `storageKey`, o que contradiz o ADR 0012 na primeira vez que alguém o chamasse.
>    Sobraram dele a descoberta de versão, a URL do tarball e as formas normalizadas.
>
> Ganhou `--tarball`, que reaproveita um arquivo já baixado — 2,39 GB por execução de
> teste era caro demais para verificar o resto.
>
> **Rodou contra o patch 16.17.1 de verdade** e os totais batem com o S1: 173 squares,
> 2.118 de cada corte de splash, 868 itens, 726 feitiços. A execução real achou três
> defeitos que a fixture não tinha — nome em branco no ddragon, `Fiddlesticks` contra
> `FiddleSticks` e stat mods fora do índice — todos corrigidos aqui. Medição em
> [`docs/evidencias/t09-indexacao-real.json`](evidencias/t09-indexacao-real.json).

| | |
|---|---|
| **Objetivo** | Trocar as requisições avulsas por uma única, e cobrir todos os tipos do ddragon que estão no escopo |
| **Dependências** | T-05 |
| **Estimativa** | ~350 linhas |
| **Effort** | alto |
| **Cobre** | §5.3 da Spec, [ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md) |

**Entra**
- Baixar `dragontail-{versão}.tgz` (2,39 GB) em streaming e percorrer em uma passada.
- Extrair só `data/{pt_BR,en_US}` e os `img/` do escopo; **descartar** TFT, challenges,
  missões, sprites e modo Classic (44 % do peso, medido em S1).
- Produzir todos os tipos do ddragon: `square`, `splash_centered`, `splash_wide`,
  `loading`, `tile`, `item_icon`, `summoner_spell_icon`, `ability_icon`, `passive_icon`,
  `profile_icon`, `rune_icon`, `map_image`.
- Filtrar chroma pela presença de `parentSkin` antes de montar URL de splash.
- `names` em `pt_BR` e `en_US`; `tags` de função, lane, comprável e mapa.

**NÃO entra**
- cdragon (T-16). Emotes, wards e ranks (T-22) — não vêm do tarball.
- Fatiamento e orçamento (T-10).

**Critérios de aceite**
1. Uma passada pelo tarball; nada é extraído duas vezes.
2. Nenhum registro produzido para caminho de TFT, challenges, missão, sprite ou Classic.
3. Entrada com `parentSkin` não gera registro de splash.
4. Os totais batem com S1: 173 squares, 2.118 splashes por tipo, 868 itens, 726 feitiços.
5. Todos os registros validam contra o JSON Schema.
6. Pico de memória compatível com o runner do Actions (streaming, não carregar tudo).

**Testes que provam**
- Tarball de fixture pequeno, montado no teste, com um caso de cada tipo, um chroma e um
  caminho fora de escopo.
- Teste dos totais contra um manifesto de contagens esperadas.
- Teste do filtro de escopo com uma tabela de caminhos dentro/fora.

---

### ✅ T-10 — Fatiamento do índice e guarda de orçamento

> **Concluído em 07/09/2026.** O fatiamento e a projeção completa já tinham vindo no
> T-09; o que este ticket entregou foram as **guardas** e um pedaço que o escopo escrito
> não previa.
>
> - **Limites em KiB, não em KB.** 150 KiB, 1,5 MiB e 15 MiB. O texto dizia "KB"; a
>   diferença é de 2,4 % e nenhuma decisão depende dela, mas o código precisava escolher.
> - **A guarda mede os bytes que iriam para o disco**, não uma serialização parecida.
>   Para isso a serialização foi separada da escrita (`prepare_catalog`, `prepare_shard`,
>   `prepare_manifest`), e o manifesto entra na conta — ele referencia os hashes, então
>   só existe depois dos outros dois.
> - **Guarda de forma do catálogo**, além da de tamanho. O critério 1b pedia
>   `skinCount` batendo com `skins[]`; virou `verify_catalog`, que também confere
>   `skinId = championKey × 1000 + skinNum`, uma base por campeão e nenhuma skin órfã.
>   São invariantes do ADR 0010 que o JSON Schema não alcança e que quebram em silêncio.
> - **O `--dry-run` também aplica a guarda**, senão o ensaio passaria e o build de
>   verdade falharia.
>
> Medido no patch 16.17.1: catálogo 63.293 gzip (42 % do limite), maior fatia 717.050
> gzip (46 %), índice inteiro 10.583.827 escritos (67 %).

| | |
|---|---|
| **Objetivo** | Projetar o catálogo completo e manter a carga inicial enxuta |
| **Dependências** | T-09 |
| **Estimativa** | ~280 linhas |
| **Effort** | médio |
| **Cobre** | RNF-03, RNF-05, §6.1 da Spec, [ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md) |

**Entra**
- Escalar a projeção do catálogo de T-07 para o catálogo inteiro: **173 campeões** em
  `champions[]` (com `skinCount`, `chromaCount`, `baseSkinId` e miniatura) e **2.118 skins**
  em `skins[]`.
- Fatiar o índice de assets por categoria, com hash no nome.
- Calcular o tamanho comprimido e **falhar** se o catálogo passar de **150 KB** ou se a
  fatia `champion` passar de 1,5 MB (RNF-03).
- **Guarda de tamanho do índice** — substitui a guarda de orçamento de 10 GB, que morreu
  com o [ADR 0012](adr/0012-onde-guardar-os-assets.md): abortar se o índice de uma versão
  passar de **15 MB**, porque agora ele é versionado no repositório.
- Preencher `shards[]` e os totais do manifesto.

**NÃO entra**
- Compressão própria. Quem comprime é o CDN; a medição usa gzip só para conferir o limite.
- Decidir o que cortar quando estourar — é decisão humana, o indexador só para.

**Critérios de aceite**
1. Uma fatia por categoria presente, cada uma com `sha256` e contagem corretos.
1b. O catálogo tem exatamente uma entrada por campeão e uma por skin; `skinCount` de cada
   campeão bate com a contagem em `skins[]`; nenhum chroma aparece em nenhum dos dois.
2. Catálogo acima de 150 KB ou fatia `champion` acima de 1,5 MB comprimida → build falha
   com mensagem clara.
3. Índice de uma versão acima de 15 MB → aborta **antes** de escrever qualquer arquivo.
4. O manifesto lista o catálogo e todas as fatias, e os totais batem com a soma delas.

**Testes que provam**
- Unitários com índices sintéticos nos dois lados de cada limite.
- Teste de que nada é escrito quando o limite estoura.

---

### ✅ T-11 — Rotação: uma versão por vez no índice

> **Reescrito e concluído em 08/09/2026.** O ticket mudou de nome porque mudou de objetivo,
> duas vezes:
>
> 1. Nasceu como "publicar novo, remover anterior" — remoção de **assets** do bucket.
> 2. Virou "reduzir a versão anterior aos tipos versionados" quando o
>    [ADR 0012](adr/0012-onde-guardar-os-assets.md) tirou o bucket.
> 3. Virou **rotação simples** quando a execução mediu o custo do histórico: **4,4 MB por
>    patch, ~115 MB/ano**, num repositório que todo `git clone` paga inteiro — e o que se
>    comprava com isso eram ícones repetidos, porque splash, loading, tile e a categoria
>    `rune` inteira não são versionados. Decidido no
>    [ADR 0013](adr/0013-uma-versao-por-vez-no-indice.md).
>
> A redução ao histórico chegou a ser escrita e testada; foi descartada **antes de
> entrar**, e a regra inteira está escrita no ADR 0013 — mais durável que um ponteiro para
> um commit.

| | |
|---|---|
| **Objetivo** | O índice guarda a versão corrente e só ela, sem deixar rastro da anterior |
| **Dependências** | T-10 |
| **Estimativa** | ~60 linhas |
| **Effort** | baixo |
| **Cobre** | RNF-05, [ADR 0013](adr/0013-uma-versao-por-vez-no-indice.md), [ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md) |

**Entra**
- `versions[]` do manifesto tem **exatamente um item**, sempre igual a `currentVersion`.
- **Varredura de órfãos**: depois de o manifesto novo estar escrito, todo documento de
  índice que ele não referencia mais é apagado do destino. É o que faz a versão anterior
  desaparecer, e o que impede uma reindexação do mesmo patch de deixar lixo.
- `assetsCopied` permanece `false`.

**NÃO entra**
- Guardar versão anterior, reduzida ou não ([ADR 0013](adr/0013-uma-versao-por-vez-no-indice.md)).
- Apagar qualquer coisa **antes** do manifesto novo. É a trava do
  [ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md) para passo destrutivo.
- Encolher o histórico do **Git**. Cada indexação continua deixando ~10,6 MB de blobs para
  sempre — problema separado, no **T-37**.

**Critérios de aceite**
1. Depois de indexar dois patches em sequência, o manifesto traz uma versão só.
2. Nenhum documento da versão anterior sobra no destino.
3. Indexar N patches no mesmo destino deixa o diretório do mesmo tamanho que indexar um.
4. Se a escrita do manifesto falhar, nada foi apagado — a versão anterior continua inteira.
5. A varredura não toca em `manifest.json` nem em arquivo fora do padrão de nome do índice.

**Testes que provam**
- Dois patches em sequência, conferindo o manifesto e o conteúdo do diretório.
- Três patches, comparando o tamanho do diretório com o do primeiro.
- Falha injetada na publicação do manifesto, conferindo que nada sumiu.
- Arquivo intruso no destino, conferindo que sobrevive.

---

### ✅ T-12 — Observabilidade: `status.json`, resumo do job e issue automática

> **Concluído em 08/09/2026.** Três decisões que o escopo escrito não tomava:
>
> - **A issue é aberta em Python, não em YAML.** O critério pedia teste de
>   idempotência, e passo de workflow não se testa sem `act`. Com a chamada em
>   Python, a idempotência, a redação e o comportamento quando a API está fora do ar
>   viram teste com `respx`. O T-13 só precisa passar `GITHUB_TOKEN`.
> - **A idempotência é por `GITHUB_RUN_ID` carimbado no corpo**, num comentário HTML
>   invisível no Markdown — não por título parecido. Título muda quando o texto do
>   erro muda; o `run_id` não.
> - **`--dry-run` não escreve nem o `status.json`.** "Mede e valida sem escrever
>   nada" é uma regra só, e uma regra só é mais fácil de lembrar do que uma com
>   exceção.
>
> **Fora do escopo escrito, mas dentro do objetivo:** o detector de **dimensão
> inesperada**. O ticket pedia "dimensões inesperadas" no `status.json` sem dizer o
> que era esperado; virou uma tabela com as medidas do S1 e um agrupamento por
> (tipo, tamanho encontrado) — uma linha por desvio, não uma por asset, senão 2.118
> splashes com tamanho novo produziriam 2.118 linhas.
>
> A promessa do T-10 de "aborta sem escrever nada" passou a significar **nenhum
> documento de índice**: o relatório da falha é escrito de propósito.

| | |
|---|---|
| **Objetivo** | Fazer a indexação falhar alto, já que não há processo para monitorar |
| **Dependências** | T-07 |
| **Estimativa** | ~180 linhas |
| **Effort** | médio |
| **Cobre** | §11 da Spec, RNF-06 |

**Entra**
- `status.json` **versionado junto com o índice** a cada execução: versão, duração, assets
  por fonte, bytes medidos, falhas por tipo, dimensões inesperadas.
- Como não há bucket ([ADR 0012](adr/0012-onde-guardar-os-assets.md)), ele vai para o mesmo
  destino do índice e é servido pelo app.
- Resumo no `$GITHUB_STEP_SUMMARY` com a mesma tabela.
- Abertura automática de issue em falha, com o log anexado e rótulo `indexacao`.
- Log estruturado JSON consolidado.

**NÃO entra**
- Métrica de tráfego do site. Não há servidor e não vamos instrumentar o navegador.
- Serviço externo de alerta. Issue no repositório é o canal.

**Critérios de aceite**
1. `status.json` valida contra um schema próprio e é escrito mesmo quando a indexação falha.
2. O resumo do job aparece na aba do Actions sem precisar abrir o log.
3. Falha simulada abre exatamente uma issue, sem duplicar em reexecução do mesmo commit.
4. Nenhum segredo aparece no log nem na issue.

**Testes que provam**
- Unitários da montagem do `status.json` e do markdown do resumo.
- Teste de idempotência da abertura de issue (mesmo `run_id` não duplica).
- Teste de redação de segredo: variáveis sensíveis nunca são serializadas.

---

### ✅ T-13 — Workflow agendado de indexação

> **Concluído em 08/09/2026, com um critério que não depende de mim.**
>
> - **O comparador de versão virou um subcomando, `check`.** Ele consulta só o
>   `versions.json` (alguns KB) e compara com o manifesto publicado; o passo de
>   indexação só roda se ele disser que sim. Em ~27 de cada 28 execuções o job
>   termina em segundos, sem tocar nos 2,39 GB.
> - **A regra é "diferente", não "mais novo".** Se o ddragon voltar atrás num patch,
>   o índice volta junto: ele descreve o que a fonte serve **hoje**. Comparar por
>   ordem deixaria o site apontando para arquivos que a fonte não tem mais.
> - **Manifesto ilegível conta como ausente.** Melhor reindexar por causa de um
>   arquivo corrompido do que ficar parado achando que está tudo certo.
> - **`git status --porcelain`, não `git diff`**, para decidir se há o que commitar:
>   na primeira execução os arquivos ainda não são rastreados, e `diff` não vê
>   arquivo novo. Seria uma falha silenciosa exatamente na estreia.
>
> **O critério 4 fica em aberto, e não por falta de código.** "Uma execução manual
> commita e, depois do deploy, o site serve a versão nova" precisa de duas coisas que
> não estão nas minhas mãos: alguém disparar o `workflow_dispatch` e o projeto estar
> ligado à Vercel. A primeira execução também põe **10,6 MB no repositório**, que é
> exatamente a pergunta do **T-37** — disparar sozinho seria decidi-la em silêncio.

| | |
|---|---|
| **Objetivo** | Refletir patch novo em até 24 h sem ninguém apertar nada |
| **Dependências** | T-07, T-11, T-12 |
| **Estimativa** | ~80 linhas (YAML) |
| **Effort** | baixo |
| **Cobre** | RNF-06, RNF-04 |

**Entra**
- `.github/workflows/index.yml`: agendado a cada 6 h e por `workflow_dispatch`.
- Detectar versão nova comparando com o manifesto publicado; sair cedo se não houver.
- **Publicar por commit**, não por API de bucket ([ADR 0012](adr/0012-onde-guardar-os-assets.md)):
  o job escreve o índice, commita e dá push; o deploy da Vercel publica. **Nenhum segredo
  de storage é necessário** — só o `GITHUB_TOKEN` que o Actions já fornece.
- `concurrency` para nunca ter duas indexações ao mesmo tempo.
- `timeout-minutes` compatível com o download de 2,39 GB.

**NÃO entra**
- Deploy do front. É a Vercel que faz, no push.
- Reindexar versões antigas. Um caminho manual basta.

**Critérios de aceite**
1. Sem versão nova, o job sai em menos de 1 minuto e não publica nada.
2. Duas execuções simultâneas não acontecem (`concurrency` prova).
3. O commit do índice é atômico: ou entra inteiro, ou não entra.
4. Uma execução manual commita e, depois do deploy, o site serve a versão nova.

**Testes que provam**
- `act` ou execução real em branch com bucket de teste.
- Teste unitário do comparador de versão (o que decide sair cedo).

---

### ✅ T-34 — Base de componentes e tokens do design

| | |
|---|---|
| **Objetivo** | Instalar a base do [ADR 0011](adr/0011-base-de-componentes-do-front.md) e traduzir os tokens do design para o Tailwind, uma vez, num lugar só |
| **Dependências** | T-08 · **e a ingestão do design** (`docs/design/TOKENS.md`) |
| **Estimativa** | ~150 linhas de lógica (+ scaffold do shadcn, que não conta) |
| **Effort** | médio |
| **Cobre** | RNF-11, [ADR 0011](adr/0011-base-de-componentes-do-front.md) |

> ✅ **Entregue em 10/09/2026**, com o design em `docs/design/telas/` e o
> [TOKENS.md](design/TOKENS.md) escrito **por leitura** do arquivo — 22 cores, 6 raios, 11
> alturas de controle e 7 tamanhos de texto, nenhum estimado.

**Entra**
- `shadcn/ui` inicializado sobre Radix, com os componentes efetivamente usados copiados
  para `apps/web/src/components/ui/`.
- `@tanstack/react-virtual` e `cmdk` no `package.json`, com o filtro do cmdk desligado por
  configuração no ponto de uso.
- Tokens de `docs/design/TOKENS.md` traduzidos para o tema do Tailwind: escala de cinzas,
  cor de destaque única, escala de espaçamento, raio de borda, escala tipográfica, fonte de
  interface e fonte mono dos metadados técnicos.
- Verificação de contraste dos pares de token que o design usa.

**NÃO entra**
- Aplicar os tokens nas telas. Isso é **T-30**, e o critério de aceite dele é a suíte
  inteira continuar passando.
- Fuse.js. Está fora por ADR.
- Qualquer componente que nenhum ticket use ainda.

**Critérios de aceite**
1. ✅ Os tokens do Tailwind batem, valor a valor, com `docs/design/TOKENS.md` — o teste lê
   os dois arquivos e compara **nos dois sentidos**: token no tema que não está no documento
   é token não documentado; token no documento que não está no tema é decisão de design que
   ninguém implementou.
2. ✅ Nenhuma **cor** literal fora do tema; o lint falha se aparecer. *Escopo ajustado —
   ver a nota abaixo.*
3. ✅ Existe **uma** cor de destaque. O teste compara matiz: os três tons de violeta ficam
   dentro de 10°, e nenhuma outra cor do tema passa de 0,2 de saturação.
4. ✅ Os pares de texto × fundo passam em AA — **depois de clarear dois cinzas do design**,
   que reprovavam. Ver a decisão de 10/09.
5. ✅ `cmdk` não filtra: consulta que não casa com nada devolve a lista inteira.

**Testes que provam**
- Teste de paridade tokens × tema do Tailwind (12 casos).
- Teste de contraste dos pares, com a fórmula da WCAG escrita no teste.
- Teste do cmdk com filtro desligado, mais a asserção de que a paleta do produto passa
  `shouldFilter={false}`.
- 17 testes dos primitivos; o axe cobre os componentes montados nas telas (T-28).

> **Três decisões, todas levadas ao dono antes de executar:**
>
> - **Contraste.** `#71717a` (4,12:1) e `#52525b` (2,57:1) reprovam em AA nos tamanhos em
>   que o design os usa (9–11px). Não era gosto: a suíte de axe do T-28 roda `color-contrast`
>   como *serious*, então aplicá-los deixaria a CI vermelha. **Decidido: clarear** — metadado
>   e contagem passam a `#a1a1aa` (6,91:1). Os dois continuam no tema, e o teste garante que
>   não virem `color`.
> - **ADR 0002.** O mock rotulava 1280×720 como "corte do cliente" e 1215×717 como "corte
>   centralizado" — o inverso do contrato medido. **Decidido: corrigir o mapeamento**,
>   mantendo as palavras do design.
> - **Rodapé legal** (RF-21). O layout do design é `100vh` sem rodapé. **Decidido: no pé da
>   barra lateral**, onde ficam as contagens.
>
> **Escopo do critério 2, ajustado com justificativa:** a regra de lint cobre **cor**, não
> espaçamento nem raio. O Tailwind v4 já expressa a escala inteira do design sem valor
> arbitrário (`px-2.5` são 10px, `p-1.25` são 5px), e uma regra que também proibisse
> `[Npx]` pegaria `top-[3px]` de posicionamento — ruído sem ganho. O que quebra um sistema de
> design duplicado é a cor, e é a cor que a regra proíbe. Provado com um arquivo de exemplo:
> a regra acusa `#8b5cf6` fora do tema.
>
> **shadcn/ui:** inicializado (`components.json`, `cn` em `src/lib/utils.ts`) com **um**
> componente sobre Radix — o `PainelLateral`, sobre `Dialog`. É o único primitivo que
> justifica a dependência, e justifica bem: diálogo modal escrito à mão erra sempre nas
> mesmas três coisas — foco que não fica preso, fundo que continua rolando, leitor de tela
> que continua lendo a página de baixo. Os outros primitivos (botão, campo, tecla, rótulos)
> são código nosso sobre os tokens, porque não têm comportamento a acertar.

---

### ✅ T-14 — Front: busca com normalização e apelidos

> **Concluído em 08/09/2026.** Duas decisões que o escopo escrito deixava em aberto:
>
> - **A supressão é por campeão, não por contagem.** O critério dizia "`jax` retorna
>   uma entrada de campeão, não 18 de skin", sem dizer como. A regra que ficou: se o
>   campeão casou, as skins **dele** saem do resultado — elas moram no painel dele
>   ([ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md)). Isso é o que faz
>   `jax` devolver uma entrada mesmo com "O Super Jax" e "Jax Deus da Guerra"
>   casando por substring, e ao mesmo tempo deixa `kda` devolver skins de campeões
>   diferentes: nenhum campeão se chama "K/DA".
> - **Apelido ganha de tudo, inclusive de prefixo.** `eve` é prefixo de "Evelynn" e
>   também apelido dela; se um dia um campeão novo começar com "eve", o apelido
>   continua mandando. Apelido é intenção declarada à mão.
>
> **Verificado no navegador, contra o catálogo real** (173 campeões, 2.118 skins):
> `kaisa`, `mf`, `j4`, `asol` em primeiro lugar; `jax` com **uma** entrada; `kda` com
> 21 skins de vários campeões; `prestigio` com o teto de 50. A busca responde em
> **5 ms** para seis consultas sobre 2.291 entradas — o RNF-01 pede menos de 50 ms
> por consulta.
>
> O `cmdk` entrou como dependência aqui, e não no T-34: ele é headless, e instalar
> não é decisão visual. O tema continua bloqueado com o resto do design.

| | |
|---|---|
| **Objetivo** | Fazer a busca acertar em primeiro lugar sem depender de busca inteligente, operando no nível de skin sem inundar o resultado com skins do mesmo campeão |
| **Dependências** | T-08 |
| **Estimativa** | ~260 linhas |
| **Effort** | médio |
| **Cobre** | RF-01, RF-02, RF-03, RF-05, RF-07, RF-24, RNF-01, [ADR 0009](adr/0009-apelidos-de-busca-mantidos-a-mao.md), [ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md) |

**Entra**
- Normalização: NFD, remover diacríticos, minúsculas, remover não-alfanuméricos.
- Importar `champion-aliases.json` de `packages/schema` **em tempo de build**.
- Paleta de busca com **cmdk**, pela lista acessível e pela navegação por teclado, com o
  **filtro embutido desligado** ([ADR 0011](adr/0011-base-de-componentes-do-front.md)).
- Índice de busca sobre **`catalog.skins[]` (2.118) e `catalog.champions[]` (173)**,
  montado uma vez, na carga do catálogo.
- **Duas classes de resultado.** Campeão casado vira **uma** entrada de campeão, nunca 18
  de skin. Skin casada vira entrada de skin, rotulada com o campeão de origem.
- Ranqueamento: casamento exato de campeão > casamento exato de skin > prefixo > substring.
- Foco automático no campo e atalho `/` sem inserir o caractere.

**NÃO entra**
- Fuse.js. Está **fora por ADR 0011**; se um dia aparecer caso real de zero resultado que a
  normalização não resolva, vira ticket próprio com o caso em mãos.
- O filtro do cmdk. Deixá-lo ligado quebraria `mf`, `j4` e `kda` em silêncio.
- Busca por tag ou filtro (T-24).
- Decisão visual — ver a nota no topo.

**Critérios de aceite**
1. `kaisa`→Kai'Sa, `belveth`→Bel'Veth, `chogath`→Cho'Gath, `KAI'SA`→Kai'Sa, em 1º lugar.
2. `mf`, `tf`, `j4`, `asol` resolvem pelo arquivo de apelidos, em 1º lugar.
2b. `jax` retorna **uma** entrada de campeão, não 18 de skin (RF-05).
2c. `kda` e `prestigio` retornam skins de **≥ 3 campeões distintos**, cada uma rotulada com
   o campeão de origem (RF-24).
3. `/` foca o campo e o valor não muda.
4. Com 173 campeões e 2.118 skins no índice, a busca responde em < 50 ms (medido).
5. Acrescentar uma linha ao JSON de apelidos passa a valer sem tocar em código.
6. O filtro do cmdk está desligado: uma consulta que não casa nada devolve a lista inteira
   do componente, e quem reduz é o nosso ranqueamento.

**Testes que provam**
- Vitest com tabela de ≥ 20 pares consulta→esperado, incluindo os quatro apelidos citados,
  o caso `jax` (uma entrada) e os casos transversais `kda` e `prestigio`.
- Teste de performance com o catálogo completo sintético (173 + 2.118).
- Teste que adiciona um apelido à fixture e confirma que passa a resolver.
- Teste que falha se o filtro do cmdk voltar a ser aplicado (a armadilha silenciosa do
  ADR 0011).

---

### ✅ T-15 — Front: painel de asset completo

> **Concluído em 08/09/2026.**
>
> - **Estado por cartão, não por painel.** São 58 cartões no Fiddlesticks; um erro de
>   rede num deles não pode apagar os outros 57 da tela. Cada cartão tem o seu
>   `pronto | baixando | erro`.
> - **A ordem é por tipo, e a tabela vive num lugar só.** `splash_centered` primeiro
>   ([ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md)), depois do maior para
>   o menor, terminando nos ícones. Tipo desconhecido vai para o fim em vez de sumir.
> - **Baixar e copiar entram por injeção**, com o comportamento real como padrão —
>   mesmo desenho do `PngDeps` do `asset-file.ts`. É o que torna o caminho de erro
>   testável sem mock de módulo.
>
> **Infraestrutura de teste que faltava:** `jsdom` e `@testing-library/react`. Sem DOM
> não dava para provar "o erro fica no cartão" nem "`Esc` fecha" — só varredura de
> fonte, que é fraca para comportamento. O `vitest.config.ts` também passou a resolver
> o alias `@/` e a transformar JSX, que o Next fazia sozinho. Isso destrava os testes
> de componente do T-19, T-20, T-24 e T-25.
>
> **Verificado no navegador, com o índice real:** painel do Fiddlesticks com 58
> cartões, ordem `splash_centered → splash_wide → loading → tile → square →
> passive_icon → ability_icon`, ficha `1280x720 · jpeg · 90 KB · ddragon` **antes** de
> qualquer clique, `Esc` fechando, e a URL copiada respondendo 200 com o `sha256`
> batendo com o do índice.
>
> **Fica uma consequência de o T-19 ainda não existir:** sem seletor de skin, o painel
> de um campeão mostra os assets de **todas** as skins dele — 13 splashes seguidas, no
> caso do Fiddlesticks. Agrupar por tipo é o que mantém isso legível até lá.

| | |
|---|---|
| **Objetivo** | Dar ao usuário todos os tipos de um asset, com ficha honesta e as duas formas de baixar |
| **Dependências** | T-08 |
| **Estimativa** | ~250 linhas |
| **Effort** | médio |
| **Cobre** | RF-09, RF-12, RF-13, RF-14 |

**Entra**
- Painel com todos os tipos disponíveis do item selecionado, cada um com ficha
  (formato, resolução, bytes, fonte) e os botões original / PNG / copiar URL.
- `splash_centered` primeiro, por ser o maior ([ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md)).
- Fechar com `Esc`.
- Estado de carregando e de erro por asset, sem derrubar o painel inteiro.

**NÃO entra**
- Seletor de skin (T-19), chromas (T-20), seleção múltipla (T-25).
- Decisão visual — ver a nota no topo.

**Critérios de aceite**
1. Todos os tipos presentes no índice aparecem; nenhum tipo ausente é inventado.
2. `splash_centered` é o primeiro da lista.
3. Copiar URL põe no clipboard uma URL que responde 200.
4. Um asset que falha ao carregar mostra o erro e não afeta os outros.
5. `Esc` fecha.

**Testes que provam**
- Vitest com fixture cobrindo ordem, ficha, clipboard e o caminho de erro.
- Teste de que um tipo ausente no índice não renderiza card.

---

# Onda 3 — skins, chromas e a segunda fonte

**Execução: (T-16 → T-17) ∥ (T-19 → T-20)**, com **T-18** ao final.

### ✅ T-16 — Adaptador cdragon

> **Concluído em 09/09/2026.** A regra "todo caminho vem do JSON" virou três travas: o
> `asset_url` devolve `None` para prefixo que não casa, uma varredura de fonte falha se
> alguém escrever f-string com extensão de imagem, e um teste confere que **todo** caminho
> registrado existe literalmente no documento.
>
> **Decisão que o ticket não tomava:** `skins[].chromaPath` — a amostra "cor original" que
> o cliente mostra ao lado das chromas — entra como `chroma` com `parentSkinNum` igual ao
> **próprio** `skinNum`. É imagem distinta (24007.png ≠ 24009.png) e é o que a torna
> reconhecível. Já `chromas[].tilePath` **não** entra: medido em 26 de 26 chromas do Jax,
> é o mesmo arquivo do `chromaPath`, e registrar os dois duplicaria o índice.
>
> **Não mapeável virou varredura do documento inteiro**, não só dos campos que o adaptador
> usa. O objetivo do critério 4 é que uma mudança de formato do cliente **apareça**, e ela
> apareceria justamente num campo que ninguém está lendo ainda.

| | |
|---|---|
| **Objetivo** | Cobrir o que o ddragon não tem: chromas e loading vintage |
| **Dependências** | T-03, T-04 |
| **Estimativa** | ~300 linhas |
| **Effort** | alto |
| **Cobre** | §5.3 da Spec |

**Entra**
- Partir de `v1/champions/{key}.json` e **só** dos caminhos que o JSON declara.
- Regra de mapeamento `/lol-game-data/assets/<Path>` → `<game-data>/<path minúsculo>`.
- Tipos: `chroma`, `loading_vintage`, e os demais como candidatos de fusão.
- Concorrência ≤ 4, herdada de T-03.

**NÃO entra**
- Montar caminho à mão. Está medido que os três caminhos de §B.2.3 dão **404 em 162 de
  162** tentativas.
- Baixar `game/` inteiro. Só os diretórios que o JSON aponta.
- Emotes, wards e ranks (T-22).

**Critérios de aceite**
1. Nenhum caminho é construído por template; todos vêm do JSON.
2. Chromas ficam com `parentSkinNum` preenchido.
3. `loading_vintage` só aparece nas skins que têm o campo.
4. Um caminho que não casa com o prefixo `/lol-game-data/assets/` é registrado como não
   mapeável, não silenciosamente descartado.
5. Todos os registros validam contra o JSON Schema.

**Testes que provam**
- `respx` com o JSON real de Jax, Lux e Nunu como fixture.
- Teste que varre o módulo procurando f-string de caminho de asset e falha se achar.
- Teste do mapeamento com casos de maiúscula e de prefixo inesperado.

---

### ✅ T-17 — Fusão de fontes

> **Concluído em 09/09/2026.**
>
> **A medição que definiu a integração:** o cdragon responde a **2,8 assets/s** com a
> concorrência de 4 da regra 4 do CLAUDE.md. Os 173 campeões inteiros custariam **~2 horas
> por patch** — não cabe na janela do workflow, e o S2 já mediu que square, splash, loading
> e tile **empatam** entre as duas fontes. Pagar duas horas para confirmar empate seria caro
> e inútil.
>
> Então a CLI busca no cdragon **só os tipos que o ddragon não trouxe** — `chroma` e
> `loading_vintage` —, e a premissa de empate continua **verificada em vez de assumida**:
> um punhado de campeões por execução vem completo, girando com o patch, e o
> `resolutionWins` do `status.json` denuncia se o cdragon vencer alguma disputa por
> resolução. Em ~58 patches todo campeão terá sido conferido.
>
> **`--sem-cdragon`** existe para o caminho do tarball ser testável e executável sozinho.

| | |
|---|---|
| **Objetivo** | Juntar ddragon e cdragon sem trocar os cortes de splash nem duplicar asset |
| **Dependências** | T-09, T-16 |
| **Estimativa** | ~200 linhas |
| **Effort** | médio |
| **Cobre** | §8 da Spec, [ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md) |

**Entra**
- Deduplicar por `(identidade, tipo canônico)`; vence a maior resolução, empate favorece
  ddragon.
- `source` e `sourceUrl` do vencedor registrados no índice.
- Relatório de fusão no `status.json`: quantos por fonte, quantos empates, quantos só
  existem em uma fonte.

**NÃO entra**
- Escolher por qualidade de JPEG. Só dimensão e, no empate, a fonte oficial.
- Fundir tipos diferentes. `splash_centered` e `splash_wide` **nunca** competem entre si.

**Critérios de aceite**
1. Mesma identidade e mesmo tipo em duas fontes → um registro só.
2. Empate de dimensão → vence ddragon, e o `source` diz isso.
3. `splash_centered` de uma fonte nunca substitui `splash_wide` da outra.
4. Chroma que só existe no cdragon sobrevive à fusão.
5. O total pós-fusão bate com a soma menos as duplicatas esperadas.

**Testes que provam**
- Tabela de casos: só-ddragon, só-cdragon, empate, cdragon maior, ddragon maior.
- Teste específico da não-competição entre os dois cortes de splash.

---

### ✅ T-18 — Testes de contrato das fontes (agendados)

> **Concluído em 09/09/2026.** 13 testes que **tocam a rede de verdade**, marcados
> `network` e excluídos da suíte padrão por `addopts` — a CI de PR nem os coleta.
>
> **Rodados contra as fontes vivas no dia da entrega, todos verdes:** CORS ainda `*` nas
> duas, as dimensões do S1 e do S2 intactas, os 55 apelidos apontando para campeões que
> existem no patch 16.18.1.
>
> **Decisão que o ticket não tomava:** o meta-teste da marca virou **três** asserções, não
> uma. A exclusão depende do `addopts` do `pyproject.toml` e do `pytestmark` do módulo
> concordarem, e os dois ficam longe um do outro — o terceiro teste falha se alguém
> escrever um teste de contrato **sem** a marca, que é o jeito de a suíte de PR ganhar um
> teste de rede sem ninguém notar.

| | |
|---|---|
| **Objetivo** | Descobrir que uma fonte mudou antes que o catálogo quebre em silêncio |
| **Dependências** | T-09, T-16 |
| **Estimativa** | ~200 linhas |
| **Effort** | médio |
| **Cobre** | §10 e §12 da Spec, [ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md) |

**Entra**
- Suíte separada, marcada `@pytest.mark.network`, que baixa 3 campeões conhecidos e valida
  que cada tipo existe **e tem a dimensão esperada** (1280×720, 1215×717, 308×560, 380×380,
  128×128, 64×64).
- Verificação dos ids da tabela de apelidos contra o `champion.json` do patch atual.
- Verificação de que ddragon e cdragon ainda mandam `Access-Control-Allow-Origin: *` —
  é a base técnica do ADR 0001.
- Workflow agendado próprio; falha abre issue.

**NÃO entra**
- Rodar em PR. São lentos, instáveis e barulhentos com as fontes.
- Bloquear deploy. Falha vira alerta.

**Critérios de aceite**
1. `pytest -m "not network"` (o que a CI de PR roda) não executa nenhum destes.
2. Dimensão diferente da esperada faz o teste falhar com mensagem dizendo qual e onde.
3. Id de apelido que não existe mais no patch atual faz falhar, citando o apelido.
4. Falha abre issue com o diff do que mudou.

**Testes que provam**
- Os próprios testes. Mais um meta-teste garantindo que a marca `network` exclui todos
  eles da suíte padrão.

---

### ✅ T-19 — Front: grade de campeões e painel com seletor de skin

> **Concluído em 09/09/2026.**
>
> - **A virtualização entra por contagem, não por tipo de lista.** Acima de 60 resultados
>   a lista vira virtual; abaixo, não paga o custo. Isso deixa a regra do
>   [ADR 0011](adr/0011-base-de-componentes-do-front.md) num número em vez de numa
>   convenção, e o `data-virtual` do scroller a torna testável.
> - **A busca perdeu o teto de 50 resultados.** Quem segura a lista passou a ser a
>   virtualização; cortar em 50 escondia resultado sem dizer.
> - **`vitest.setup.ts` novo**: o jsdom não traz `ResizeObserver` nem `scrollIntoView`, e o
>   cmdk usa os dois. Sem o stub, todo teste de componente que renderize a paleta morre com
>   um erro que não tem nada a ver com o que ele queria provar.
>
> O orçamento de 3 cliques está contado em teste, nos quatro caminhos do ADR 0010 — com um
> contador de verdade, não por inspeção.

| | |
|---|---|
| **Objetivo** | Dar a navegação no nível de campeão e o seletor de skin no nível certo — dentro do painel |
| **Dependências** | T-14 |
| **Estimativa** | ~280 linhas |
| **Effort** | alto |
| **Cobre** | RF-04, RF-15, RF-25, [ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md) |

**Entra**
- **Grade padrão de 173 campeões**, a partir de `catalog.champions[]`, cada cartão com a
  arte da skin base e o número de skins.
- **Painel do campeão** com a lista de skins dele e o seletor; escolher uma skin troca os
  assets exibidos.
- **Resultado de skin abre o painel do campeão já com aquela skin selecionada** — o
  resultado de busca é atalho para dentro do painel, não destino separado.
- Carregar a fatia de assets sob demanda, na primeira abertura de painel.
- **TanStack Virtual nos resultados de busca de skin** (até 2.118). A grade de 173
  campeões e a lista de skins do painel (até ~90) **não** virtualizam — não pagam o custo
  ([ADR 0011](adr/0011-base-de-componentes-do-front.md)).
- Altura de item fixa por breakpoint, que é o que a virtualização exige.
- Contagem de cliques do fluxo mantida em ≤ 3.

**NÃO entra**
- Grade de skins soltas. Foi o erro que o [ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md) corrigiu.
- Chromas (T-20), filtros (T-24).
- Decisão visual — ver a nota no topo.

**Critérios de aceite**
1. Sem nada digitado, a grade tem exatamente 173 cartões, cada um com contagem de skins.
2. `deus da guerra` → clicar no resultado abre o painel de Jax com a skin 24004 já
   selecionada.
3. `jax` → clicar no resultado abre o painel de Jax na skin base.
4. Trocar de skin no seletor troca os assets sem recarregar a fatia.
5. Nenhum chroma aparece na grade nem na lista de skins do painel.
6. Do carregamento ao arquivo salvo: ≤ 3 cliques nos quatro caminhos do ADR 0010,
   contados por teste.
7. Com 2.118 resultados de skin, o número de nós no DOM fica na casa das dezenas, não dos
   milhares, e a rolagem não perde quadro.

**Testes que provam**
- Vitest com catálogo de fixture completo: contagem da grade, atalho da busca para a skin
  certa, troca de skin, ausência de chroma.
- Teste que conta cliques dos quatro caminhos e falha em > 3.
- Teste que conta nós renderizados com 2.118 resultados e falha se a virtualização sumir.

---

### ✅ T-20 — Front: chromas atrás de toggle

> **Concluído em 09/09/2026, junto com o T-19** — o toggle vive dentro do painel do
> campeão, e separar os dois em PRs diferentes deixaria um deles sem o que mostrar.
>
> **Decisão que o ticket não tomava:** trocar de skin **fecha** os chromas abertos. Sem
> isso, o toggle continuaria aberto mostrando os chromas da skin anterior — que é
> exatamente o tipo de coisa que passa despercebida e mostra a arte errada.

| | |
|---|---|
| **Objetivo** | Dar acesso aos 7.037 chromas sem poluir nenhum resultado |
| **Dependências** | T-19 |
| **Estimativa** | ~120 linhas |
| **Effort** | baixo |
| **Cobre** | RF-06, [ADR 0008](adr/0008-catalogo-de-skins-e-seletor.md), [ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md) |

**Entra**
- Dentro do painel do campeão, na skin selecionada, um controle que revela os chromas dela,
  ligados por `parentSkinNum`.
- Chroma baixa como qualquer outro asset.

**NÃO entra**
- Chroma na busca de primeiro nível. É explicitamente proibido pelo RF-06.
- Nome próprio de chroma — o cdragon não fornece; usa-se o da skin-mãe + número.
- Decisão visual — ver a nota no topo.

**Critérios de aceite**
1. Nenhum chroma aparece em resultado de busca nem na grade de campeões.
2. O controle revela exatamente os chromas cujo `parentSkinNum` casa com a skin selecionada.
2b. `chromaCount` do catálogo bate com a quantidade revelada.
3. Skin sem chroma não mostra o controle.
4. Chroma revelado baixa com o `fileName` do índice.

**Testes que provam**
- Vitest com skin com chroma e skin sem, cobrindo os quatro critérios.

---

# Onda 4 — categorias e download em lote

**Execução: (T-21 ∥ T-22)**, com **(T-24 ∥ T-25)** em paralelo. ⏸️ T-23 e T-26 suspensos.

### ✅ T-21 — Indexar as categorias não-campeão do ddragon

> **Concluído em 09/09/2026.** As cinco categorias já vinham do **T-09** — o que faltava
> eram as **etiquetas de filtro**, e é isso que este ticket entregou.
>
> **Nada é inventado:** cada etiqueta sai de um campo que a própria fonte declara.
> `compravel` vem de `gold.purchasable`, `mapa:sr|aram|arena` de `maps`, `classe:*` das
> `tags` que a Riot já dá, `arvore:*` do `runesReforged.json`.
>
> **Decisão que o ticket não tomava:** stat mod leva `arvore:nenhuma` em vez de ficar sem
> etiqueta. Ele não pertence a árvore alguma, e isso é **informação** — sem ela, o filtro
> por árvore teria que fingir que stat mod é runa ou deixá-lo fora sem explicar.
>
> Medido no patch real: **865 dos 868 itens** com etiqueta, 696 compráveis (os outros 172
> são missão, modo antigo ou upgrade do Ornn, que é exatamente o que a §B.1.6 queria
> separar), 77 runas com árvore, 5 mapas. O índice cresceu 140 KB.
>
> Categoria sem etiqueta fica com o campo **ausente**, não com `[]`: lista vazia no índice
> seria ruído com aparência de dado.

| | |
|---|---|
| **Objetivo** | Cobrir item, runa, feitiço, ícone de perfil e mapa |
| **Dependências** | T-09 |
| **Estimativa** | ~300 linhas |
| **Effort** | alto |
| **Cobre** | RF-08, §6.1 da Spec |

**Entra**
- Categorias `item`, `rune`, `summoner_spell`, `profile_icon`, `map`, com nomes em
  `pt_BR`/`en_US` e as `tags` da §B.1.6 (comprável, mapa 11/12/30).
- `hasAlpha` medido: runas e stat mods são RGBA e nunca podem virar JPEG.
- Fatia própria por categoria.

**NÃO entra**
- Emotes, wards e ranks (T-22). Não vêm do tarball.
- Filtro de UI (T-24).

**Critérios de aceite**
1. Totais batem com S1: 868 itens, 726 feitiços, 5.021 ícones de perfil, 5 mapas.
2. Runas saem com `hasAlpha: true` e `format: "png"`.
3. `tags` permitem filtrar comprável e por mapa.
4. Cada categoria vira uma fatia própria no manifesto.

**Testes que provam**
- Unitários com fixture por categoria, incluindo o caso de alfa.
- Teste dos totais contra as contagens de S1.

---

### ✅ T-22 — Indexar emotes e ward skins

> **Concluído em 09/09/2026.** As contagens batem **exatamente**: 2.338 emotes e 530
> arquivos de ward. As 9 entradas que faltavam para os 2.347 declarados trazem
> `/lol-game-data/assets/` e **nada depois** — casam a regra de mapeamento e não apontam
> para arquivo nenhum. Ficam registradas como não mapeáveis.
>
> **Uma medição corrigiu outra:** o S4 projetou 7,7 MB de wards a partir de uma amostra de
> 40 arquivos; o total real é **25,3 MB**, medido duas vezes com `sha256` idêntico. A
> amostra não era representativa. Emotes ficaram
> em 148,3 MB contra 156,5 MB projetados, dentro da margem.
>
> **Correção de desempenho que veio junto:** o cdragon estava sendo buscado com
> concorrência **1**, não 4 — um `await` por asset dentro de um laço. A regra 4 do CLAUDE.md
> permite 4 por host. Com `asyncio.gather` sob o mesmo semáforo, a busca foi de **2,8 para
> 32 assets/s**, e a amostra de verificação da fusão (T-17) subiu de 3 para 12 campeões por
> execução — de ~58 patches para ~15 até todo campeão ter sido conferido.

> **Reduzido em 07/09/2026** ([ADR 0012](adr/0012-onde-guardar-os-assets.md)): os
> **emblemas de elo saem da v1**. O emblema composto só existe dentro do
> `ranked-emblems-latest.zip`, de 61,5 MB; verifiquei que o cdragon tem as *peças*
> (`diamond_base.png`, `diamond_crown_d1.png`, `backlight.png`) com CORS aberto, mas não o
> emblema montado — e compor violaria o [ADR 0001](adr/0001-formato-de-entrega-dos-assets.md).
> Sem storage, não há onde guardar o resultado da extração do zip.

| | |
|---|---|
| **Objetivo** | Fechar o catálogo com o que só existe fora do tarball |
| **Dependências** | T-16, T-02 |
| **Estimativa** | ~250 linhas |
| **Effort** | médio |
| **Cobre** | RF-08, §A.3 do KICKOFF, §B.4 |

**Entra**
- Emotes (2.347) e ward skins (265) pelo cdragon, partindo dos JSONs `v1/`.
- Respeitar as dimensões e formatos medidos no T-02.

**NÃO entra**
- **Emblemas de elo.** Fora da v1 — ver a nota acima.
- Assets da wiki. Bloqueado pelo [ADR 0004](adr/0004-consentimento-da-wiki-e-teto-de-resolucao.md).
- Ícones de posição e moedas — v2.

**Critérios de aceite**
1. As duas categorias aparecem no manifesto com contagem conferida: 2.338 emotes e 530
   arquivos de ward (265 wards × 2 imagens). ✅ **Batem exatamente.**
2. ~~O total de bytes bate com o medido em T-02, com margem de 15 %.~~ → **Ajustado em
   09/09/2026: o número do T-02 para wards estava errado.** Emotes fecham em **148,3 MB**
   contra os 156,5 MB projetados (**−5,2 %**, dentro da margem). Wards fecham em
   **25,3 MB** contra 7,7 MB projetados (**+229 %**): o S4 extrapolou de uma amostra de 40
   arquivos com mediana de 15,3 KB, e a média real é 65 KB. O critério passa a ser a
   medição completa registrada em
   [`docs/evidencias/t22-emotes-e-wards.json`](evidencias/t22-emotes-e-wards.json), não a
   extrapolação. **Não muda o produto:** desde o [ADR 0012](adr/0012-onde-guardar-os-assets.md)
   nada é armazenado, e esses bytes só existem como número no índice.
3. Nenhuma requisição à wiki.
4. Nenhum registro com `category: "rank"` é produzido.

**Testes que provam**
- Unitários com fixture dos JSONs das duas categorias.
- Teste de que o total medido não diverge do projetado além da margem.
- Teste que falha se algum registro sair com `category: "rank"`.

---

### ⏸️ T-23 — Zips por categoria pré-gerados — **SUSPENSO**

> ⏸️ **Suspenso em 07/09/2026** ([ADR 0012](adr/0012-onde-guardar-os-assets.md)): sem
> storage não há onde pré-gerar, e o **RF-16 saiu da v1**. O ticket **não foi apagado** —
> ele volta inteiro se um dia a opção A for retomada, junto com o T-06. Até lá, o download
> em lote é só o do cliente (T-25).

| | |
|---|---|
| **Objetivo** | Entregar "todos os ícones de item" sem o navegador baixar 868 arquivos |
| **Dependências** | T-21, T-22 |
| **Estimativa** | ~180 linhas |
| **Effort** | médio |
| **Cobre** | ~~RF-16~~ — fora da v1 ([ADR 0012](adr/0012-onde-guardar-os-assets.md)) |

**Entra**
- Um zip por categoria, gerado no indexador, com os arquivos nomeados pelo `fileName`.
- Entradas `zips[]` no manifesto, com bytes, contagem e `sha256`.
- Zip entra no orçamento do RNF-05.

**NÃO entra**
- Zip por campeão ou por seleção — é no cliente (T-25).
- Recompressão dos assets. Zip em modo `stored` para JPEG e PNG já comprimidos.

**Critérios de aceite**
1. Um zip por categoria, listado no manifesto e baixável direto do bucket.
2. O `Content-Length` bate com o manifesto.
3. Descompactar produz exatamente os `fileName` do índice.
4. Os zips entram na conta do orçamento e podem fazer T-10 abortar.

**Testes que provam**
- Unitário que gera, lê de volta e compara a lista de nomes com o índice.
- Teste de que o modo de compressão é `stored`.

---

### ✅ T-24 — Front: navegação por categoria e filtros

| | |
|---|---|
| **Objetivo** | Dar um caminho para quem não sabe o nome do que procura |
| **Dependências** | T-21, T-22 |
| **Estimativa** | ~280 linhas |
| **Effort** | alto |
| **Cobre** | RF-08, RNF-03 |

> ✅ **Entregue em 09/09/2026.** Dois dos seis filtros nomeados no RF-08 **não existem**, e
> não por esquecimento:
>
> - **`elo`** — a categoria `rank` saiu da v1 com o
>   [ADR 0012](adr/0012-onde-guardar-os-assets.md). Não há o que filtrar.
> - **`lane`** — nenhuma das duas fontes declara posição. O `champion.json` do ddragon traz
>   `tags` (as seis classes) e o cdragon traz o mesmo; lane só existe em fontes de
>   estatística, que este projeto não usa. Escrever "Top/Jungle/Mid/ADC/Suporte" à mão seria
>   inventar dado, que é a única coisa que o projeto não faz. Se um dia entrar, entra como
>   fonte nova e ticket próprio.
>
> Os outros quatro entregaram, e **`função` mudou de lugar**: ela é atributo de campeão, e
> campeão é a home ([ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md)), então o
> filtro vive na grade e não na navegação por categoria. Medido no catálogo real: Mago 75,
> Lutador 60, Assassino 46, Tanque 46, Suporte 43, Atirador 33 — os 173 campeões têm função.
>
> Os grupos de filtro das categorias são **derivados da fatia carregada**, não declarados:
> `compravel`, `mapa:*`, `classe:*`, `arvore:*` e `slot:*` viram grupo porque estão nos
> dados. Fonte que parar de trazer uma etiqueta faz o grupo sumir sozinho.

**Entra**
- Navegação por categoria, carregando a fatia sob demanda (a home só carrega o catálogo).
- **TanStack Virtual nas categorias grandes** — ícones de perfil (5.042) e emotes (2.338)
  ([ADR 0011](adr/0011-base-de-componentes-do-front.md)). O limite mora no
  `asset-panel.ts` e vale para os dois usos do painel: 200 cartões.
- Filtros por ~~lane~~, função, comprável, mapa, árvore de runa e ~~elo~~, a partir das
  `tags` — ver a nota acima.
- Combinação de filtro com busca.

**NÃO entra**
- Filtro salvo entre sessões. Sem back-end e sem conta.
- Decisão visual — ver a nota no topo.

**Critérios de aceite**
1. ✅ Abrir uma categoria carrega só a fatia dela.
2. ✅ Cada filtro reduz a lista corretamente, e combinados também (OU dentro do grupo, E
   entre grupos).
3. ✅ A fatia `champion` continua sendo a única carregada na home (RNF-03) — e a navegação
   por categoria nem essa pede.
4. ✅ Filtro sem resultado mostra estado vazio com o que foi filtrado, em palavras.
5. ✅ Abrir a categoria de ícones de perfil (5.042) desenha **12 cartões**, não 5.042.

**Testes que provam**
- Vitest com fixture multicategoria: carga sob demanda, cada filtro, combinações, vazio.
- Teste de rede que confirma que só uma fatia é buscada, contado em URLs pelo `AssetsClient`.
- O teste da escala empresta uma janela de 700 px ao jsdom (`offsetHeight`), porque sem
  layout o virtualizador desenha **zero** cartões — e zero passaria numa asserção de
  "poucos nós" sem provar nada.

---

### ✅ T-25 — Front: seleção múltipla e zip no cliente

| | |
|---|---|
| **Objetivo** | "Tudo do Jax" e seleção livre, sem servidor — e, desde o [ADR 0012](adr/0012-onde-guardar-os-assets.md), **o único caminho de download em lote** |
| **Dependências** | T-19 |
| **Estimativa** | ~200 linhas |
| **Effort** | médio |
| **Cobre** | RF-17, RF-18, [ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md) |

> ✅ **Entregue em 09/09/2026.** Três decisões que o ticket não previa e que valem registro:
>
> - **Falha de um arquivo não derruba o lote.** Numa seleção de 300, abortar por causa de um
>   404 é hostil. O que não veio entra num `FALHAS.txt` **dentro do zip**, com motivo e URL —
>   quem abrir vê o que falta, em vez de contar 299 e não saber qual sumiu.
> - **Nome repetido não sobrescreve.** `zip.file()` sobrescreve em silêncio: 300 selecionados
>   virariam 299 arquivos sem erro nenhum. Colisão vira `(2)`, `(3)`.
> - **Chroma só entra se estiver revelado.** "Tudo do Jax" com os chromas escondidos leva 3
>   assets; com o controle aberto, 5. Arrastar 43 chromas que a tela não mostrou é a mesma
>   surpresa que o RF-06 existe para evitar.
>
> A §6.1 da Spec dizia "3 minutos e meio" para os ícones de perfil; pela taxa que ela mesma
> declara (28/s) são **3 min 1 s**. A linha foi corrigida junto com o teste que calcula.

**Entra**
- Selecionar vários assets e baixar como zip montado com JSZip, em modo `STORE` — JPEG e
  PNG já vêm comprimidos, e deflatar de novo gasta CPU do usuário para economizar ~0%.
- Concorrência 4 na busca dos bytes (regra 4 do CLAUDE.md: são as mesmas fontes de
  terceiros do indexador), e cancelamento.
- Ação "tudo deste campeão" que pré-monta a seleção, e "selecionar os N filtrados" na
  navegação por categoria.
- Acima de 300 arquivos ou 500 MB, **avisar** com estimativa de tempo honesta. Não há mais
  zip por categoria para onde empurrar (T-23 suspenso), então o aviso precisa informar em
  vez de redirecionar. Base medida: ~28 arquivos/s.
- Progresso durante a montagem, obrigatório — a categoria `item` leva ~31 s.

**NÃO entra**
- Conversão PNG em lote. Fica para v2 se alguém pedir.
- Qualquer chamada a servidor próprio.

**Critérios de aceite**
1. ✅ Selecionar N assets e baixar produz um zip com N arquivos, com os `fileName` corretos —
   gerado com o JSZip real e **relido** com o JSZip real, bytes conferidos.
2. ✅ Nenhuma requisição a servidor próprio durante a montagem: o teste lista as URLs
   pedidas e confere o host de cada uma.
3. ✅ Acima do limite aparece o aviso com a estimativa, e o botão **continua habilitado**.
4. ✅ "Tudo do Jax" seleciona todos os assets do campeão, chromas incluídos se revelados.

**Testes que provam**
- Vitest montando um zip de fixture e lendo de volta a lista de nomes.
- Teste do limite (aparece o aviso com estimativa, o botão continua habilitado).
- Teste de rede confirmando ausência de chamada a servidor próprio.
- Teste de que a concorrência nunca passa de 4.

---

### ⏸️ T-26 — Front: seletor de versão e modo histórico honesto

> ⏸️ **Suspenso em 08/09/2026** pelo [ADR 0013](adr/0013-uma-versao-por-vez-no-indice.md).
> O índice guarda uma versão só, então não há o que selecionar nem modo histórico a
> tornar honesto. RF-19 e RF-20 saíram da v1 junto. O ticket fica escrito: se o teto
> de uma versão for revisto, ele volta como está — o que ele descreve continua certo.

| | |
|---|---|
| **Objetivo** | Permitir patch antigo sem mentir sobre o que existe |
| **Dependências** | T-11 |
| **Estimativa** | ~200 linhas |
| **Effort** | médio |
| **Cobre** | RF-19, RF-20, [ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md) |

**Entra**
- Seletor de versão a partir do manifesto, com `currentVersion` como padrão.
- **Toda** versão tem `assetsCopied: false` desde o [ADR 0012](adr/0012-onde-guardar-os-assets.md),
  então o front sempre usa `sourceUrl`. O que distingue o modo histórico é a **ausência dos
  tipos não versionados**, garantida pelo T-11.
- Aviso explícito de que splash, loading e tile de patches antigos **não existem** — e por quê.

**NÃO entra**
- Servir a arte atual com rótulo antigo. É exatamente o que o RF-20 proíbe.
- Comparar versões lado a lado. v2.

**Critérios de aceite**
1. Trocar de versão recarrega o índice daquela versão.
2. Em versão antiga, nenhum card de splash, loading ou tile é renderizado.
3. O aviso aparece e explica o motivo.
4. Download em versão antiga usa `sourceUrl` e funciona.

**Testes que provam**
- Vitest com manifesto de duas versões, uma com assets e outra sem.
- Teste de que nenhum tipo não versionado renderiza no modo histórico.

---

# Onda 5 — fechamento do produto

**Execução: (T-27 ∥ T-28 ∥ T-31) → T-29 → T-30.**

### ✅ T-27 — Página "Sobre", créditos e rodapé legal

| | |
|---|---|
| **Objetivo** | Cumprir a obrigação legal e dar crédito às fontes |
| **Dependências** | T-08 |
| **Estimativa** | ~120 linhas |
| **Effort** | baixo |
| **Cobre** | RF-21, RF-22, RF-23, RNF-10 |

**Entra**
- Rodapé com o aviso legal da Riot em todas as páginas.
- Página "Sobre" com o que é o projeto, as fontes (ddragon, cdragon, Riot static), as
  licenças e o aviso de não afiliação.
- Bloco preparado para o crédito à League of Legends Wiki / Weird Gloop, **desligado** até
  o consentimento.

**NÃO entra**
- Texto legal definitivo (é T-33, junto com o nome do produto).
- Decisão visual — ver a nota no topo.

**Critérios de aceite**
1. ✅ O aviso legal aparece em toda página — mora no `layout.tsx`, que é o único caminho por
   onde toda página passa.
2. ✅ A página cita todas as fontes efetivamente usadas, e um teste percorre os valores de
   `AssetSource` exigindo crédito para cada um: **fonte nova não entra sem crédito**.
3. ✅ O crédito à wiki não aparece enquanto o consentimento não existir.
4. ✅ O nome exibido continua passando na regra do [ADR 0003](adr/0003-nome-publico-do-produto.md).

**Testes que provam**
- Vitest: presença do aviso, ausência do bloco da wiki com a flag desligada, regra do nome.

> ✅ **Entregue em 09/09/2026.** Duas coisas que o ticket não dizia e que valem registro:
>
> - **Creditar a wiki antes da autorização é pior que não creditar.** Seria afirmar em
>   público que usamos conteúdo de quem pediu, nos termos, para não ser usado de forma
>   automatizada ([ADR 0004](adr/0004-consentimento-da-wiki-e-teto-de-resolucao.md)). O
>   `NEXT_PUBLIC_WIKI_CONSENT_GRANTED` espelha a trava do indexador, e o teste exige que a
>   página **não** contenha "Weird Gloop" hoje.
> - **As duas licenças ficam separadas.** A arte é da Riot em todas as fontes; o CC BY-SA
>   3.0 vale só para o texto da wiki. Confundir as duas é o risco anotado no KICKOFF, e o
>   teste exige que nenhuma outra fonte reivindique licença de texto.

---

### ✅ T-28 — Acessibilidade

| | |
|---|---|
| **Objetivo** | Teclado, contraste e texto alternativo em tudo |
| **Dependências** | T-15, T-19 |
| **Estimativa** | ~120 linhas |
| **Effort** | médio |
| **Cobre** | RNF-11 |

**Entra**
- Navegação completa por teclado, incluindo a grade de resultados e o painel.
- `alt` em toda imagem, com o nome do asset.
- Foco visível e ordem de foco previsível; `aria` no painel.
- axe integrado ao e2e.

**NÃO entra**
- Escolha de cores de contraste — vem do design (T-30). O que este ticket entrega é a
  **verificação** automática; o ajuste de paleta é feito lá.

**Critérios de aceite**
1. ✅ Todo o fluxo J1 é possível só com teclado — digitar, `Enter` no resultado, `Enter` no
   botão de baixar, com o arquivo salvo conferido.
2. ✅ axe não reporta violação crítica nem séria em nenhuma das quatro telas.
3. ✅ Toda `img` tem `alt` não vazio, e a prévia traz o nome do asset.
4. ✅ O foco é visível em todo elemento interativo — nenhum controle zera o `outline` do
   `:focus-visible` sem substituto.

**Testes que provam**
- axe no Playwright em home, painel, categoria e "Sobre".
- Percurso por teclado do fluxo completo, mais `Escape`, `/` e a ordem de tabulação.

> ✅ **Entregue em 09/09/2026.** Duas correções de comportamento saíram daqui, e as duas
> vieram de teste que falhou por motivo certo:
>
> - **`Escape` não funcionava antes de a fatia chegar.** O ouvinte morava no
>   `PainelDeAsset`, que só monta depois dos assets — então a tecla ficava sem efeito
>   exatamente durante a espera, que é quando alguém mais desiste. Subiu para o
>   `PainelDoCampeao`.
> - **`Escape` com chromas abertos fechava tudo de uma vez.** Dois ouvintes na mesma tecla.
>   Agora é um só, e fecha o de dentro primeiro.
>
> O teste do axe **verifica que o axe rodou**: sem isso, uma análise que não injetou
> devolveria zero violações e o teste passaria provando nada.
>
> **O contraste é o critério que este ticket não fecha**, e é de propósito: a paleta chega
> com o design (T-30). O que fica pronto é a verificação, para o design chegar já sob ela.

---

### ✅ T-29 — e2e do fluxo completo

| | |
|---|---|
| **Objetivo** | Provar a regra dos 3 cliques e o fluxo buscar→baixar de ponta a ponta |
| **Dependências** | T-19, T-25 |
| **Estimativa** | ~250 linhas |
| **Effort** | médio |
| **Cobre** | RF-15, RF-02, RF-03, RF-09, RF-11, RF-13, RNF-01, RNF-02 |

**Entra**
- Playwright contra um bucket de fixture servido localmente.
- Jobs J1 e J2 medidos em cliques e em tempo.
- Download real verificado: nome, MIME e dimensão do arquivo salvo.
- Job novo na CI.

**NÃO entra**
- Testar contra o bucket de produção. Fixture local é determinístico.
- Teste visual de regressão. Depois de T-30, se fizer sentido.

**Critérios de aceite**
1. ✅ J1 e J2 completam em ≤ 3 cliques, contados por um contador de verdade — e há um teste
   provando que o contador falha no quarto.
2. ✅ O arquivo baixado tem o `fileName` esperado e o **conteúdo** certo: `sha256` igual ao
   do índice e assinatura de JPEG nos bytes. Conferir o conteúdo vale mais que o MIME
   anunciado.
3. ✅ O PNG convertido tem as mesmas dimensões do original, lidas do IHDR do arquivo salvo.
4. ✅ Busca em < 50 ms medidos **dentro da página** e prévia em < 1 s.
5. ✅ O job roda em todo PR.

**Testes que provam**
- Os próprios cenários Playwright: 13, em ~20 s.

> ✅ **Entregue em 09/09/2026.** Três coisas que valem registro:
>
> - **A fixture é servida de outra origem** (`127.0.0.1:4321` contra `localhost:3000`), como
>   o ddragon é em produção. É isso que faz o teste do RF-11 valer: sem CORS aberto o canvas
>   fica *tainted* e o `toBlob` falha — a hipótese inteira do
>   [ADR 0001](adr/0001-formato-de-entrega-dos-assets.md), rodando de verdade.
> - **A prévia da imagem não existia.** O RNF-02 mede "a prévia da splash em < 1 s" e o
>   cartão só mostrava a ficha. Sem prévia o critério 4 era immensurável, então o cartão
>   ganhou um `<img>` — `loading="lazy"`, `alt` com o nome do asset, e `<img>` cru em vez de
>   `next/image` porque a URL é de terceiro e o [ADR 0012] não tem proxy.
> - **O RNF-01 é medido dentro da página**, com `performance.now()` em volta do evento de
>   input até o quadro seguinte. Medir por fora somaria o custo do protocolo do Playwright
>   ao número do requisito.
>
> Só Chromium na CI: o e2e prova comportamento e o caminho do canvas, não compatibilidade
> entre motores.

---

### ✅ T-30 — Integrar o design aprovado

| | |
|---|---|
| **Objetivo** | Aplicar o desenho feito no Claude Design sobre o comportamento já testado |
| **Dependências** | T-27, T-28, T-29, **T-34** |
| **Estimativa** | ~300 linhas |
| **Effort** | médio |
| **Cobre** | §A.4 do KICKOFF, RNF-11 |

> ✅ **Entregue em 10/09/2026.** Todas as telas vestidas com os tokens do T-34, e a
> suíte inteira das ondas anteriores passando **sem uma linha alterada** — é essa a
> prova de que só a aparência mudou.

**Entra**
- Aplicação dos tokens de **T-34** nos componentes já existentes, **sem mudar
  comportamento**, conferindo cada tela contra a referência em `docs/design/`.
- Verificação de contraste sobre a paleta escolhida.
- Ajuste de responsividade.

**NÃO entra**
- Mudar comportamento ou critério de aceite de ticket anterior. Se o design pedir
  comportamento diferente, **abre-se ticket novo** — este só veste.

**Critérios de aceite**
1. ✅ **325 testes de vitest e os 28 cenários e2e anteriores passam sem alteração.**
2. ✅ axe sem violação séria nem crítica em home, painel, categoria, "Sobre" **e em tela
   estreita** — cinco varreduras.
3. ✅ O layout funciona em telas estreitas: 4 cenários novos a 375px, incluindo "nada
   transborda na horizontal" e "o aviso legal continua inteiro".
4. ✅ Nenhuma cor solta: a regra de lint do T-34 é erro. Espaçamento vem da escala do
   Tailwind (`px-2.5`, `p-1.25`), sem valor arbitrário.

**Testes que provam**
- A suíte inteira, inalterada.
- axe com a paleta nova, agora incluindo a viewport estreita.
- Teste de contraste dos pares de token.

> **Três coisas que o axe pegou e nenhum teste de unidade pegaria:**
>
> 1. **O botão primário perdeu a cor do texto.** `cn("bg-acento text-superficie", "text-12")`
>    — o `tailwind-merge` não sabe que `text-12` é **tamanho** e `text-superficie` é **cor**,
>    então descartou a segunda. O botão herdou o branco do corpo e caiu para **3,1:1** sobre
>    o violeta em vez de 4,64:1. O teste de tokens comparava valores e passou; quem viu foi o
>    axe, no navegador, onde as classes viram cor. Corrigido ensinando o `twMerge` a escala
>    do design.
> 2. **Link só por cor** (WCAG 1.4.1, *serious*): o design usa `text-decoration: none` em
>    link. Dentro de bloco de texto isso reprova, e os links da página "Sobre" ganharam
>    sublinhado. Link de navegação, que não está em bloco de texto, ficou como o design quer.
> 3. **O `Dialog` do Radix mudou comportamento sem avisar.** Ao virar diálogo, o painel do
>    campeão passou a fechar por `Escape` do próprio Radix (atropelando a ordem
>    chroma-primeiro) e por clique fora (que ele nunca teve). Dois testes de onda anterior
>    caíram. O `PainelLateral` ganhou `fecharPorEsc` e `fecharPorFora`, e o painel do campeão
>    desliga os dois — **vestir não é mudar comportamento**.
>
> **Uma adaptação do design ao dado real:** o cartão do campeão é **1:1**, não o 16:9 do
> mock. A miniatura do campeão é o `square` de 128×128 do ddragon; cortá-la em 16:9 tiraria
> 44% da altura, que é onde está o rosto. O 16:9 volta quando houver cartão de skin.
>
> **Uma dívida registrada:** na tela estreita o aviso legal fica no topo, porque a barra
> lateral vira faixa. É conforme (o RF-21 pede visível, e ele está inteiro e visível), mas
> come a primeira dobra. Levá-lo para o pé da página exigiria inverter a ordem de DOM entre
> navegação e conteúdo, o que piora a ordem de tabulação. Fica como está, anotado.

---

### ✅ T-31 — Aviso de índice velho

| | |
|---|---|
| **Objetivo** | Detectar "a indexação parou" sem monitoramento |
| **Dependências** | T-08 |
| **Estimativa** | ~60 linhas |
| **Effort** | baixo |
| **Cobre** | §11 da Spec, RNF-06 |

**Entra**
- Se `manifest.generatedAt` tem mais de 72 h, um aviso discreto aparece no site.
- O aviso mostra a data da última indexação.

**NÃO entra**
- Bloquear o uso. O site velho ainda serve.
- Decisão visual — ver a nota no topo.

**Critérios de aceite**
1. ✅ Manifesto com 71 h → sem aviso. Com 73 h → aviso. No limite exato, ainda sem aviso.
2. ✅ O aviso mostra a data legível e o `datetime` da máquina, mais a idade em palavras.
3. ✅ O site continua plenamente funcional: é `role="status"`, não `alert`, e não bloqueia
   nada.

**Testes que provam**
- Vitest com relógio fake nos dois lados do limite.

> ✅ **Entregue em 09/09/2026.** O limite de 72 h é escolhido, não herdado: o workflow roda a
> cada 6 h, então são **doze execuções seguidas sem sucesso** — isso não é lentidão da Riot
> nem fila do Actions, é coisa quebrada. Apertar mais transformaria fim de semana devagar em
> alarme falso, e alarme falso é como se aprende a ignorar alarme.

---

### ✅ T-35 — Tirar o `next-env.d.ts` do controle de versão

| | |
|---|---|
| **Objetivo** | Remover uma armadilha que quebra a CI em silêncio |
| **Dependências** | nenhuma |
| **Estimativa** | ~15 linhas (configuração) |
| **Effort** | baixo |
| **Cobre** | RNF-12 |

> Descoberto durante o **T-08**. O `next dev` acrescenta sozinho
> `/// <reference path="./.next/types/routes.d.ts" />` ao `next-env.d.ts`. Como `.next/` é
> gerado e ignorado pelo Git, commitar essa linha faz o `tsc` da CI falhar procurando um
> arquivo que não existe lá. Hoje o arquivo está versionado e alguém vai commitar a
> alteração sem perceber.

**Entra**
- `next-env.d.ts` sai do controle de versão e entra no `.gitignore`, como o Next faz por
  padrão.
- Uma declaração ambiente própria em `apps/web/src/types/` para o que o `tsc` realmente
  precisa sem os tipos gerados — hoje, só `declare module "*.css"`.
- Ajuste do `include` do tsconfig.

**NÃO entra**
- Rodar `next build` na CI. O ticket é sobre o `tsc`, que é o que a CI já roda.

**Critérios de aceite**
1. ✅ `tsc --noEmit` passa com `.next/` ausente e com `next-env.d.ts` ausente.
2. ✅ `next dev` não deixa mais a árvore suja — verificado rodando `next build` inteiro: o
   arquivo é regerado e o `git status` não o vê.
3. ✅ A CI continua verde.

**Testes que provam**
- A própria CI, que roda a partir de um clone limpo, sem `.next/`.

> ✅ **Entregue em 09/09/2026.** O `include` do tsconfig **continua o que o Next escreve**,
> e isso é a parte não óbvia: tirar `next-env.d.ts` de lá parecia mais limpo, mas o
> `next dev` reescreve o tsconfig e põe a linha de volta — a árvore ficaria suja pelo outro
> arquivo. Padrão de `include` que aponta para arquivo ausente não é erro para o `tsc`, e é
> isso que faz a solução simples funcionar.
>
> Sobrou uma declaração ambiente própria em `src/types/ambiente.d.ts`, com o que o `tsc` da
> CI precisa sem os tipos gerados. Hoje é uma linha: `declare module "*.css"`.

---

### ✅ T-38 — Reindexar quando o indexador muda, não só quando o patch muda

| | |
|---|---|
| **Objetivo** | Que uma melhoria no indexador chegue ao site sem esperar duas semanas |
| **Dependências** | T-13 |
| **Estimativa** | ~60 linhas |
| **Effort** | baixo |
| **Cobre** | RNF-05, §9 |

> Descoberto em **09/09/2026**, ao entregar o T-22. O `decide` do `scheduling.py` compara
> **só a versão do jogo**: `indexed != latest`. O T-21 acrescentou etiquetas de filtro e o
> T-22 acrescentou emotes e wards, e nenhum dos dois chegou ao índice publicado — a Riot
> ainda está no 16.18.1, então o workflow olha, vê a mesma versão e não faz nada. A saída
> hoje é disparar o workflow à mão com `force`, o que foi exatamente o que se fez.

**Entra**
- Uma **assinatura de geração** no manifesto: o que o indexador produziria de diferente
  mesmo com a mesma versão do jogo. Candidato natural: `schemaVersion` mais a lista de
  categorias mais um número de geração que sobe quando um construtor muda.
- `decide` passa a reindexar quando a versão **ou** a assinatura diferem, com o motivo
  dizendo qual dos dois mudou.
- A assinatura entra no `index-manifest` (contrato `1.2.0`) e no seu JSON Schema.

**NÃO entra**
- Hash do código-fonte do indexador. Reindexaria a cada refatoração e a cada bump de
  dependência — 22 minutos e 2,39 GB por mudança de comentário.
- Reindexação a pedido pela interface. Não há back-end (ADR 0005).

**Critérios de aceite**
1. ✅ Mesma versão e mesma assinatura → não reindexa.
2. ✅ Mesma versão e assinatura diferente → reindexa, e o motivo diz "assinatura" **e qual**
   parte mudou: o número do indexador ou quais categorias entraram e saíram.
3. ✅ Versão diferente → reindexa como hoje, e o motivo fala do patch, não da assinatura.
4. ✅ Manifesto sem assinatura (o publicado hoje) → reindexa, e não quebra.
5. ✅ Contrato diferente também reindexa — `schemaVersion` novo é saída nova.

**Testes que provam**
- Unitários de `decide` para as cinco combinações, mais ordem de categorias e precedência.
- Testes de ponta a ponta no `check`, inclusive o caso real do T-22 (índice sem `emote` nem
  `ward`), **sem baixar nada** para descobrir.

> ✅ **Entregue em 09/09/2026.** Contrato do índice em **1.2.0**: o manifesto ganhou
> `generation` com `indexer` (número que sobe à mão) e `categories` (o que a execução
> emitiu de verdade).
>
> **Por que o número é manual.** Hash do código reindexaria 2,39 GB a cada refatoração e a
> cada bump de dependência. O preço de ser manual é lembrar de subir, e por isso o histórico
> de cada bump está escrito ao lado da constante: "por que este número é 3?" tem resposta
> sem `git log`.
>
> **`categories` é o que foi emitido, não o que uma execução padrão emitiria.** Rodar com
> `--sem-cdragon` grava uma assinatura menor, e a próxima execução reindexa por causa
> disso — que é o certo, porque esse índice está mesmo incompleto.
>
> **O índice publicado hoje não tem o campo** (foi gerado antes deste ticket), então a
> próxima execução agendada vai reindexar uma vez dizendo "sem assinatura de geração". É o
> comportamento pedido no critério 4.

---

### ⏳ T-39 — Fatiar `champion` quando ela apertar o RNF-03

| | |
|---|---|
| **Objetivo** | Não deixar a fatia da primeira abertura estourar o orçamento do navegador |
| **Dependências** | T-10 |
| **Estimativa** | ~120 linhas |
| **Effort** | médio |
| **Cobre** | RNF-03 |

> Medido em **09/09/2026**, na primeira publicação com as duas fontes: a fatia `champion`
> tem **1.488.627 bytes gzip** contra o limite de **1.572.864** do RNF-03 — **5,4% de
> folga**. A ~2,5 KiB gzip por patch, ela estoura em cerca de **33 patches**, pouco mais de
> um ano. O [ADR 0015](adr/0015-orcamento-do-indice-depois-da-segunda-fonte.md) subiu o teto
> do RNF-05 e **não** o do RNF-03 de propósito: este é o limite que o navegador paga, e a
> saída aqui não é subir o número.

**Entra**
- `champion` deixa de ser uma fatia e passa a ser N, fatiadas por **tipo** — os 6.994
  chromas são metade do peso e ninguém os abre por acaso (RF-06).
- O manifesto passa a declarar as fatias por `(category, type)`, e o `AssetsClient` carrega
  só a que o painel precisa.
- A guarda do `limits.py` continua valendo por fatia.

**NÃO entra**
- Subir o `SHARD_GZIP_LIMIT`. É exatamente o que este ticket existe para não fazer.
- Fatiar as outras categorias. `profile_icon` está em 336 KiB gzip, com folga de 4×.

**Critérios de aceite**
1. Nenhuma fatia passa de 1,5 MiB gzip no patch corrente.
2. Abrir o painel de um campeão carrega menos bytes do que hoje.
3. Revelar os chromas de uma skin carrega a fatia de chroma, e só então.
4. O contrato sobe de versão e o front antigo falha explicitamente, não em silêncio.

**Testes que provam**
- Teste de orçamento por fatia com o índice real.
- Teste de rede: abrir um campeão não busca a fatia de chroma.

---

# Onda 6 — componente opcional

### ✅ T-32 — API FastAPI

| | |
|---|---|
| **Objetivo** | Entregar a alternativa de back-end como peça de portfólio, sem que nada dependa dela |
| **Dependências** | T-10 |
| **Estimativa** | ~400 linhas |
| **Effort** | alto |
| **Cobre** | §7 da Spec, [ADR 0006](adr/0006-api-como-componente-opcional.md) |

> ✅ **Entregue em 09/09/2026**, com o escopo ajustado pelo
> [ADR 0012](adr/0012-onde-guardar-os-assets.md): **não há bucket para ler nem MinIO para
> simular**. O que existe é o diretório que o indexador escreve, e é dele que as rotas leem.
> O resto do ticket ficou de pé como estava.

**Entra**
- `/health` (já existia), `/versions`, `/index/{gameVersion}/{category}`, `POST /zip`.
- ~~Leitura do bucket~~ → leitura do **diretório do índice**, com cache invalidado por
  `mtime` do manifesto — barato de checar, e muda exatamente quando o arquivo muda. Um TTL
  teria a janela de erro embutida no número.
- `Dockerfile` e `docker-compose` para subir local, ~~com MinIO~~ **sozinha**: um contêiner
  que precisasse de outro para responder `/health` não seria opcional coisa nenhuma.
- Testes com `TestClient`.

**NÃO entra**
- Deploy em qualquer lugar. Roda local, por decisão de ADR.
- Qualquer alteração no front que passe a depender dela — isso é critério de revisão de PR.

**Critérios de aceite**
1. ✅ `docker compose up` sobe a API (~~+ MinIO~~) e `/health` responde — **verificado na
   CI**, não localmente: não há Docker nesta máquina, então o critério virou um job que roda
   o `compose up --wait` e faz `curl` no `/health` a cada PR que toca a API.
2. ✅ `/versions` devolve o mesmo conteúdo do `manifest.json`, campo por campo.
3. ✅ `POST /zip` com N ids devolve um zip com N arquivos; acima do limite devolve 413.
4. ✅ `grep` no `apps/web` não encontra nenhuma chamada à API.
5. ✅ Derrubar a API não afeta nenhum teste do front — ela nunca é iniciada por eles.

**Testes que provam**
- `TestClient` para cada endpoint, incluindo o 413 e o 503 de índice ausente.
- Teste de arquitetura: nenhuma referência à API no código do front, nem no `package.json`.
- e2e do front rodando com a API desligada (é como ele sempre roda).

> O `POST /zip` monta no servidor o que o T-25 monta no cliente, e existe para **mostrar o
> outro caminho**, não para ser usado: com o front zipando no navegador, uma API que baixa
> 500 arquivos por requisição seria a coisa mais cara do sistema.
>
> Ela reusa o `SourceClient` do indexador de propósito. A regra 4 do CLAUDE.md — User-Agent
> identificado, concorrência ≤ 4, backoff — é imposta por código, e ter duas implementações
> dela é ter uma que vai divergir.

---

# Pré-lançamento

### T-33 — Checklist de lançamento (D1, D2, D6, D7)

| | |
|---|---|
| **Objetivo** | Agrupar tudo que depende de decisão humana e que só importa no dia de tornar o site público |
| **Dependências** | T-27, T-30 |
| **Estimativa** | ~50 linhas |
| **Effort** | médio |
| **Cobre** | RF-21, RF-23, RNF-10, ADRs [0003](adr/0003-nome-publico-do-produto.md) e [0004](adr/0004-consentimento-da-wiki-e-teto-de-resolucao.md) |

> **Gatilho explícito:** este ticket só é executado quando o dono do projeto disser
> "vamos publicar". **Ele não bloqueia nenhuma onda anterior.** Até lá, o site roda em
> preview da Vercel, o que é uso privado e não dispara nenhuma obrigação da política da Riot.
>
> 🟡 **Parcialmente entregue em 10/09/2026.** O gatilho foi puxado e tudo que **não** depende
> de conta ou dinheiro do dono está feito, com teste: o D1 fechou, o checklist virou
> [`docs/LANCAMENTO.md`](LANCAMENTO.md), e há teste que impede marcador de decisão novo de
> entrar sem justificativa escrita.
>
> ✅ **D6, o texto, fechou no mesmo dia**, no segundo "vamos publicar". A comparação achou
> **duas** políticas que alcançam o site — o boilerplate das *General Policies* do Developer
> Portal e o aviso do *Legal Jibber Jabber* —, e os dois textos foram copiados das páginas e
> travados em teste. O `[A CONFIRMAR]` saiu e a lista de pendentes chegou a zero.
>
> **O que falta é só 🔑:**
>
> | | O que é |
> |---|---|
> | **D6** registro | Registrar "Biblioteca de Assets" no Developer Portal — passo a passo no checklist |
> | **D7** | Criar o projeto na Vercel como `biblioteca-de-assets` — sem domínio próprio, decidido pelo dono |
>
> O **D2** não está bloqueado, está **esperando**: se o consentimento da Weird Gloop chegar,
> é uma variável de ambiente — o crédito já está escrito e desligado.

**Entra**
- **D1** — nome público definido, sem "Riot", "League of Legends" nem "LoL"; trocado em
  `siteConfig.displayName`, que é o único lugar.
- **D6** — texto dos avisos legais copiado **literalmente** das políticas da Riot, e produto
  registrado no Developer Portal.
- **D7** — endereço público no ar, depois de D1. Em 10/09/2026 o dono decidiu publicar pela
  URL da Vercel, sem domínio próprio.
- **D2** — se o consentimento da Weird Gloop tiver chegado, ligar o crédito à wiki na
  página "Sobre" e registrar a evidência em `docs/SPIKES.md` com data. Se não tiver, a
  página diz que o teto de resolução é 1280×720.
- Checklist final: aviso visível, sem monetização, tier gratuito respeitado, `status.json`
  saudável.

**NÃO entra**
- Escrever o adaptador da wiki. Mesmo com consentimento, é ticket próprio, com spike S4
  antes.
- Qualquer forma de monetização — proibida pelo [ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md).

**Critérios de aceite**
1. ✅ `siteConfig.displayName` não é mais placeholder e passa na regra do ADR 0003.
2. ✅ Os avisos legais são idênticos aos textos oficiais — comparação registrada no PR, no
   checklist e em `docs/evidencias/politicas-da-riot-2026-09-10.md`.
3. 🔑 O produto aparece registrado no Developer Portal (print no PR).
4. 🔑 A URL de produção da Vercel resolve para o site. *Ajustado em 10/09/2026:* era "o
   domínio resolve"; o dono decidiu publicar sem domínio próprio, e o subdomínio segue a
   mesma regra de nome.
5. ✅ Nenhum marcador resta. O `[A DECIDIR]` do nome e o `[A CONFIRMAR]` do texto legal
   acabaram, e a lista de pendentes do teste está vazia.

**Testes que provam**
- Teste que falha se `displayName` for o placeholder, e que confere as três palavras
  proibidas.
- Teste que varre o código atrás de `[A DECIDIR]` e `[A CONFIRMAR]`. Ele **não** falha pelos
  marcadores que já existem — falha por marcador **novo** sem justificativa, e falha também
  se a lista de pendentes ficar desatualizada. Suíte vermelha por semanas é suíte que
  ninguém lê.
- Teste de que os avisos citados no checklist são os mesmos que o site publica, inteiros.
- Trava literal: os dois textos oficiais guardados no teste, e falha se o publicado diferir
  deles em qualquer coisa além do marcador de lugar.

---

### ⏳ T-40 — Densidade da grade

| | |
|---|---|
| **Objetivo** | Deixar quem quer ver mais cartões ver mais cartões |
| **Dependências** | T-30 |
| **Estimativa** | ~40 linhas |
| **Effort** | baixo |
| **Cobre** | — |

> Aberto em **10/09/2026**, na ingestão do design. O arquivo do Claude Design expõe uma
> propriedade `density` com dois valores — `densa` (alvo de 152px por cartão) e `confortável`
> (210px) — e **nenhum requisito pede isso**. O T-30 implementou só o denso, que é o padrão
> do design, e os dois valores já estão no tema como `--spacing-alvo-cartao-*`.

**Entra**
- Um controle na barra do título da grade que alterna entre as duas larguras-alvo.
- A escolha guardada no `localStorage` — é preferência de quem usa, não estado de sessão.

**NÃO entra**
- Uma terceira densidade. O design tem duas.
- Guardar em conta. Não há conta ([ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md)).

**Critérios de aceite**
1. Alternar muda o número de colunas na mesma largura de janela.
2. A escolha sobrevive a recarregar a página.
3. Sem `localStorage` disponível, o padrão é `densa` e nada quebra.

**Testes que provam**
- Vitest com as duas densidades na mesma largura, contando colunas.
- Teste com `localStorage` que lança, porque navegador em modo privado faz isso.

---

### ✅ T-41 — Navegação unificada na barra lateral

| | |
|---|---|
| **Objetivo** | Uma navegação só, como o design desenhou |
| **Dependências** | T-30 |
| **Estimativa** | ~150 linhas |
| **Effort** | médio |
| **Cobre** | RF-04, RF-08 |

> ✅ **Entregue em 10/09/2026**, no mesmo dia em que foi aberto: o dono viu a tela e pediu
> as categorias à esquerda. Elas estavam **abaixo de 173 cartões de campeão**, o que obrigava
> a rolar a grade inteira para chegar em "Itens" — o print que motivou o pedido mostra
> exatamente isso.
>
> O T-30 não tinha feito de propósito: o ticket dele diz "se o design pedir comportamento
> diferente, abre-se ticket novo; este só veste", e mudar a arquitetura de informação altera
> o que os testes do T-19 e do T-24 afirmam.

**Entra**
- A barra lateral passa a listar "Campeões" junto com as outras categorias, com contagem.
- A coluna principal mostra **uma** grade por vez.
- Os testes do T-19 e do T-24 são ajustados para a estrutura nova — este ticket **pode**
  alterá-los, com a justificativa no PR.

**NÃO entra**
- Mudar o que cada grade mostra. `champion` continua um cartão por campeão (RF-04) e a busca
  continua operando em skin ([ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md)).

**Critérios de aceite**
1. ✅ A barra lateral lista todas as categorias, "Campeões" inclusive e primeira.
2. ✅ Abrir uma categoria troca a grade; a home abre em "Campeões" (RF-04).
3. ✅ Nenhuma fatia é carregada antes do clique (RNF-03) — o e2e do T-29 continua valendo.
4. ✅ A barra de filtros quebra em linhas e a grade continua na tela.

**Testes que provam**
- Os do T-24, adaptados a um "palco" que reproduz o que a barra lateral faz, mais **5 testes
  novos da barra lateral de verdade**, montando o `Rodape` com provedor.
- O e2e do T-29, inalterado, mais dois cenários novos.

> **Um defeito que o e2e não pegava, e agora pega.** Ao trocar a grade por categoria, o
> scroller virtual passou a ficar dentro de um pai que também rolava — e um scroller virtual
> num pai que rola mede **altura zero** e desenha nada. A contagem ficava certa ("254 de
> 868"), os filtros funcionavam, e a lista vinha **vazia**, sem erro no console.
>
> A fixture do e2e tinha 3 itens, abaixo do limite de 200 que liga a virtualização — então o
> caminho quebrado nunca era exercitado. Agora tem **220**, e há teste que confere altura do
> scroller e contagem de cartões. É a segunda vez que esse defeito aparece; da terceira, ele
> falha vermelho.
>
> **A peça nova é um contexto de 40 linhas.** A barra lateral vive no `layout.tsx` — é o
> único caminho por onde toda página passa, e é por isso que o aviso do RF-21 mora lá — e a
> lista de categorias só existe depois que a página carrega o manifesto. Layout não recebe
> prop de página, então os dois falam por `navegacao-context.tsx`. Sem provedor, o padrão é
> vazio e o `Rodape` desenha só o resto — que é o que mantém o teste do T-27 passando sem
> saber que o contexto existe.

---

### ✅ T-42 — Publicação na Vercel

| | |
|---|---|
| **Objetivo** | O repositório pronto para a Vercel publicar sem configuração além do Root Directory |
| **Dependências** | T-33 |
| **Estimativa** | ~200 linhas |
| **Effort** | médio |
| **Cobre** | RNF-04, RNF-10, §9 da Spec, [ADR 0016](adr/0016-publicacao-na-vercel.md) |

> ✅ **Entregue em 10/09/2026**, aberto no mesmo dia pelo "vamos publicar" do dono: no ar
> para ele e alguns amigos, aberto por URL, sem senha, sem divulgação.

**Entra**
- `apps/web/vercel.json`: framework, e instalação e build com o pnpm do `packageManager` —
  sozinha, a Vercel só vai até o pnpm 10.
- Os cabeçalhos da §9 no `next.config.ts`, com o manifesto passando a revalidar sempre.
- `noindex` por padrão, desligável por variável.
- Build de produção na CI, e o servidor de produção conferido por um script que o dono também
  roda contra a URL publicada.
- Plano B desligado para o commit do bot: deploy hook por segredo opcional.
- README e checklist com o passo a passo.

**NÃO entra**
- Criar o projeto na Vercel — é conta do dono.
- Domínio próprio. O D7 decidiu publicar pela URL da Vercel.

**Critérios de aceite**
1. ✅ O `vercel.json` instala e builda com o pnpm do `packageManager`, e um teste segura os
   dois juntos.
2. ✅ O build de produção passa na CI.
3. ✅ Catálogo e fatias saem imutáveis; manifesto e status revalidam — conferido no servidor
   de produção, não só no config.
4. ✅ Toda resposta leva `X-Robots-Tag: noindex`, e o HTML leva `<meta name="robots">`,
   enquanto `NEXT_PUBLIC_SITE_INDEXABLE` não for `true`.
5. ✅ Nenhuma variável de ambiente é obrigatória.
6. 🔑 O site responde no domínio de produção — depende do dono criar o projeto.

**Testes que provam**
- `publicacao.test.ts`: `vercel.json` × `packageManager`; todo arquivo de `public/indice` cai
  em exatamente uma regra de cache; o hash do nome é o do conteúdo; `noindex` nos dois modos.
- A CI builda, sobe `next start` e roda `scripts/conferir-publicacao.mjs` contra ele.

---

### ✅ T-36 — Teto de versões guardadas no índice

> **Fechado em 08/09/2026 pela decisão, não pelo código.** Levantado durante o T-11, quando
> a execução mediu **4,4 MB por versão antiga** — 47 % acima dos ~3 MB que o ticket e o
> [ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md) estimavam.
>
> A pergunta era "guardar as N últimas, só as do ano, ou todas?". A resposta foi
> **N = 1**, registrada no [ADR 0013](adr/0013-uma-versao-por-vez-no-indice.md): 26 patches
> por ano a 4,4 MB são ~115 MB/ano que todo `git clone` paga para sempre, e o que se compra
> é histórico incompleto por construção — sem splash, sem loading, sem tile e sem runa
> nenhuma, porque essas URLs não são versionadas no ddragon.
>
> A implementação virou o **T-11**, que ficou mais simples do que se tivesse teto > 1: não
> há rotação a fazer, só a versão nova e a varredura do que sobrou.

---

### ✅ T-37 — O índice no histórico do Git

> **Fechado em 09/09/2026 pela medição, não pelo código.** Levantado no T-11 com um número
> meu que estava **errado por um fator de ~25**: eu disse ~275 MB/ano de histórico; medido
> em 78 patches simulados, são **~12 MiB/ano** e **28 MiB em três anos**. Eu tinha esquecido
> que o Git comprime o JSON (8,8×) e faz delta entre índices consecutivos (mais ~3×).
>
> O [ADR 0014](adr/0014-onde-vive-o-indice-gerado.md) compara cinco saídas com o custo de
> clone em 1, 3 e 10 anos. **Venceu a A: o índice fica no `main`.** Nenhuma alternativa
> compra o suficiente para pagar o que cobra — 28 MiB em três anos num repositório que hoje
> tem 0,65 MiB.
>
> O **branch órfão com force-push** fica registrado como plano B, com gatilho explícito:
> `.git` acima de 200 MiB, ou o `git clone` incomodando na prática. No ritmo medido, ~17
> anos.
>
> Nenhum código foi necessário: o T-13 já fazia o certo.

---

## Mapa de cobertura

Todo requisito da Spec tem pelo menos um ticket.

| Requisito | Tickets |
|---|---|
| RF-01, RF-02, RF-03, RF-07 | T-14 |
| RF-04, RF-25 | T-19 |
| RF-05, RF-24 | T-14 |
| RF-06 | T-20 |
| RF-08 | T-21, T-22, T-24 |
| RF-09, RF-12, RF-13, RF-14 | T-08, T-15 |
| RF-10, RF-11 | T-05, T-08 |
| RF-15 | T-19, T-29 |
| ~~RF-16~~ | ⏸️ T-23 suspenso — fora da v1 ([ADR 0012](adr/0012-onde-guardar-os-assets.md)) |
| RF-17, RF-18 | T-25 |
| ~~RF-19, RF-20~~ | fora da v1 ([ADR 0013](adr/0013-uma-versao-por-vez-no-indice.md)); ⏸️ T-26 suspenso |
| RF-21, RF-22 | T-27, T-33 |
| RF-23 | T-27, T-33 |
| RNF-01 | T-14, T-19, T-29 |
| RNF-02 | T-29 |
| RNF-03 | T-10, T-08, T-24 |
| RNF-04 | T-13, T-42 |
| RNF-05 | T-02, T-10, T-11, ✅ T-36, ✅ T-37 |
| RNF-13 | T-15 (aviso de divergência), T-09 (medição do sha256) |
| RNF-06 | T-12, T-13, T-31 |
| RNF-07 | T-08 |
| RNF-08, RNF-09 | T-03 |
| RNF-10 | T-27, T-33, T-42 |
| RNF-11 | T-28, T-30 |
| RNF-12 | CI, em todo ticket; **T-35** |

## Resumo das ondas

| Onda | Tickets | Paralelismo | Entrega |
|---|---|---|---|
| 0 | ✅ T-02 → T-01 | sequencial | **Concluída.** Orçamento fechado em 2,0 GB (20,1 % de 10 GB); protótipo removido |
| 1 | ✅ (T-03 ∥ T-04) → (T-05 ∥ T-06) → T-07; T-08 ∥ | 2 frentes | **Concluída.** Esqueleto andante: 1 campeão, 2 tipos, ponta a ponta — falta só publicar no R2 de verdade |
| 2 | ✅ T-09 → T-10 → T-11 → T-12 → T-13; ✅ T-14, T-15; 🚧 T-34 quando o design chegar | sequencial | **Concluída.** Patch inteiro indexado, com guarda, rotação, relatório, workflow, busca e painel |
| 3 | ✅ (T-16 → T-17); ✅ (T-19 → T-20); ✅ T-18 | sequencial | **Concluída.** Segunda fonte, fusão, grade, seletor de skin, chromas e contrato agendado |
| 4 | (T-21 ∥ T-22); (T-24 ∥ T-25) ∥ · ⏸️ T-23 e T-26 suspensos | 2 frentes | Catálogo inteiro e download em lote pelo cliente |
| 5 | (T-27 ∥ T-28 ∥ T-31) → T-29 → T-30 | 3 frentes | Produto fechado e vestido |
| 6 | T-32 | — | API opcional |
| — | 🟡 T-33 → ✅ T-42 | gatilho manual | Pré-lançamento e publicação na Vercel. O que resta do T-33 é conta do dono |
