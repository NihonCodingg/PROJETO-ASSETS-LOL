# lol-assets

Catálogo de assets visuais de League of Legends na melhor fonte disponível,
servidos sem re-encode e com PNG gerado no navegador sob demanda — pensado para
editores de vídeo e thumbnail que precisam do arquivo agora, sem login e sem
navegar por wiki.

> Status: **etapa 5 das 7** (tickets escritos, aguardando aprovação). Ainda não há
> produto rodando. A fonte de verdade é [`docs/SPEC.md`](docs/SPEC.md), quebrada em
> [`docs/TICKETS.md`](docs/TICKETS.md) e apoiada pelos [ADRs](docs/adr/README.md) e
> pelos números de [`docs/SPIKES.md`](docs/SPIKES.md).
> O [`docs/KICKOFF.md`](docs/KICKOFF.md) guarda a ideia e a pesquisa originais.

Uso pessoal e de um pequeno grupo, sem monetização, **custo de operação zero**:
Vercel Hobby + Cloudflare R2 (tier gratuito) + GitHub Actions. Nada no caminho do
usuário depende de um servidor nosso.

## Estrutura

```
apps/web/          front-end Next.js (Vercel)
apps/api/          API FastAPI — opcional, fora do caminho crítico (ADR 0006)
packages/indexer/  adaptadores de fonte, fusão, nomeação e publicação
packages/schema/   contrato do índice (JSON Schema + tipos TS) e apelidos de busca
docs/              kickoff, spikes, spec, tickets, ADRs, evidências e sessões
```

## Como rodar

Pré-requisitos: Node 22+, [pnpm](https://pnpm.io) 11+, Python 3.12+ e
[uv](https://docs.astral.sh/uv/).

```bash
pnpm install
uv sync --all-packages
cp .env.example .env
```

Se o `uv` não estiver no PATH (é o caso quando foi instalado com `pip install uv`),
troque `uv` por `python -m uv` em todos os comandos.

**Regra no Windows: o caminho do repositório não pode ter caractere não-ASCII.**
Com acento, o `pnpm install` falha com `ERR_PNPM_EPERM` nos pacotes de binário nativo
(`esbuild`, `unrs-resolver`). Mantenha em um caminho como `D:\PROJETOS\PROJETO-ASSETS-LOL`.
Detalhes em [`docs/SPIKES.md`](docs/SPIKES.md).

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
