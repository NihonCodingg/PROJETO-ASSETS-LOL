# Evidências dos spikes

Os JSONs brutos das medições que sustentam a [Spec](../../SPEC.md), os
[ADRs](../../adr/README.md) e o orçamento do RNF-05. Cada arquivo traz o
`user_agent` usado, a data e os dados sem tratamento.

| Arquivo | O que mede |
|---|---|
| `s1-ddragon.json` | Tarball do patch inteiro: 34.305 arquivos, dimensões e modo de cor de 100 % das imagens |
| `s2-cdragon.json` | Jax, Lux e Nunu no cdragon: 559 assets medidos, com a comparação contra o ddragon |
| `s3-volume.json` | Contagens reais do catálogo e o custo de converter JPEG em PNG |
| `s4-orcamento.json` | Emotes, ward skins, loading vintage e emblemas de elo; orçamento fechado |

Os **scripts** que produziram estes arquivos viviam em `prototype/spikes/` e foram
apagados no ticket T-01, junto com o resto do protótipo. Eles continuam recuperáveis pelo
histórico do Git:

```bash
git show 0410fd7 -- prototype/spikes   # S1, S2, S3 e o cliente HTTP compartilhado
git show 388ea0a -- prototype/spikes   # S4
```

A leitura tratada destes números está em [`docs/SPIKES.md`](../../SPIKES.md).
