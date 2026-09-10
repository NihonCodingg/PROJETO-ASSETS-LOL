# ADR 0014 — Onde vive o índice gerado

- **Status:** ✅ **aceito** (09/09/2026) — **opção A**: o índice fica no `main`
- **Data:** 2026-09-08
- **Depende de:** [ADR 0012](0012-onde-guardar-os-assets.md), [ADR 0013](0013-uma-versao-por-vez-no-indice.md)
- **Ticket:** T-37
- **Evidência:** medição própria, descrita abaixo; nenhum número aqui é estimado

## Antes de tudo: eu errei o número que motivou este ADR

No relatório da Onda 2 e no T-37 eu escrevi que o índice commitado custaria
**~275 MB/ano** de histórico no Git. **Está errado, por um fator de ~25.** O número real,
medido, é **~12 MiB/ano**.

O erro foi supor que cada patch guarda os 10,6 MB inteiros. Ele não guarda, por duas
razões que eu conhecia e não apliquei:

1. **O Git comprime com zlib.** Os 10.584.618 bytes de JSON viram **1.201.076 bytes**
   comprimidos — 8,8×.
2. **O Git faz delta entre objetos parecidos.** Índices de patches consecutivos são quase
   idênticos: mudam as strings de versão em 6.966 das 15.515 URLs e o `sha256` do pouco
   que a Riot realmente retocou. O delta come quase tudo isso, e o custo cai de 1,2 MiB
   para **~0,38 MiB por patch**.

Este ADR existe porque a pergunta era boa. A resposta é que o problema é **muito menor do
que eu disse**, e isso muda a recomendação.

## A medição

Simulação de 78 patches (três anos) num repositório descartável, commitando o índice real
do patch 16.17.1 reescrito a cada iteração — nomes com hash recalculados, `git gc
--prune=now` em cada marco. Três cenários, porque o delta depende de quanto muda:

- **piso** — só as strings de versão mudam (nenhuma arte mudou no patch);
- **real** — o piso mais 5 % dos assets com `sha256` e `bytes` novos (skins novas, ícones
  retocados);
- **teto** — todos os `sha256` mudam. Não acontece; existe para limitar por cima.

Tamanho do `.git` **inteiro**, em MiB:

| Patches | Tempo | piso | **real** | teto |
|---:|---|---:|---:|---:|
| 1 | — | 1,2 | **1,1** | 1,1 |
| 13 | 6 meses | 7,0 | **6,8** | 12,6 |
| 26 | **1 ano** | 9,8 | **11,7** | 23,7 |
| 52 | 2 anos | 20,0 | **20,5** | 48,7 |
| 78 | **3 anos** | 24,8 | **27,8** | 71,4 |

Marginal no cenário real: **0,38 MiB por patch**, estável do 13º ao 78º — a cadeia de
delta longa não degrada.

Para escala: o `.git` do projeto hoje é **0,65 MiB**. O GitHub recomenda repositórios
abaixo de 1 GB e "fortemente recomenda" abaixo de 5 GB. No cenário real, 1 GB chega em
**~85 anos**.

## Contexto

O [ADR 0012](0012-onde-guardar-os-assets.md) tirou o storage; o
[ADR 0013](0013-uma-versao-por-vez-no-indice.md) limitou o índice a uma versão, o que
mantém o **diretório de trabalho** em 10,6 MB. O que nenhum dos dois tocou é o **histórico
do Git**: cada indexação reescreve o índice com nomes novos, e todo blob commitado fica no
repositório para sempre.

A pergunta do T-37 era: quanto isso custa, e vale mudar de estratégia antes da primeira
execução do workflow?

## As saídas

Custo em **tamanho de `git clone`** (o padrão, sem `--depth`), sempre incluindo o código:

| | 1 ano | 3 anos | 10 anos | Exige de você | Quebra |
|---|---:|---:|---:|---|---|
| **A — deixar no `main`** (o que o T-13 faz hoje) | **12 MiB** | **28 MiB** | ~90 MiB | nada | nada |
| **B — gerar no build da Vercel** | 0,7 MiB | 0,7 MiB | 0,7 MiB | nada | o build; ver abaixo |
| **C — branch órfão com force-push** | ~1,9 MiB | ~1,9 MiB | ~1,9 MiB | aprovar um passo a mais no build | nada |
| **D — repositório separado de dados** | 0,7 MiB | 0,7 MiB | 0,7 MiB | criar o repo **e um PAT** | a promessa do ADR 0012 |
| **E — voltar para o R2** | 0,7 MiB | 0,7 MiB | 0,7 MiB | **cartão de crédito** | o ADR 0012 inteiro |

### A — deixar no `main`

O índice é commitado em `apps/web/public/indice/`, como o T-13 já faz.

- **Custo:** 12 MiB no primeiro ano, 28 MiB em três, ~90 MiB em dez.
- **Exige:** nada. Já está escrito e testado.
- **Quebra:** nada. Quem quiser evitar o histórico usa `git clone --depth 1`.
- **Contra:** o `git log` do código fica cheio de commits `chore(indice)`, um a cada
  patch. É poluição visual real, mas é o `main` de um projeto de uma pessoa.

### B — gerar no build da Vercel

Nada é commitado; o build baixa o tarball e roda a indexação.

- **Custo de clone:** zero. O repositório fica em 0,65 MiB para sempre.
- **Exige:** nada de você.
- **Quebra:** o build. **Baixar 2,39 GB e medir 15.526 imagens a cada deploy**, inclusive
  num commit de CSS. O plano Hobby dá 45 minutos de build; a varredura leva ~15 aqui, com
  disco local e sem concorrência. E se o ddragon estiver fora no momento do deploy, o
  deploy falha — hoje uma queda do ddragon não impede publicar o site.
- **Veredito:** resolve o problema errado. Troca 12 MiB/ano por fragilidade em todo deploy.

### C — branch órfão com force-push

O índice vive em `refs/heads/indice`, com **um commit só**, reescrito (`push --force`) a
cada patch. É o padrão para dado gerado, e você está certo sobre por quê: o código fica
limpo, e reescrever a branch de dados não afeta ninguém, porque ninguém tem trabalho em
cima dela.

- **Custo de clone:** ~1,9 MiB, **constante**. Um `git clone` normal busca todas as
  branches, então ele baixa o índice atual (1,2 MiB comprimidos) — mas não o histórico
  dele, que não existe.
- **Exige:** duas coisas mecânicas, nenhuma delas um segredo novo:
  1. **O build precisa buscar o índice.** A Vercel constrói uma branch só. O
     `buildCommand` passa a baixar os arquivos de `raw.githubusercontent.com` antes do
     `next build`. **Verifiquei: o `raw` responde `Access-Control-Allow-Origin: *` e não
     pede autenticação em repositório público.**
  2. **Algo precisa disparar o deploy.** Commit em branch órfã não dispara a Vercel. A
     saída barata é o workflow tocar um arquivo de marcação no `main` — o número do patch,
     dezenas de bytes por indexação em vez de megabytes.
- **Quebra:** nada. O `GITHUB_TOKEN` padrão escreve em qualquer branch do próprio
  repositório.
- **Contra:** mais peças. Um passo de build que depende do `raw` estar de pé no momento do
  deploy, e um arquivo de marcação cuja única função é existir.

### D — repositório separado de dados

`lol-assets-indice`, só com o índice.

- **Custo de clone do código:** **zero de verdade** — o clone nunca vê o índice, nem o
  atual.
- **Exige:** criar o repositório **e um Personal Access Token**, porque o `GITHUB_TOKEN`
  do Actions só escreve no repositório onde o workflow roda.
- **Quebra:** a promessa explícita do [ADR 0012](0012-onde-guardar-os-assets.md) de que
  **nenhum segredo além do `GITHUB_TOKEN`** seria necessário. Um PAT expira, precisa ser
  rotacionado, e é exatamente o tipo de manutenção que a opção B do 0012 existia para
  evitar.
- **Contra:** paga com um segredo os 1,2 MiB que a opção C não cobra.

### E — voltar para o R2

- **Custo de clone:** zero.
- **Exige:** cartão de crédito na Cloudflare — a restrição forte que decidiu o ADR 0012.
- **Quebra:** o ADR 0012 inteiro, e traz de volta quatro variáveis de ambiente.

## Decisão: **A**, com a **C** anotada como plano B

**Deixe no `main`.** São 12 MiB no primeiro ano e 28 MiB em três, num repositório que hoje
tem 0,65 MiB. Nenhuma das alternativas compra o suficiente para pagar o que cobra:

- a **B** troca 12 MiB/ano por um build de 15 minutos que pode falhar por causa do ddragon;
- a **C** custa duas peças novas — um passo de build e um arquivo de marcação — para
  economizar ~26 MiB em três anos;
- a **D** custa um segredo para economizar mais 1,2 MiB que a C;
- a **E** custa um cartão.

A **C é a escolha certa quando o número for grande**, e ela continua disponível: migrar
depois é `git filter-repo` no histórico do índice, ou simplesmente começar a branch órfã e
deixar o passado no `main`. **Nada aqui é irreversível.**

**Gatilho para revisitar,** para a decisão não depender de ninguém lembrar: quando o
`.git` do repositório passar de **200 MiB**, ou quando o `git clone` incomodar na prática —
o que vier primeiro. No ritmo medido, 200 MiB chegam em ~17 anos.

## Isto reabre o R2 (ADR 0012)?

**Não, e o custo acumulado empurra na direção oposta.**

O argumento para reabrir seria o histórico ficar caro o bastante para um bucket valer o
cartão. Ele fica em 28 MiB em três anos. Um bucket de R2 não economiza isso de forma
relevante, e **a opção C economiza a mesma coisa de graça e sem cartão** — o que faz do R2
a pior das cinco saídas para este problema específico.

O que **poderia** reabrir o 0012 é outra coisa: se o tráfego do site começar a bater nas
fontes a ponto de virar má vizinhança, ou se o ddragon passar a bloquear hotlink. Nenhum
dos dois é o caso, e nenhum dos dois tem a ver com tamanho de repositório.

## Consequências

- O T-37 fecha sem escrever código. O T-13 já faz o certo.
- O `git log` do `main` passa a ter um commit `chore(indice)` por patch. Se incomodar, é
  sintoma de que a hora da C chegou.
- O número errado do relatório da Onda 2 e do T-37 precisa ser corrigido, com a medição no
  lugar dele.
- A primeira indexação foi disparada em 09/09/2026, logo depois desta decisão. Era o que
  estava travado por esta pergunta.
