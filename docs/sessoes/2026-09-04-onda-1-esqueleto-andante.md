# Sessão 04/09/2026 — Onda 1: o esqueleto andante

Seis tickets, seis PRs, CI verde antes de cada merge. Mais a pasta `docs/design/`, pedida
antes da onda.

| PR | Ticket | O que entrega |
|---|---|---|
| [#1](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/1) | — | `docs/design/` e o que deve ir nela |
| [#2](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/2) | **T-03** | Cliente HTTP com a etiqueta de rede |
| [#3](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/3) | **T-04** | Contrato em código: modelos, validação e fixture |
| [#4](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/4) | **T-05** | Adaptador ddragon mínimo |
| [#5](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/5) | **T-06** | Publicador no R2 com manifesto atômico |
| [#6](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/6) | **T-07** | CLI ligando as pontas |
| [#7](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/7) | **T-08** | Front carrega o índice, lista e baixa |

A suíte foi de 12 para **102 testes Python** e de 3 para **25 de vitest**.

## A arquitetura foi validada de ponta a ponta — menos o último passo

O objetivo desta onda era provar a arquitetura antes de escalar, e ela se provou. Duas
verificações ao vivo, não só com mock:

**A CLI, contra o ddragon de verdade:**

```
2 assets · 1 campeão(ões) · 18 skins · patch 16.17.1
16.17.1/champion/Jax_000_splash_centered.jpg
16.17.1/champion/Jax_square.png
catalog-99ca9adce52d.json
index-champion-4346d0020399.json
manifest.json
```

Os bytes batem exatamente com os medidos nos spikes: square 27.107, splash 92.299.

**O front, contra a saída da CLI**, servida pelo próprio Next. Na abertura, três
requisições — e a fatia de assets **não** está entre elas:

```
GET /bucket/manifest.json                    → 200
GET /bucket/catalog-99ca9adce52d.json        → 200
GET /bucket/16.17.1/champion/Jax_square.png  → 200
```

Ela só apareceu **depois do clique** no campeão. É a ordem do ADR 0010 observada em rede,
não deduzida do código.

E no navegador: o `sha256` dos bytes baixados **bate com o do índice**, o PNG convertido
preserva 1280×720 e sai 7,75× maior — consistente com os 8,14× medidos no protótipo, mais
uma confirmação do ADR 0001.

## 🛑 O que falta e por que parei aqui

**A publicação real no R2 precisa de credencial que só você pode configurar.**

Não contornei com storage local, como você pediu. O que existe hoje é o `--dry-run`, que é
o **mesmo código com outro destino** — e há um teste que publica nos dois e compara as
árvores byte a byte, então não há divergência escondida entre "testei local" e "subiu no
bucket". Mas byte a byte igual não é a mesma coisa que ter subido, e a Onda 1 existe para
provar a arquitetura **real**.

Para fechar, preciso destas quatro variáveis:

```
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_BUCKET=lol-assets
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
```

Mais, para o front resolver as URLs públicas:

```
ASSETS_PUBLIC_BASE_URL=https://<domínio ou r2.dev>
```

No R2: criar o bucket, gerar um API token com permissão de leitura e escrita **só nele**, e
habilitar acesso público (r2.dev ou domínio próprio). Depois disso rodo
`lol-assets-indexer index --champion Jax` sem `--dry-run`, aponto o front para a base
pública e fecho a onda com o caminho real.

**Não me mande as credenciais aqui.** Coloque num `.env` na raiz do repositório — ele já
está no `.gitignore` — e me avise. Para o T-13 elas vão como secrets do repositório no
GitHub, nunca no código.

## Decisões que tomei durante a execução

- **Executei em sequência, não em paralelo.** A onda previa duas frentes; numa sessão só,
  paralelizar não daria ganho e complicaria a ordem dos PRs.
- **A fixture do T-04 é medida, não inventada.** Baixei os arquivos reais e medi dimensão,
  formato, alfa, bytes e `sha256`. Um teste falha se as dimensões pararem de bater com os
  spikes.
- **O adaptador passou a devolver os bytes junto com o registro** (T-07). Baixar de novo na
  hora de publicar arriscaria publicar bytes diferentes dos medidos, e o `sha256` do índice
  deixaria de valer para o arquivo que está no bucket.
- **`publish_shard` recusa fatia cujos assets ainda não subiram.** O ticket não pedia; é a
  trava que torna a rotação de versão do T-11 segura de implementar.
- **Três testes de varredura de fonte**, para regras que se perdem em refactor: nenhuma
  escrita de imagem nos adaptadores nem no `imaging.py` (ADR 0001).

## O que a CI pegou e o local não

O `--help` do T-07 passava aqui e falhava lá. O Rich quebra o texto na largura do terminal;
em 80 colunas a CI truncava o nome das opções. Corrigido fixando `COLUMNS` e limpando ANSI
no teste. Foi a CI fazendo o trabalho dela — um teste dependente de ambiente disfarçado de
teste de comportamento.

## Trabalho fora do escopo, anotado como ticket

**T-35 — tirar o `next-env.d.ts` do controle de versão.** O `next dev` acrescenta sozinho
uma referência a `.next/types/routes.d.ts`, que é gerado e ignorado pelo Git. Commitar essa
linha faria o `tsc` da CI falhar procurando um arquivo que não existe lá. Revertido no PR
#7; o conserto durável virou ticket. São **35 tickets** agora.

## O que não toquei

`docs/design/` continua vazia, com só o README. **T-34 e T-30 seguem bloqueados**, e não
usei o Chrome nem tentei resolver o design sozinho.

## Próximo passo

Configure o R2 e me avise. Fecho a Onda 1 com a publicação real e sigo para a **Onda 2**
(T-09: adaptador ddragon completo pelo tarball), que não depende disso.
