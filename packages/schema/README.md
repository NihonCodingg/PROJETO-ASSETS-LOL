# @lol-assets/schema · lol-assets-schema

Contrato único do índice de assets, compartilhado por `apps/web`, `apps/api` e
`packages/indexer`. É a **única** coisa que os três compartilham.

| Caminho | Papel |
|---|---|
| `schemas/index-manifest.schema.json` | O `manifest.json` — único arquivo de nome fixo no bucket |
| `schemas/catalog.schema.json` | Navegação (173 campeões) e busca (2.149 skins), sem asset |
| `schemas/index-shard.schema.json` | Uma fatia de assets por categoria e versão (`$defs.asset`), carregada sob demanda |
| `data/champion-aliases.json` | Apelidos de busca, mantidos à mão |
| `examples/` | Fixture do contrato — retrato medido do patch 16.17.1 |
| `src/lol_assets_schema/models.py` | Modelos Pydantic, com as regras dos ADRs |
| `src/lol_assets_schema/validators.py` | Validação contra o JSON Schema |
| `src-ts/` | Tipos TypeScript e a fixture exportada para o front |
| `src/lol_assets_schema/` | Caminhos do contrato e `SCHEMA_VERSION` para o lado Python |

Contrato atual: **1.1.0**. Qualquer mudança exige um ADR em `docs/adr/` e uma versão nova
(KICKOFF §0.3).

## Navegação e busca operam em níveis diferentes

O `catalog` carrega as **duas** projeções, e nenhum asset:

- `champions[]` — 173 entradas. É a grade padrão do site.
- `skins[]` — 2.149 entradas. É o índice de busca, e é o que faz `"K/DA"` e `"Prestígio"`
  retornarem skins de vários campeões sem nenhum campo extra: os nomes das skins já os
  contêm.

As fatias de asset vêm **depois**, sob demanda. Ver
[ADR 0010](../../docs/adr/0010-navegacao-por-campeao-busca-por-skin.md).

## Três regras que o schema impõe, não só documenta

- `hasAlpha: true` obriga `format: "png"`. JPEG não carrega canal alfa
  ([ADR 0001](../../docs/adr/0001-formato-de-entrega-dos-assets.md) regra 4).
- Cortes de splash exigem `skinId` e `skinNum`.
- Toda skin do catálogo exige `championKey` — sem ela não dá para rotular o resultado de
  busca com o campeão de origem.

As três têm teste em `tests/test_schema_contract.py`, cada uma com um caso negativo.

## Apelidos de busca

`data/champion-aliases.json` mapeia o que a pessoa digita (já normalizado: minúsculo, sem
acento, sem apóstrofo) para o `id` interno do campeão no Data Dragon.

**Ampliar a lista é editar o arquivo.** Não há gerador, não há script, não é preciso rodar
o indexador: o `apps/web` importa o arquivo em tempo de build, então um merge na `main`
publica o apelido novo no próximo deploy
([ADR 0009](../../docs/adr/0009-apelidos-de-busca-mantidos-a-mao.md)).

Só vale registrar o que a normalização sozinha não acha — `kaisa` já encontra Kai'Sa sem
apelido; `mf` não encontra Miss Fortune.
