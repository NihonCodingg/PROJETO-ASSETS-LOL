# Sessão 09/09/2026 — Onda 3: a segunda fonte e as skins

Cinco tickets, três PRs. CI verde antes de cada merge.

| PR | Tickets | O que entrega |
|---|---|---|
| [#21](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/21) | **T-16, T-17** | Adaptador cdragon e fusão de fontes |
| [#22](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/22) | **T-19, T-20** | Grade, seletor de skin e chromas |
| [#23](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/23) | **T-18** | Contrato das fontes, agendado |

**283 testes Python** de PR (eram 235) mais **13 de rede**, e **149 de vitest** (eram 111).

## A medição que decidiu a integração do cdragon

O adaptador estava pronto quando o número apareceu: o cdragon responde a **2,8 assets/s**
com a concorrência de 4 da regra 4 do CLAUDE.md — 115 assets do Jax em 41,6 s, medido. Os
173 campeões inteiros custariam **~2 horas por patch**, num workflow que hoje termina em
27 s.

E o S2 já tinha medido que square, splash, loading e tile **empatam** entre as duas fontes.
Pagar duas horas por patch para confirmar empate seria caro e inútil.

**A saída:** a CLI busca no cdragon só os tipos que o ddragon **não trouxe** — `chroma` e
`loading_vintage`, que é a cobertura real da segunda fonte. E a premissa de empate continua
**verificada em vez de assumida**: um punhado de campeões por execução vem completo,
girando com o hash do patch, e o `resolutionWins` do `status.json` denuncia na hora se o
cdragon vencer alguma disputa. Em ~58 patches todo campeão terá sido conferido.

## As duas coisas que quebrariam em silêncio

**Os cortes de splash competindo na fusão.** O centrado tem 1280×720 e o aberto 1215×717 —
se entrassem na mesma disputa, o centrado venceria e o corte aberto **sumiria do catálogo
inteiro**, sem erro nenhum. A chave da fusão inclui o tipo por isso, e há um teste só para
essa linha.

**Chroma vazando para a busca.** São 7.037. Um deles na grade ou na lista de skins quebraria
o RF-06 sem sintoma. O toggle sai por `parentSkinNum`, e trocar de skin **fecha** os chromas
abertos — senão o painel mostraria os da skin anterior.

## O orçamento de 3 cliques, contado

Nos quatro caminhos do ADR 0010, com um contador que passa por cada clique de verdade:
**2, 2, 3, 3**. Fecha exatamente, como o ADR previu.

## O contrato das fontes vale hoje

13 testes rodados contra ddragon e cdragon vivos: CORS ainda `*` nos dois, dimensões do S1
e do S2 intactas, os 55 apelidos apontando para campeões que existem no patch **16.18.1**.
Eles ficam fora da CI de PR por configuração — `283 passed, 13 deselected` — e rodam
sozinhos, uma vez por dia, abrindo issue em vez de bloquear merge.

## O pipeline em produção

A primeira execução do workflow foi disparada depois da decisão do
[ADR 0014](../adr/0014-onde-vive-o-indice-gerado.md), e o agendamento já pegou um patch
novo sozinho:

```
patch 16.18.1 · 15.548 assets · 173 campeões · 2.121 skins · 27 s
unexpectedDimensions: nenhum
```

O `.git` com dois índices commitados ficou em **2,02 MiB** — batendo com a previsão do
ADR 0014, que estimava ~1,1 MiB por índice mais ~0,4 pelo segundo.

## Decisões que tomei durante a execução

- **`chromas[].tilePath` não entra no índice**: medido em 26 de 26 chromas do Jax, é o
  mesmo arquivo do `chromaPath`.
- **`skins[].chromaPath` entra** como a amostra "cor original", com `parentSkinNum` igual
  ao próprio `skinNum` — é o que a torna reconhecível.
- **Não mapeável virou varredura do documento inteiro**, não só dos campos usados: uma
  mudança de formato apareceria num campo que ninguém está lendo ainda.
- **A virtualização entra acima de 60 resultados**, por contagem e não por tipo de lista.
- **O meta-teste da marca `network` tem três asserções**, porque a exclusão depende de dois
  arquivos distantes concordarem.

## Infraestrutura que faltava

`vitest.setup.ts`: o jsdom não traz `ResizeObserver` nem `scrollIntoView`, e o cmdk usa os
dois. Sem o stub, todo teste de componente que renderize a paleta morre com um erro que não
tem nada a ver com o que ele queria provar.

## O que não toquei

`docs/design/` continua vazia. **T-34 e T-30 seguem bloqueados**, e não usei o Chrome.

## Próximo passo

**Onda 4**: categorias não-campeão com tags (T-21), emotes e wards (T-22), navegação por
categoria com filtros (T-24) e o zip no cliente (T-25).
