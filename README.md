# lol-assets

Catálogo público de assets visuais de League of Legends em PNG, na melhor
resolução disponível — pensado para editores de vídeo e thumbnail que precisam
do arquivo agora, sem login e sem navegar por wiki.

> Status: **etapa 3 das 7** (protótipo + spikes). Ainda não há produto rodando.
> A fonte de verdade do projeto é [`docs/KICKOFF.md`](docs/KICKOFF.md).

## Estrutura

```
apps/web/          front-end Next.js (Vercel)
apps/api/          API FastAPI (zips sob demanda, índice, metadados)
packages/indexer/  adaptadores de fonte, fusão, conversão e publicação
packages/schema/   contrato do índice (JSON Schema + tipos TS + Pydantic)
prototype/         descartável — apagado no primeiro ticket da etapa 6
docs/              kickoff, spikes, spec, tickets, ADRs e relatórios de sessão
```

## Como rodar

Pré-requisitos: Node 22+, [pnpm](https://pnpm.io) 11+, Python 3.12+ e
[uv](https://docs.astral.sh/uv/).

```bash
pnpm install
uv sync --all-packages
cp .env.example .env
```

Qualidade (é o que a CI roda):

```bash
pnpm -r --if-present lint typecheck test
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

## Fontes dos assets

Data Dragon e Community Dragon. A League of Legends Wiki **não** é acessada de
forma automatizada: os Termos de Uso da Weird Gloop exigem consentimento prévio,
que ainda não foi solicitado (KICKOFF §B.3.2).

## Legal

Projeto não oficial, sem vínculo com a Riot Games. O aviso legal exigido pela
Developer API Policy fica visível no rodapé do site.
