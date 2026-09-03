# @lol-assets/schema · lol-assets-schema

Contrato único do índice de assets, compartilhado por `apps/web`, `apps/api` e
`packages/indexer`. É a **única** coisa que os três compartilham.

| Caminho | Papel |
|---|---|
| `schemas/` | JSON Schema do índice — fonte de verdade |
| `src-ts/` | Tipos TypeScript gerados a partir do schema |
| `src/lol_assets_schema/` | Modelos Pydantic gerados a partir do schema |

O schema completo chega com a Spec (etapa 4). Qualquer mudança nele exige um
ADR em `docs/adr/` e uma nova versão de `SCHEMA_VERSION` (KICKOFF §0.3).
