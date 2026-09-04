# Fixture do contrato

Um retrato **medido** do patch `16.17.1`. Nada aqui é inventado: dimensão, formato, canal
alfa, bytes e `sha256` de cada asset saíram do arquivo real, baixado do ddragon e medido
com Pillow. O `sourceUrl` de cada registro diz exatamente de onde veio.

| Arquivo | Conteúdo |
|---|---|
| `manifest.json` | Uma versão, apontando para o catálogo e para as três fatias |
| `catalog.json` | 3 campeões (Jax, Lux, Nunu) e todas as skins deles — os dois níveis do [ADR 0010](../../../docs/adr/0010-navegacao-por-campeao-busca-por-skin.md) |
| `index-champion.json` | Assets de campeão: `square`, `splash_centered`, `splash_wide`, `loading`, `tile` |
| `index-item.json` | Um ícone de item — PNG **sem** alfa |
| `index-rune.json` | Um ícone de runa — PNG **com** alfa |

## Por que estes casos

A fixture existe para o front (T-08) andar em paralelo com o indexador. Para isso ela
precisa exercitar o que é difícil, não só o caminho feliz:

- **Os dois níveis do ADR 0010.** `champions[]` para navegar, `skins[]` para buscar, e cada
  skin ligada ao campeão por `championKey`.
- **Os nomes canônicos do [ADR 0002](../../../docs/adr/0002-nomes-canonicos-de-corte-de-splash.md).**
  `splash_centered` mede 1280×720 e `splash_wide` mede 1215×717 — exatamente a inversão que
  ddragon e cdragon fazem entre si.
- **Alfa de verdade.** A runa é RGBA e o ícone de item é RGB puro, que é o que o S1 mediu.
  É esse par que faz o front acertar quando desabilitar o botão "Baixar PNG"
  ([ADR 0001](../../../docs/adr/0001-formato-de-entrega-dos-assets.md) regra 4).
- **Skin sem asset.** O catálogo tem 54 skins e a fatia tem asset só de quatro delas.
  É de propósito: é o caso que o front precisa saber tratar sem quebrar.

## Como foi gerada

Baixando estes arquivos e medindo cada um:

- `cdn/16.17.1/data/{pt_BR,en_US}/champion/{Jax,Lux,Nunu}.json` — nomes, título, tags e skins
- `cdn/16.17.1/img/champion/{Id}.png` — square
- `cdn/img/champion/{centered,splash,loading,tiles}/{Id}_{num}.jpg` — os cortes
- `cdn/16.17.1/img/item/3031.png` e `cdn/img/perk-images/Styles/Precision/Conqueror/Conqueror.png`

Chromas ficam fora do catálogo por serem identificados pelo campo `parentSkin` do ddragon
(KICKOFF §B.1.4), e o `chromaCount` de cada skin conta quantos ela tem.

Se o contrato mudar, a fixture é regerada — nunca editada à mão. Ela é validada contra o
JSON Schema em `tests/test_models.py`, e o front a consome por `src-ts/examples.ts`.
