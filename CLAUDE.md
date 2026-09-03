# CLAUDE.md — regras de trabalho do projeto lol-assets

> Estas regras são a cópia literal da §0.2 de [`docs/KICKOFF.md`](docs/KICKOFF.md).
> Se houver conflito, vale o KICKOFF (e, quando existirem, `docs/SPEC.md` e `docs/TICKETS.md`).

## Regras

1. Ler `docs/KICKOFF.md` (este arquivo) antes de qualquer coisa. Depois que existirem, `docs/SPEC.md` e `docs/TICKETS.md` têm precedência sobre ele.
2. Nunca inventar um endpoint, path ou formato de asset. Se não está na Parte B, testar primeiro e registrar o resultado em `docs/SPIKES.md`.
3. Nenhuma requisição automatizada à wiki (`wiki.leagueoflegends.com`) enquanto `WIKI_CONSENT_GRANTED` não estiver documentado em `docs/SPIKES.md` com data e evidência. O adaptador pode existir, mas desligado por flag.
4. Requisições ao ddragon e cdragon sempre com `User-Agent: lol-assets-indexer/{versão} (+https://github.com/NihonCodingg/PROJETO-ASSETS-LOL; contato do mantenedor)`, concorrência ≤ 4, backoff exponencial em 429/5xx.
5. PRs com no máximo ~500 linhas de lógica (exclui lockfiles, fixtures e snapshots). Se um ticket não cabe, dividir o ticket, não inflar o PR.
6. TDD nos módulos de lógica (indexador, fusão, conversão, busca). UI pode ter testes mais leves, mas o fluxo "buscar → baixar" tem teste e2e.
7. Nada de segredo no código. Variáveis de ambiente documentadas em `.env.example`.
8. Commits em Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`). Idioma do código e dos identificadores: inglês. Idioma de docs e commits: português.
9. Ao terminar qualquer tarefa, relatar em português: o que foi feito, o que foi assumido, o que ficou pendente, e qual o próximo passo sugerido. Esse relatório também é salvo em `docs/sessoes/AAAA-MM-DD-{tema}.md` e commitado.
10. Se algo na Parte B se mostrar errado na prática, corrigir `docs/PESQUISA` via PR com a evidência, não contornar em silêncio.
11. **Git:** remoto único é `https://github.com/NihonCodingg/PROJETO-ASSETS-LOL.git`. `main` só recebe merge via PR. Trabalho em branches `feat/T-XX-descricao`, `docs/...`, `chore/...`. Etapas 1–4 (bootstrap, spikes, protótipo, spec) podem ir direto na `main` porque ainda não há código de produção; a partir dos tickets, só PR. Push ao final de cada bloco, sem exceção — trabalho não enviado é trabalho que não existe.
12. Decisões de arquitetura viram ADRs em `docs/adr/NNNN-titulo.md` (contexto, decisão, consequências). A Spec referencia os ADRs, não os repete.

## Onde as coisas ficam

| Caminho | Conteúdo |
|---|---|
| `docs/KICKOFF.md` | Processo (Parte 0), ideia (Parte A), pesquisa das fontes (Parte B) |
| `docs/SPIKES.md` | Números reais medidos nos spikes |
| `docs/SPEC.md` | Especificação (etapa 4) |
| `docs/TICKETS.md` | Tickets de execução (etapa 5) |
| `docs/adr/` | Decisões de arquitetura (regra 12) |
| `docs/sessoes/` | Relatório de cada sessão (regra 9) |
| `apps/web/` | Front-end Next.js |
| `apps/api/` | API FastAPI |
| `packages/indexer/` | Adaptadores, fusão, conversão e publicação |
| `packages/schema/` | Contrato do índice (JSON Schema + tipos TS + modelos Pydantic) |
| `prototype/` | Descartável; apagado no primeiro ticket da etapa 6 |

## Comandos

```bash
pnpm install          # dependências JS/TS de todo o workspace
uv sync               # dependências Python de todo o workspace
pnpm -r lint          # eslint
pnpm -r typecheck     # tsc --noEmit
pnpm -r test          # vitest
uv run ruff check .   # lint Python
uv run ruff format --check .
uv run mypy .         # tipos Python
uv run pytest         # testes Python
```

## Etiqueta de rede (regra 4, obrigatória em qualquer adaptador)

- `User-Agent: lol-assets-indexer/{versão} (+https://github.com/NihonCodingg/PROJETO-ASSETS-LOL; contato do mantenedor)`
- Concorrência ≤ 4 requisições simultâneas por host.
- Backoff exponencial em 429 e 5xx.
- `wiki.leagueoflegends.com`: **proibido** enquanto `WIKI_CONSENT_GRANTED` não estiver documentado em `docs/SPIKES.md` com data e evidência (regra 3).
