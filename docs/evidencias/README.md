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

**Contra o RNF-03 e o RNF-05**, que é o que o T-10 vai transformar em guarda:

| Documento | Bruto | gzip | Limite |
|---|---:|---:|---|
| Catálogo | 595.297 | **60.634** | 150 KB |
| Fatia `champion` | 5.192.806 | **710.213** | 1,5 MB |
| Índice inteiro | ~8,4 MB | — | 15 MB |

Os três passam com folga. O `descartePorPasta` no JSON mostra o que o filtro de escopo
joga fora e por onde: challenges (3.388), modo Classic (2.492) e as onze pastas de TFT.
