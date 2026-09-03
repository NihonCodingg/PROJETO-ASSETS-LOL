# ADR 0007 — Só a versão atual tem assets copiados; orçamento de 10 GB

- **Status:** aceito
- **Data:** 2026-09-03
- **Depende de:** [ADR 0005](0005-arquitetura-estatica-custo-zero.md)
- **Evidência:** [SPIKES](../SPIKES.md) — S1 e S3

## Contexto

O tier gratuito do Cloudflare R2 dá **10 GB**. Os spikes mediram quanto custa uma versão
completa do catálogo, nos bytes de origem (sem re-encode, conforme o
[ADR 0001](0001-formato-de-entrega-dos-assets.md)):

| Fatia | Tamanho |
|---|---:|
| Splash centralizada · 2.149 skins | 196,4 MB |
| Splash aberta · 2.149 skins | 372,1 MB |
| Loading · 2.149 skins | 101,8 MB |
| Tile · 2.149 skins | 84,2 MB |
| Chromas · 7.037 | 408,7 MB |
| Ícones de perfil · 5.021 | 554,0 MB |
| Square, itens, feitiços, passivas, runas, mapas | 16,9 MB |
| **Total medido** | **~1,74 GB** |

Emotes (2.347) e ward skins (265) ainda não foram medidos em bytes; pela dimensão dos
ícones a estimativa é de mais ~150 MB, o que leva uma versão a **~1,9 GB**.

A Riot publica um patch a cada duas semanas. Copiar tudo de toda versão estoura os 10 GB
em cerca de **10 semanas** e depois cresce para sempre.

## Decisão

1. **Apenas a versão atual tem assets copiados para o R2.** Uma versão, ~1,9 GB, ~19 % do
   tier gratuito. Sobra espaço para os zips por categoria e para crescimento do catálogo.
2. **Versões anteriores existem só como índice**, apontando para as URLs versionadas do
   ddragon (`sourceUrl`). O campo `storageKey` fica ausente e o front usa `sourceUrl`.
   O índice de uma versão antiga custa alguns MB.
3. Ao indexar um patch novo, os assets do patch anterior são **removidos do bucket**; o
   índice dele permanece.
4. **Idiomas:** `pt_BR` primeiro; `en_US` entra quando couber. Os dois juntos custam
   18,2 MB de JSON de origem por patch, então cabem — mas a ordem de prioridade fica
   registrada para quando o orçamento apertar.
5. Se o orçamento apertar, a primeira fatia a sair são os **ícones de perfil** (554 MB,
   32 % do total, e o tipo de asset que menos serve a um editor de vídeo).

## A pegadinha que isso expõe

**Histórico de splash não existe no ddragon.** Os spikes confirmaram que
`img/champion/splash/`, `centered/`, `loading/` e `tiles/` são servidos **sem versão na
URL**: eles sempre entregam a arte *atual*. Só `square`, `item`, `spell`, `passive`,
`profileicon` e `map` ficam sob `/cdn/{versão}/` e são realmente históricos.

Consequência direta: para versões anteriores, o índice só pode oferecer os tipos
versionados. Splash, loading e tile de patches antigos **não são recuperáveis** por esta
arquitetura — e a interface precisa dizer isso, em vez de servir a arte de hoje com um
rótulo de ontem. A §A.3 previa "squares/splashes de versões antigas": os squares sim, os
splashes não. A única fonte conhecida para o histórico de splash é a wiki, que depende do
consentimento do [ADR 0004](0004-consentimento-da-wiki-e-teto-de-resolucao.md).

## Consequências

- O custo de armazenamento fica constante em ~1,9 GB, independente de quantos patches
  passem. O orçamento nunca é atingido por acúmulo.
- O índice acumula, mas é barato: alguns MB por versão.
- O front precisa lidar com asset **sem** `storageKey` e com tipos ausentes em versões
  antigas. Isso é contrato, não caso de erro — está no JSON Schema.
- Uma versão antiga depende do ddragon estar no ar. É o mesmo risco que a §A.5 já
  aceitava para a indexação, e afeta só o modo histórico.
- O passo de remoção do patch anterior é destrutivo e roda sozinho no Actions. Precisa de
  teste e de trava: nunca apagar antes do índice novo estar publicado e verificado.
