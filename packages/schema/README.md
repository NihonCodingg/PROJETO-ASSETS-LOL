# @lol-assets/schema · lol-assets-schema

Contrato único do índice de assets, compartilhado por `apps/web`, `apps/api` e
`packages/indexer`. É a **única** coisa que os três compartilham.

| Caminho | Papel |
|---|---|
| `schemas/index-manifest.schema.json` | O `manifest.json` — único arquivo de nome fixo no bucket |
| `schemas/index-shard.schema.json` | Uma fatia do índice por categoria e versão (`$defs.asset`) |
| `data/champion-aliases.json` | Apelidos de busca, mantidos à mão |
| `src-ts/` | Tipos TypeScript (escritos à mão hoje; gerados em ticket futuro) |
| `src/lol_assets_schema/` | Caminhos do contrato e `SCHEMA_VERSION` para o lado Python |

Contrato atual: **1.0.0**. Qualquer mudança exige um ADR em `docs/adr/` e uma versão nova
(KICKOFF §0.3).

## Duas regras que o schema impõe, não só documenta

- `hasAlpha: true` obriga `format: "png"`. JPEG não carrega canal alfa
  ([ADR 0001](../../docs/adr/0001-formato-de-entrega-dos-assets.md) regra 4).
- Cortes de splash exigem `skinId` e `skinNum`.

Ambas têm teste em `tests/test_schema_contract.py`, incluindo um teste negativo.

## Apelidos de busca

`data/champion-aliases.json` mapeia o que a pessoa digita (já normalizado: minúsculo, sem
acento, sem apóstrofo) para o `id` interno do campeão no Data Dragon.

**Ampliar a lista é editar o arquivo.** Não há gerador, não há script, não é preciso rodar
o indexador: o `apps/web` importa o arquivo em tempo de build, então um merge na `main`
publica o apelido novo no próximo deploy
([ADR 0009](../../docs/adr/0009-apelidos-de-busca-mantidos-a-mao.md)).

Só vale registrar o que a normalização sozinha não acha — `kaisa` já encontra Kai'Sa sem
apelido; `mf` não encontra Miss Fortune.
