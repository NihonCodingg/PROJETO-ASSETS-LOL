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
