# Sessão 03/09/2026 — bootstrap do monorepo e spikes S1–S3

Etapa 3 das 7. Blocos 1 e 2 do prompt da Parte C do KICKOFF.

## O que foi feito

**Bloco 1 — bootstrap** (commit `0de7b22`)

- Repositório clonado; estava **vazio** (sem branches). `main` é a branch padrão.
- `docs/KICKOFF.md` commitado primeiro, isolado (commit `4de417d`).
- Monorepo montado exatamente na estrutura da §0.3: pnpm workspaces + uv workspace.
  - `apps/web` — Next.js 15, React 19, Tailwind 4, TypeScript strict, ESLint 9, Vitest 3.
  - `apps/api` — FastAPI com `/health` e teste de fumaça.
  - `packages/indexer` — CLI Typer com `version` e teste de fumaça.
  - `packages/schema` — pacote duplo (Python + TS) carregando só `SCHEMA_VERSION`;
    o contrato real chega com a Spec.
- `CLAUDE.md` com as 12 regras da §0.2 copiadas palavra por palavra.
- `.github/workflows/ci.yml` com dois jobs: Python (ruff, ruff format, mypy, pytest)
  e web (eslint, tsc, vitest).
- `.env.example`, `.gitignore`, `.gitattributes` (normaliza para LF, porque a CI é Linux),
  `.npmrc`, `README.md`, `docs/adr/`, `docs/sessoes/`.

Qualidade verificada de verdade: ruff, ruff format, mypy e pytest (3 testes) verdes;
eslint, tsc e vitest (2 testes) verdes.

**Bloco 2 — spikes** (commit `0410fd7`)

- `prototype/spikes/` com `common.py`, `s1_ddragon.py`, `s2_cdragon.py`, `s3_volume.py`.
- `docs/SPIKES.md` com os números reais e os JSONs brutos em `prototype/spikes/results/`.
- Nenhuma requisição à wiki. `common.py` levanta exceção se receber URL da wiki.

## O que foi assumido

- **Escopo do bootstrap.** Criei esqueletos mínimos mas reais (um `/health` na API, um
  `version` na CLI, um `site-config` na web) em vez de pastas vazias, para que a CI
  exercite o toolchain de verdade. Nada disso é código de produto.
- **Contato no User-Agent.** Usei a URL de issues do repositório, não e-mail pessoal.
  Configurável por `INDEXER_CONTACT`.
- **Aviso legal da Riot.** O texto em `apps/web/src/lib/site-config.ts` está marcado
  `[A CONFIRMAR]` — precisa ser copiado literalmente da Developer API Policy antes do
  lançamento.
- **Versões das dependências.** Fixadas por faixa (`^`) e travadas nos lockfiles
  (`pnpm-lock.yaml`, `uv.lock`), ambos commitados.
- **Contagem de campeões.** `champion-summary.json` do cdragon traz 236 entradas; usei
  173, que é o número de campeões reais (as outras 63 são do modo League Classic, ids
  60xxx) e bate exatamente com os JSONs do ddragon.

## O que ficou pendente

1. **`pnpm install` não funciona no caminho atual.** O acento em `D:\PROGRAMAÇÃO\…`
   causa `ERR_PNPM_EPERM` em pacotes com binário nativo. Isolado com quatro testes
   controlados (detalhes em `docs/SPIKES.md`). Contornei espelhando o workspace em
   `C:\…\lolassets-mirror` para gerar o lockfile e rodar os checks. **Decisão sua:**
   mover o repositório para um caminho sem acento.
2. **"PNG sempre" (§A.4) custa 5,7×.** Converter os JPEGs da fonte para PNG multiplica
   o armazenamento por 5,7 sem ganhar um pixel — a fonte não tem canal alfa.
   Recomendo servir o formato de origem e converter no cliente. **Decisão sua**, porque
   contraria um princípio declarado não negociável.
3. **Nome do produto.** "lol-assets" contém "LoL". A §B.5.1 proíbe "Riot" ou
   "League of Legends" no nome. Vale decidir se "LoL" conta.
4. **Consentimento da Weird Gloop** para a wiki: tarefa humana, ainda não iniciada.
5. **Spikes não executados:** S4 (wiki, bloqueado) e a conferência dos emblemas de elo
   em `static.developer.riotgames.com` (§B.4).
6. **Base dos `champion-abilities/…`** do cdragon continua desconhecida (404 na base
   testada). Não bloqueia a v1.

## Próximo passo sugerido

Aprovar (ou corrigir) as duas decisões do item 1 e 2 acima e liberar o **bloco 3**:
o protótipo descartável em `prototype/web/` que valida a regra dos 3 cliques da §A.4.
Ele já nasce sabendo que a conversão para PNG deve acontecer no cliente, o que é
exatamente o que o item 2 recomenda — então o protótipo também serve de prova dessa
decisão.
