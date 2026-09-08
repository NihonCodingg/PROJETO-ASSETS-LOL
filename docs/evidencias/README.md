# Evidências

Medições brutas, sem tratamento. Cada número citado na [Spec](../SPEC.md), nos
[ADRs](../adr/README.md) ou nos [tickets](../TICKETS.md) deve poder ser rastreado até um
arquivo daqui.

| Arquivo | O que mede | Quando |
|---|---|---|
| [`spikes/`](spikes/) | As quatro sondagens que sustentam a Spec e os ADRs | 02–03/09/2026 |
| [`t09-indexacao-real.json`](t09-indexacao-real.json) | A primeira indexação do patch inteiro pelo tarball (T-09) | 07/09/2026 |

## `t09-indexacao-real.json`

Patch **16.17.1**, tarball de 2.564.139.878 bytes, 34.305 arquivos, uma passada.

| | |
|---|---:|
| Imagens medidas | 15.526 |
| Imagens descartadas pelo filtro de escopo | 18.421 |
| Imagens ilegíveis | 0 |
| Registros no índice | **15.515** |
| Bytes que o índice descreve | 1.439.374.815 (1,34 GiB) |
| Campeões no catálogo | 173 |
| Skins no catálogo | 2.118 |

**Contra o RNF-03 e o RNF-05**, agora impostos por código no T-10. Os números do JSON são
da serialização compacta; a tabela abaixo é dos arquivos **como o indexador os escreve**,
que é o que a guarda mede:

| Documento | Escrito | gzip | Limite | Uso |
|---|---:|---:|---|---:|
| Catálogo | 779.470 | **63.293** | 150 KiB | 41 % |
| Fatia `champion` | 6.524.686 | **717.050** | 1,5 MiB | 46 % |
| Índice inteiro | **10.583.827** | — | 15 MiB | 67 % |

Os três passam. O que tem menos folga é o índice inteiro, e é ele que o [T-11] vai fazer
crescer ~3 MB por versão antiga guardada.

O `descartePorPasta` no JSON mostra o que o filtro de escopo joga fora e por onde:
challenges (3.388), modo Classic (2.492) e as onze pastas de TFT.

## Duas versões, medidas na execução do T-11

Indexação de `16.16.1` e depois `16.17.1` no mesmo destino, com o mesmo tarball, antes do
[ADR 0013](../adr/0013-uma-versao-por-vez-no-indice.md):

| | Bytes | Assets | Categorias |
|---|---:|---:|---|
| Corrente (16.17.1) | 10.581.799 | 15.515 | champion, item, map, profile_icon, **rune**, summoner_spell |
| Anterior reduzida (16.16.1) | **4.429.668** | 6.966 | champion, item, map, profile_icon, summoner_spell |

Foi este número que derrubou o histórico: **4,4 MB por patch**, não os ~3 MB estimados —
e sem a categoria `rune`, porque `perk-images` não é versionado no ddragon. A ~26 patches
por ano, seriam ~115 MB/ano num repositório que todo clone paga inteiro.

## O `status.json` do patch 16.17.1

Primeira execução com o relatório do T-12 ligado. O que confirma mais que o resto:
**`unexpectedDimensions` saiu vazio** — todas as 2.118 splashes, 2.118 tiles, 2.118
loadings e 173 squares batem, pixel a pixel, com o que o S1 mediu.

```json
"counts":  { "assets": 15515, "champions": 173, "skins": 2118, "categories": 6 },
"bytes":   { "index": 10583827, "catalogGzip": 63293, "largestShardGzip": 717050,
             "describedAssets": 1439374815 },
"source":  { "files": 34305, "imagesMeasured": 15526, "imagesSkipped": 18421,
             "caseMismatches": 52 }
```

Os 52 `caseMismatches` são as 13 skins do Fiddlesticks vezes os 4 cortes — a divergência
de caixa que o T-09 encontrou, agora contada a cada execução em vez de descoberta de novo.
