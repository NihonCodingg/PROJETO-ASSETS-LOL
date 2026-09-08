# Sessão 07–08/09/2026 — Onda 2: o patch inteiro

Sete tickets, sete PRs, CI verde antes de cada merge. Mais um ADR que nasceu no meio da
onda e reescreveu um ticket já pronto.

| PR | Ticket | O que entrega |
|---|---|---|
| [#11](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/11) | **T-09** | Adaptador ddragon completo pelo tarball |
| [#12](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/12) | **T-10** | Guarda de tamanho e de forma do índice |
| [#13](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/13) | **T-11** | Uma versão por vez no índice |
| [#14](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/14) | **T-12** | `status.json`, resumo do job e issue automática |
| [#15](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/15) | **T-13** | Workflow agendado de indexação |
| [#16](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/16) | **T-14** | Busca com normalização, apelidos e cmdk |
| [#17](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/17) | **T-15** | Painel de asset completo |

A suíte foi de **102 para 235 testes Python** e de **25 para 104 de vitest**.

## O patch inteiro, medido

A Onda 1 provou a arquitetura com um campeão e dois tipos. Esta provou com tudo:

| | |
|---|---:|
| Tarball baixado | 2.564.139.878 B |
| Arquivos no tarball | 34.305 |
| Imagens medidas | 15.526 |
| Descartadas pelo filtro de escopo | 18.421 |
| Ilegíveis | **0** |
| Registros no índice | **15.515** |
| Bytes que o índice descreve | 1,34 GiB |
| Campeões · skins | 173 · 2.118 |
| Índice escrito | 10.583.827 B |

Os totais batem com o S1: 173 squares, 2.118 de cada corte de splash, 868 itens, 726
feitiços. Evidência bruta em
[`docs/evidencias/t09-indexacao-real.json`](../evidencias/t09-indexacao-real.json).

## O que só apareceu rodando de verdade

A fixture do T-09 tinha um caso de cada coisa e passava. O patch real achou **três defeitos
que ela não tinha como ter**:

1. **Item com `"name": ""`.** O ddragon tem placeholder que nunca removeram. O schema exige
   um caractere, e a indexação inteira abortava num `ValidationError` — depois de doze
   minutos de varredura.
2. **`Fiddlesticks` contra `FiddleSticks`.** O ddragon escreve o campeão de um jeito em
   `data/` e de outro em `img/champion/*/`. Eram **13 skins × 4 cortes = 52 arquivos**
   sumindo do índice **sem erro nenhum** — o pior tipo de bug. A busca por caminho passou a
   tolerar divergência de caixa e a devolver o caminho **real**, para a URL não dar 404.
3. **Stat mods fora do índice.** Nenhum JSON do ddragon os lista; o construtor de runas ia
   só pelo `runesReforged.json`. São 10 ícones que a §A.4 do KICKOFF cita junto com as
   runas justamente porque têm alfa.

Nenhum dos três é sutil depois de encontrado. Os três eram invisíveis antes.

## A medição que reescreveu um ticket pronto

O T-11 estava escrito, testado e rodando: reduzir a versão anterior aos tipos versionados.
Aí a execução mediu o que isso custa — **4,4 MB por patch, não os ~3 MB estimados**, ~115
MB/ano num repositório que todo `git clone` baixa inteiro. E o que se comprava eram ícones
repetidos: splash, loading, tile e a categoria `rune` **inteira** não são versionados.

Você parou a entrega e decidiu: **teto de uma versão**. Virou o
[ADR 0013](../adr/0013-uma-versao-por-vez-no-indice.md), e a propagação foi larga — RF-19 e
RF-20 fora da v1, T-26 suspenso, T-36 fechado, ADR 0007 emendado, jornada J5 riscada.

A redução que já estava escrita foi **descartada antes de entrar**. A regra dela está por
extenso no ADR, o que é mais durável que um ponteiro para um commit.

**Foi a melhor decisão da onda, e ela só existiu porque a medição veio antes da entrega.**

## 🛑 O que ficou em aberto, e por quê

**O índice ainda não está no repositório.** O T-13 commita 10,6 MB na primeira execução — e
isso é exatamente a pergunta do **T-37**, que registrei em vez de responder sozinho:

> O teto de uma versão mantém o **diretório** em 10,6 MB. Ele não encosta no **histórico do
> Git**: cada indexação reescreve o índice inteiro com nomes novos, e todo blob commitado
> fica lá para sempre. Com o T-13 rodando a cada 6 h, são ~~**~275 MB/ano**~~ que todo clone
> baixa.

> ⚠️ **Corrigido em 08/09/2026:** o número acima está errado por um fator de ~25. Medido,
> são **~12 MiB/ano** — eu esqueci que o Git comprime (8,8×) e faz delta entre índices
> consecutivos (mais ~3×). Três anos custam 28 MiB, num repositório que hoje tem 0,65 MiB.
> A análise das cinco saídas está no
> [ADR 0014](../adr/0014-onde-vive-o-indice-gerado.md), proposto.

Disparar o workflow sozinho ainda seria decidir em silêncio, então continua com você — mas
a decisão é bem menos pesada do que eu a apresentei.

**Quando você quiser:** Actions → Indexação → Run workflow. Os campos `force` e
`game_version` estão lá para reindexar sem esperar patch novo.

O critério 4 do T-13 também depende da **Vercel estar ligada**, que ainda não está.

## Decisões que tomei durante a execução

- **O adaptador mínimo do T-05 foi removido, não deixado ao lado.** Ele montava
  `storageKey`, o que contradiz o ADR 0012 na primeira chamada. O mapa de pastas do
  ADR 0002 passou a existir num lugar só, com teste que falha se alguém criar o segundo.
- **As guardas medem os bytes que iriam para o disco**, não uma serialização parecida. Foi
  o que exigiu separar serialização de escrita — e é o que faz "aborta antes de escrever"
  ser verificável em vez de aproximado.
- **A regra do histórico sai da URL, não de uma lista de tipos.** A lista do ticket estava
  incompleta (faltava `ability_icon`), e lista escrita à mão fica errada de novo assim que
  o ddragon mudar um caminho de lugar.
- **A issue automática ficou em Python, não em YAML.** O critério pedia teste de
  idempotência, e passo de workflow não se testa sem `act`.
- **A busca suprime as skins do campeão que casou.** Uma regra só resolve os dois critérios
  opostos: `jax` devolve uma entrada, `kda` devolve skins de vários campeões.
- **`--dry-run` não escreve nem o `status.json`.** Regra com exceção é regra que ninguém
  lembra.

## Trabalho fora do escopo, anotado como ticket

- **T-36 — teto de versões.** Levantado no T-11, **fechado na mesma onda** pela sua decisão.
- **T-37 — o índice no histórico do Git.** ~275 MB/ano quando o T-13 rodar sozinho. As
  saídas possíveis e o custo de cada uma estão no ticket. São **37 tickets** agora.

## Correções de número na Spec

- **2.118 skins, não 2.149.** O 2.149 vinha do cdragon (S3); o ddragon, única fonte da v1,
  lista 2.118 skins e 6.994 chromas. A diferença entra com o T-16.
- **~2,7 MB por versão antiga → 4,4 MB medidos.** Corrigido antes de virar decisão errada.
- **RNF-05** passou a citar os 10,6 MB medidos.

## Infraestrutura que faltava

`jsdom` e `@testing-library/react`, mais o alias `@/` e a transformação de JSX no
`vitest.config.ts`. Sem DOM, comportamento de componente só dava para provar por varredura
de fonte, que é fraca. Destrava T-19, T-20, T-24 e T-25.

## O que não toquei

`docs/design/` continua vazia, com só o README. **T-34 e T-30 seguem bloqueados**, e não
usei o Chrome.

## Próximo passo

A **Onda 3**: cdragon (T-16), fusão de fontes (T-17), seletor de skin (T-19) e chromas
(T-20). Nada dela depende do T-37 nem da Vercel.

Antes disso, duas coisas suas: decidir o **T-37** e, se quiser ver o site de pé, disparar o
workflow uma vez e ligar a Vercel.
