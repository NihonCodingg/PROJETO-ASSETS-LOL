# TICKETS v1

> Etapa 5. Quebra de [`SPEC.md`](SPEC.md) em unidades executáveis, uma por sessão.
> Cada ticket cabe em **≤ 500 linhas de lógica** (exclui lockfiles, fixtures e snapshots).
> Se não couber, divide-se o ticket — nunca se infla o PR (regra 5 do [CLAUDE.md](../CLAUDE.md)).
>
> Data: 03/09/2026 · 33 tickets · 7 ondas
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

### T-03 — Cliente HTTP com a etiqueta de rede

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

### T-04 — Contrato em código: modelos, validação e fixture

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

### T-05 — Adaptador ddragon mínimo: um campeão, dois tipos

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

### T-06 — Publicador no R2 com manifesto atômico

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

### T-07 — CLI do indexador ligando as pontas

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

### T-08 — Front: carregar o índice, listar e baixar um asset

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

### T-09 — Adaptador ddragon completo pelo tarball

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

### T-10 — Fatiamento do índice e guarda de orçamento

| | |
|---|---|
| **Objetivo** | Projetar o catálogo completo, manter a carga inicial enxuta e impedir que uma publicação estoure os 10 GB |
| **Dependências** | T-09 |
| **Estimativa** | ~280 linhas |
| **Effort** | médio |
| **Cobre** | RNF-03, RNF-05, §6.1 da Spec, [ADR 0010](adr/0010-navegacao-por-campeao-busca-por-skin.md) |

**Entra**
- Escalar a projeção do catálogo de T-07 para o catálogo inteiro: **173 campeões** em
  `champions[]` (com `skinCount`, `chromaCount`, `baseSkinId` e miniatura) e **2.149 skins**
  em `skins[]`.
- Fatiar o índice de assets por categoria, com hash no nome.
- Calcular o tamanho comprimido e **falhar** se o catálogo passar de **150 KB** ou se a
  fatia `champion` passar de 1,5 MB (RNF-03).
- Somar os bytes projetados e **abortar antes de publicar** se passar de 8 GB, com
  mensagem dizendo qual categoria é a maior.
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
3. Total projetado acima de 8 GB → aborta **antes** de qualquer upload.
4. O manifesto lista o catálogo e todas as fatias, e os totais batem com a soma delas.

**Testes que provam**
- Unitários com índices sintéticos nos dois lados de cada limite.
- Teste de que o publicador não é chamado quando o orçamento estoura.

---

### T-11 — Rotação de versão: publicar novo, remover anterior

| | |
|---|---|
| **Objetivo** | Manter o bucket em uma versão de assets sem nunca deixar o site sem arquivo |
| **Dependências** | T-06 |
| **Estimativa** | ~150 linhas |
| **Effort** | médio |
| **Cobre** | RF-19, RF-20, RNF-05, [ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md) |

**Entra**
- Depois do manifesto novo publicado **e relido com sucesso**, remover os assets da versão
  anterior, mantendo as fatias de índice dela.
- Marcar `assetsCopied: false` na versão que perdeu os assets e remover do índice dela os
  tipos não versionados (`splash_*`, `loading`, `tile`) — eles deixam de existir (RF-20).
- Modo `--keep-previous` para depuração.

**NÃO entra**
- Apagar índice antigo. Índice acumula; é barato e é o histórico.
- Recuperar splash histórico. É impossível por esta arquitetura, e a Spec diz isso.

**Critérios de aceite**
1. A remoção só roda depois de o manifesto novo ser lido de volta do bucket com sucesso.
2. Falha na releitura → nada é removido e o comando sai ≠ 0.
3. A versão anterior fica com `assetsCopied: false` e sem os tipos não versionados.
4. As fatias de índice da versão anterior continuam acessíveis.
5. Nunca há um instante em que o manifesto aponte para asset já removido.

**Testes que provam**
- Teste de ordem com S3 falso: releitura falhando prova que nada foi apagado.
- Teste que percorre o manifesto resultante e confirma que toda URL referenciada existe.
- Teste do filtro de tipos não versionados.

---

### T-12 — Observabilidade: `status.json`, resumo do job e issue automática

| | |
|---|---|
| **Objetivo** | Fazer a indexação falhar alto, já que não há processo para monitorar |
| **Dependências** | T-07 |
| **Estimativa** | ~180 linhas |
| **Effort** | médio |
| **Cobre** | §11 da Spec, RNF-06 |

**Entra**
- `status.json` publicado a cada execução: versão, duração, assets por fonte, bytes
  publicados, falhas por tipo, dimensões inesperadas.
- Resumo no `$GITHUB_STEP_SUMMARY` com a mesma tabela.
- Abertura automática de issue em falha, com o log anexado e rótulo `indexacao`.
- Log estruturado JSON consolidado.

**NÃO entra**
- Métrica de tráfego do site. Não há servidor e não vamos instrumentar o navegador.
- Serviço externo de alerta. Issue no repositório é o canal.

**Critérios de aceite**
1. `status.json` valida contra um schema próprio e é publicado mesmo quando a indexação falha.
2. O resumo do job aparece na aba do Actions sem precisar abrir o log.
3. Falha simulada abre exatamente uma issue, sem duplicar em reexecução do mesmo commit.
4. Nenhum segredo aparece no log nem na issue.

**Testes que provam**
- Unitários da montagem do `status.json` e do markdown do resumo.
- Teste de idempotência da abertura de issue (mesmo `run_id` não duplica).
- Teste de redação de segredo: variáveis sensíveis nunca são serializadas.

---

### T-13 — Workflow agendado de indexação

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
- Segredos do R2 vindos de secrets do repositório.
- `concurrency` para nunca ter duas indexações ao mesmo tempo.
- `timeout-minutes` compatível com o download de 2,39 GB.

**NÃO entra**
- Deploy do front. É a Vercel que faz, no push.
- Reindexar versões antigas. Um caminho manual basta.

**Critérios de aceite**
1. Sem versão nova, o job sai em menos de 1 minuto e não publica nada.
2. Duas execuções simultâneas não acontecem (`concurrency` prova).
3. Os segredos não aparecem em log.
4. Uma execução manual publica e o site passa a servir a versão nova.

**Testes que provam**
- `act` ou execução real em branch com bucket de teste.
- Teste unitário do comparador de versão (o que decide sair cedo).

---

### T-14 — Front: busca com normalização e apelidos

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
- Índice de busca sobre **`catalog.skins[]` (2.149) e `catalog.champions[]` (173)**,
  montado uma vez, na carga do catálogo.
- **Duas classes de resultado.** Campeão casado vira **uma** entrada de campeão, nunca 18
  de skin. Skin casada vira entrada de skin, rotulada com o campeão de origem.
- Ranqueamento: casamento exato de campeão > casamento exato de skin > prefixo > substring.
- Foco automático no campo e atalho `/` sem inserir o caractere.

**NÃO entra**
- Fuse.js. Fica como segunda camada só se aparecer caso real de zero resultado (ticket novo).
- Busca por tag ou filtro (T-24).
- Decisão visual — ver a nota no topo.

**Critérios de aceite**
1. `kaisa`→Kai'Sa, `belveth`→Bel'Veth, `chogath`→Cho'Gath, `KAI'SA`→Kai'Sa, em 1º lugar.
2. `mf`, `tf`, `j4`, `asol` resolvem pelo arquivo de apelidos, em 1º lugar.
2b. `jax` retorna **uma** entrada de campeão, não 18 de skin (RF-05).
2c. `kda` e `prestigio` retornam skins de **≥ 3 campeões distintos**, cada uma rotulada com
   o campeão de origem (RF-24).
3. `/` foca o campo e o valor não muda.
4. Com 173 campeões e 2.149 skins no índice, a busca responde em < 50 ms (medido).
5. Acrescentar uma linha ao JSON de apelidos passa a valer sem tocar em código.

**Testes que provam**
- Vitest com tabela de ≥ 20 pares consulta→esperado, incluindo os quatro apelidos citados,
  o caso `jax` (uma entrada) e os casos transversais `kda` e `prestigio`.
- Teste de performance com o catálogo completo sintético (173 + 2.149).
- Teste que adiciona um apelido à fixture e confirma que passa a resolver.

---

### T-15 — Front: painel de asset completo

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

### T-16 — Adaptador cdragon

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

### T-17 — Fusão de fontes

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

### T-18 — Testes de contrato das fontes (agendados)

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

### T-19 — Front: grade de campeões e painel com seletor de skin

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

**Testes que provam**
- Vitest com catálogo de fixture completo: contagem da grade, atalho da busca para a skin
  certa, troca de skin, ausência de chroma.
- Teste que conta cliques dos quatro caminhos e falha em > 3.

---

### T-20 — Front: chromas atrás de toggle

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

**Execução: (T-21 ∥ T-22) → T-23**, com **(T-24 ∥ T-25 ∥ T-26)** em paralelo.

### T-21 — Indexar as categorias não-campeão do ddragon

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

### T-22 — Indexar emotes, ward skins e emblemas de elo

| | |
|---|---|
| **Objetivo** | Fechar o catálogo com o que só existe fora do tarball |
| **Dependências** | T-16, T-02 |
| **Estimativa** | ~250 linhas |
| **Effort** | médio |
| **Cobre** | RF-08, §A.3 do KICKOFF, §B.4 |

**Entra**
- Emotes (2.347) e ward skins (265) pelo cdragon, partindo dos JSONs `v1/`.
- Emblemas de elo pelo zip oficial da Riot em `static.developer.riotgames.com`
  (`source: "riot_static"`), com nome `Rank_{tier}_{divisão}.png`.
- Respeitar o orçamento medido em T-02.

**NÃO entra**
- Assets da wiki. Bloqueado pelo [ADR 0004](adr/0004-consentimento-da-wiki-e-teto-de-resolucao.md).
- Ícones de posição e moedas — v2.

**Critérios de aceite**
1. As três categorias aparecem no manifesto com contagem conferida.
2. Emblemas de elo vêm do zip oficial, não do cdragon, e o `source` diz isso.
3. O total de bytes bate com o projetado em T-02, com margem de 15 %.
4. Nenhuma requisição à wiki.

**Testes que provam**
- Unitários com fixture dos JSONs e um zip de fixture.
- Teste do nome de arquivo de elo.
- Teste de que o total medido não diverge do projetado além da margem.

---

### T-23 — Zips por categoria pré-gerados

| | |
|---|---|
| **Objetivo** | Entregar "todos os ícones de item" sem o navegador baixar 868 arquivos |
| **Dependências** | T-21, T-22 |
| **Estimativa** | ~180 linhas |
| **Effort** | médio |
| **Cobre** | RF-16, [ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md) |

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

### T-24 — Front: navegação por categoria e filtros

| | |
|---|---|
| **Objetivo** | Dar um caminho para quem não sabe o nome do que procura |
| **Dependências** | T-21, T-22 |
| **Estimativa** | ~280 linhas |
| **Effort** | alto |
| **Cobre** | RF-08, RNF-03 |

**Entra**
- Navegação por categoria, carregando a fatia sob demanda (a home só carrega `champion`).
- Filtros por função, lane, comprável, mapa, árvore de runa e elo, a partir das `tags`.
- Combinação de filtro com busca.

**NÃO entra**
- Filtro salvo entre sessões. Sem back-end e sem conta.
- Decisão visual — ver a nota no topo.

**Critérios de aceite**
1. Abrir uma categoria carrega só a fatia dela.
2. Cada filtro reduz a lista corretamente, e combinados também.
3. A fatia `champion` continua sendo a única carregada na home (RNF-03).
4. Filtro sem resultado mostra estado vazio com o que foi filtrado.

**Testes que provam**
- Vitest com fixture multicategoria: carga sob demanda, cada filtro, combinações, vazio.
- Teste de rede que confirma que só uma fatia é buscada na home.

---

### T-25 — Front: seleção múltipla e zip no cliente

| | |
|---|---|
| **Objetivo** | "Tudo do Jax" e seleção livre, sem servidor |
| **Dependências** | T-19 |
| **Estimativa** | ~200 linhas |
| **Effort** | médio |
| **Cobre** | RF-17, RF-18, [ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md) |

**Entra**
- Selecionar vários assets e baixar como zip montado com JSZip.
- Ação "tudo deste campeão" que pré-monta a seleção.
- Acima de 300 arquivos ou 500 MB, recomendar o zip por categoria — **recomendação, não
  bloqueio**.
- Progresso durante a montagem.

**NÃO entra**
- Conversão PNG em lote. Fica para v2 se alguém pedir.
- Qualquer chamada a servidor próprio.

**Critérios de aceite**
1. Selecionar N assets e baixar produz um zip com N arquivos, com os `fileName` corretos.
2. Nenhuma requisição a servidor próprio durante a montagem.
3. Acima do limite, aparece a recomendação e ainda assim é possível prosseguir.
4. "Tudo do Jax" seleciona todos os assets do campeão, chromas incluídos se revelados.

**Testes que provam**
- Vitest montando um zip de fixture e lendo de volta a lista de nomes.
- Teste do limite (aparece a recomendação, o botão continua habilitado).
- Teste de rede confirmando ausência de chamada a servidor próprio.

---

### T-26 — Front: seletor de versão e modo histórico honesto

| | |
|---|---|
| **Objetivo** | Permitir patch antigo sem mentir sobre o que existe |
| **Dependências** | T-11 |
| **Estimativa** | ~200 linhas |
| **Effort** | médio |
| **Cobre** | RF-19, RF-20, [ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md) |

**Entra**
- Seletor de versão a partir do manifesto, com `currentVersion` como padrão.
- Em versão com `assetsCopied: false`, usar `sourceUrl` e mostrar só os tipos versionados.
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

### T-27 — Página "Sobre", créditos e rodapé legal

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
1. O aviso legal aparece em toda página.
2. A página cita todas as fontes efetivamente usadas.
3. O crédito à wiki não aparece enquanto o consentimento não existir.
4. O nome exibido continua passando na regra do [ADR 0003](adr/0003-nome-publico-do-produto.md).

**Testes que provam**
- Vitest: presença do aviso, ausência do bloco da wiki com a flag desligada, regra do nome.

---

### T-28 — Acessibilidade

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
1. Todo o fluxo J1 é possível só com teclado.
2. axe não reporta violação crítica nem séria.
3. Toda `img` tem `alt` não vazio.
4. O foco é visível em todo elemento interativo.

**Testes que provam**
- axe no Playwright em home, painel e categoria.
- Teste de percurso por teclado do fluxo completo.

---

### T-29 — e2e do fluxo completo

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
1. J1 e J2 completam em ≤ 3 cliques; o teste falha em 4.
2. O arquivo baixado tem o `fileName` esperado e o MIME correto.
3. O PNG convertido tem as mesmas dimensões do original.
4. Busca responde em < 50 ms e a prévia abre em < 1 s.
5. O job roda em todo PR.

**Testes que provam**
- Os próprios cenários Playwright.

---

### T-30 — Integrar o design aprovado

| | |
|---|---|
| **Objetivo** | Aplicar o desenho feito no Claude Design sobre o comportamento já testado |
| **Dependências** | T-27, T-28, T-29 |
| **Estimativa** | ~300 linhas |
| **Effort** | médio |
| **Cobre** | §A.4 do KICKOFF, RNF-11 |

**Entra**
- Tokens de espaçamento, cor e tipografia a partir do design.
- Aplicação nos componentes já existentes, **sem mudar comportamento**.
- Verificação de contraste sobre a paleta escolhida.
- Ajuste de responsividade.

**NÃO entra**
- Mudar comportamento ou critério de aceite de ticket anterior. Se o design pedir
  comportamento diferente, **abre-se ticket novo** — este só veste.

**Critérios de aceite**
1. Todos os testes das ondas anteriores continuam passando, sem alteração.
2. axe continua sem violação crítica nem séria com a paleta nova.
3. O layout funciona em telas estreitas.
4. Nenhum valor de cor ou espaçamento fica solto no componente; tudo vem de token.

**Testes que provam**
- A suíte inteira, inalterada — é essa a prova de que só a aparência mudou.
- axe com a paleta nova.
- Teste de contraste dos pares de token.

---

### T-31 — Aviso de índice velho

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
1. Manifesto com 71 h → sem aviso. Com 73 h → aviso.
2. O aviso mostra a data.
3. O site continua plenamente funcional com o aviso na tela.

**Testes que provam**
- Vitest com relógio fake nos dois lados do limite.

---

# Onda 6 — componente opcional

### T-32 — API FastAPI

| | |
|---|---|
| **Objetivo** | Entregar a alternativa de back-end como peça de portfólio, sem que nada dependa dela |
| **Dependências** | T-10 |
| **Estimativa** | ~400 linhas |
| **Effort** | alto |
| **Cobre** | §7 da Spec, [ADR 0006](adr/0006-api-como-componente-opcional.md) |

**Entra**
- `/health` (já existe), `/versions`, `/index/{gameVersion}/{category}`, `POST /zip`.
- Leitura do bucket, com cache em memória.
- `Dockerfile` e `docker-compose` para subir local com MinIO.
- Testes com `TestClient`.

**NÃO entra**
- Deploy em qualquer lugar. Roda local, por decisão de ADR.
- Qualquer alteração no front que passe a depender dela — isso é critério de revisão de PR.

**Critérios de aceite**
1. `docker compose up` sobe API + MinIO e `/health` responde.
2. `/versions` devolve o mesmo conteúdo do `manifest.json`.
3. `POST /zip` com N ids devolve um zip com N arquivos; acima do limite devolve 413.
4. `grep` no `apps/web` não encontra nenhuma chamada à API.
5. Derrubar a API não afeta nenhum teste do front.

**Testes que provam**
- `TestClient` para cada endpoint, incluindo o 413.
- Teste de arquitetura: nenhuma referência à API no código do front.
- e2e do front rodando com a API desligada.

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
> preview da Vercel com o nome de trabalho, o que é uso privado e não dispara nenhuma
> obrigação da política da Riot.

**Entra**
- **D1** — nome público definido, sem "Riot", "League of Legends" nem "LoL"; trocado em
  `siteConfig.displayName`, que é o único lugar.
- **D6** — texto do aviso legal copiado **literalmente** da Developer API Policy, e produto
  registrado no Developer Portal.
- **D7** — domínio contratado e apontado, depois de D1.
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
1. `siteConfig.displayName` não é mais placeholder e passa na regra do ADR 0003.
2. O aviso legal é idêntico ao texto oficial (comparação manual registrada no PR).
3. O produto aparece registrado no Developer Portal (print no PR).
4. O domínio resolve para o site.
5. Nenhum marcador `[A DECIDIR]` ou `[A CONFIRMAR]` resta no código.

**Testes que provam**
- Teste que falha se `displayName` for o placeholder.
- Teste que varre o código atrás de `[A DECIDIR]` e `[A CONFIRMAR]` e falha se achar.

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
| RF-16 | T-23 |
| RF-17, RF-18 | T-25 |
| RF-19, RF-20 | T-11, T-26 |
| RF-21, RF-22 | T-27, T-33 |
| RF-23 | T-27, T-33 |
| RNF-01 | T-14, T-19, T-29 |
| RNF-02 | T-29 |
| RNF-03 | T-10, T-08, T-24 |
| RNF-04 | T-13 |
| RNF-05 | T-02, T-10, T-23 |
| RNF-06 | T-12, T-13, T-31 |
| RNF-07 | T-08 |
| RNF-08, RNF-09 | T-03 |
| RNF-10 | T-27, T-33 |
| RNF-11 | T-28, T-30 |
| RNF-12 | CI, em todo ticket |

## Resumo das ondas

| Onda | Tickets | Paralelismo | Entrega |
|---|---|---|---|
| 0 | ✅ T-02 → T-01 | sequencial | **Concluída.** Orçamento fechado em 2,0 GB (20,1 % de 10 GB); protótipo removido |
| 1 | (T-03 ∥ T-04) → (T-05 ∥ T-06) → T-07; T-08 ∥ | 2 frentes | **Esqueleto andante**: 1 campeão, 2 tipos, ponta a ponta |
| 2 | T-09 → (T-10 ∥ T-11 ∥ T-12) → T-13; (T-14 ∥ T-15) ∥ | 2 frentes | Catálogo de campeões completo e automático |
| 3 | (T-16 → T-17) ∥ (T-19 → T-20); T-18 ao final | 2 frentes | Grade de campeões, seletor de skin, chromas e a segunda fonte |
| 4 | (T-21 ∥ T-22) → T-23; (T-24 ∥ T-25 ∥ T-26) ∥ | 2 frentes | Catálogo inteiro e download em lote |
| 5 | (T-27 ∥ T-28 ∥ T-31) → T-29 → T-30 | 3 frentes | Produto fechado e vestido |
| 6 | T-32 | — | API opcional |
| — | T-33 | gatilho manual | Pré-lançamento |
