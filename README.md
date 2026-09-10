# lol-assets

Catálogo de assets visuais de League of Legends na melhor fonte disponível,
servidos sem re-encode e com PNG gerado no navegador sob demanda — pensado para
editores de vídeo e thumbnail que precisam do arquivo agora, sem login e sem
navegar por wiki.

> **Estado (10/09/2026):** o site está completo para o patch **16.18.1** — 173 campeões,
> 2.121 skins e 27.283 assets, com busca, navegação por categoria, seleção múltipla e zip
> no navegador. Dos 31 tickets, dois ficaram suspensos de propósito: zips pré-gerados
> (T-23) e o modo histórico de versões (T-26). A fonte de verdade é
> [`docs/SPEC.md`](docs/SPEC.md), quebrada em [`docs/TICKETS.md`](docs/TICKETS.md) e
> apoiada pelos [ADRs](docs/adr/README.md) e pelos números de
> [`docs/SPIKES.md`](docs/SPIKES.md). O [`docs/KICKOFF.md`](docs/KICKOFF.md) guarda a
> ideia e a pesquisa originais.

Uso pessoal e de um pequeno grupo, sem monetização, **custo de operação zero**:
Vercel Hobby + GitHub Actions, e **nenhum serviço de armazenamento**. O índice é
estático e aponta para as URLs das fontes; o navegador busca de lá
([ADR 0012](docs/adr/0012-onde-guardar-os-assets.md)). Nada no caminho do usuário
depende de um servidor nosso.

## Abrir o site local

**Um comando.** O índice está versionado no repositório desde o
[ADR 0014](docs/adr/0014-onde-vive-o-indice-gerado.md), então um clone já vem com tudo o que
o site precisa:

```bash
pnpm -C apps/web dev
```

E abrir <http://localhost:3000>.

O que você vê: **173 campeões, 2.121 skins e 27.283 assets** do patch 16.18.1, com as
categorias na barra da esquerda. As imagens vêm direto do ddragon e do cdragon — o
repositório guarda o índice (~19 MB de JSON), nunca os arquivos
([ADR 0012](docs/adr/0012-onde-guardar-os-assets.md)).

> Se a página abrir dizendo "Falhou ao carregar o catálogo", o índice sumiu do seu clone.
> `git checkout -- apps/web/public/indice` traz de volta.

## Como o índice chega ao site

Um workflow do GitHub Actions roda por patch, indexa o ddragon e o cdragon, escreve
~19 MB de JSON em `apps/web/public/indice/` e commita — o `manifest.json` por último,
para o site nunca ver um índice pela metade ([ADR 0014](docs/adr/0014-onde-vive-o-indice-gerado.md)).
O deploy da Vercel publica o commit. Não há storage, não há servidor no caminho do
usuário: as imagens vêm das URLs das fontes, que têm CORS aberto
([ADR 0012](docs/adr/0012-onde-guardar-os-assets.md)).

## Estrutura

```
apps/web/          front-end Next.js (Vercel)
apps/api/          API FastAPI — opcional, fora do caminho crítico (ADR 0006)
packages/indexer/  adaptadores de fonte, fusão, nomeação e publicação
packages/schema/   contrato do índice (JSON Schema + tipos TS) e apelidos de busca
docs/              kickoff, spikes, spec, tickets, ADRs, evidências e sessões
```

## Desenvolver

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
(`esbuild`, `unrs-resolver`). Mantenha em um caminho como `D:\PROJETOS\lol-assets`.
Detalhes em [`docs/SPIKES.md`](docs/SPIKES.md).

Qualidade (é o que a CI roda):

```bash
pnpm -r --if-present lint typecheck test
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

### Gerar o índice você mesmo

Só é preciso para trabalhar **no indexador** — o site não depende disso.

```bash
uv run lol-assets-indexer index
```

Ele **baixa o `dragontail` do patch atual: 2,39 GB**. Na CI leva ~105 s; numa conexão
doméstica, bem mais. Mede 15.559 imagens, busca o que só o cdragon tem, e escreve ~19 MB de
JSON em `apps/web/public/indice/`.

**`--dry-run` não serve para isto.** Ele mede e valida **sem escrever nada** — é ensaio, não
geração.

Depois de rodar, o `git status` vai mostrar o índice alterado. **Descarte:** quem o commita é
o workflow, não você.

```bash
git checkout -- apps/web/public/indice
```

Se você já tem o tarball em disco, pule o download:

```bash
uv run lol-assets-indexer index --tarball caminho/para/dragontail-16.17.1.tgz
```

Para conferir se já há índice sem gerar nada:

```bash
uv run lol-assets-indexer check
```

### A API opcional

O site funciona inteiro sem ela ([ADR 0006](docs/adr/0006-api-como-componente-opcional.md)).
Se quiser subir mesmo assim:

```bash
docker compose up --build
```

`http://localhost:8000/docs` traz o Swagger. As rotas leem o índice do próprio repositório,
montado como volume somente-leitura — **não há bucket** desde o
[ADR 0012](docs/adr/0012-onde-guardar-os-assets.md).

Sem Docker, dá para rodar direto:

```bash
uv run uvicorn lol_assets_api.main:app --reload
```

## Fontes dos assets

Data Dragon e Community Dragon. A League of Legends Wiki **não** é acessada de
forma automatizada: os Termos de Uso da Weird Gloop exigem consentimento prévio,
que ainda não foi solicitado (KICKOFF §B.3.2).

## Legal

Projeto não oficial, sem vínculo com a Riot Games. O aviso legal exigido pela
Developer API Policy fica visível no rodapé do site.
