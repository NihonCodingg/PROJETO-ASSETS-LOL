# ADR 0007 — Só a versão atual tem assets copiados; orçamento de 10 GB

- **Status:** ⚠️ **largamente emendado** pelo [ADR 0012](0012-onde-guardar-os-assets.md) (07/09/2026)
  e pelo [ADR 0013](0013-uma-versao-por-vez-no-indice.md) (08/09/2026)
- **Data:** 2026-09-03
- **Depende de:** [ADR 0005](0005-arquitetura-estatica-custo-zero.md)
- **Evidência:** [SPIKES](../SPIKES.md) — S1, S3 e S4

> **Leia o [ADR 0012](0012-onde-guardar-os-assets.md) antes deste.**
> Sem storage, **não há o que copiar nem o que rotacionar**: os itens 1 a 3 e 5 caem por
> inteiro. O que **sobrevive, e é a parte mais importante deste ADR**, é a §"A pegadinha
> que isso expõe": splash, loading e tile do ddragon não são versionados, e por isso o
> histórico desses tipos continua impossível. Isso não mudou e não muda com storage nenhum.

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

1. ~~**Apenas a versão atual tem assets copiados para o R2.**~~ → **Corrigido pelo
   [ADR 0012](0012-onde-guardar-os-assets.md): nenhuma versão tem assets copiados.**
2. **Toda versão existe só como índice**, apontando para as URLs das fontes (`sourceUrl`).
   O campo `storageKey` fica **sempre** ausente. *(Era a regra das versões antigas; virou a
   regra de todas.)*
3. ~~Ao indexar um patch novo, os assets do patch anterior são **removidos do bucket**.~~ →
   ~~**Não há bucket, então não há remoção.** O que acumula é índice: ~10 MB por versão
   corrente e ~3 MB por versão antiga, que fica reduzida aos tipos versionados.~~ →
   **Corrigido pelo [ADR 0013](0013-uma-versao-por-vez-no-indice.md):** a versão antiga
   custa **4,4 MB medidos**, não ~3 MB estimados, e o índice **não acumula** — guarda uma
   versão só. Removida do manifesto, ela é apagada do destino.
4. **Idiomas:** `pt_BR` primeiro; `en_US` entra quando couber. Os dois juntos custam
   18,2 MB de JSON de origem por patch, então cabem — mas a ordem de prioridade fica
   registrada para quando o orçamento apertar.
5. ~~Se o orçamento apertar, a primeira fatia a sair são os **ícones de perfil**.~~ →
   **Não há orçamento de armazenamento a estourar.** O limite que sobra é o do RNF-03
   (tamanho do catálogo e das fatias na carga), que é sobre latência, não sobre disco.

## A pegadinha que isso expõe

**Histórico de splash não existe no ddragon.** Os spikes confirmaram que
`img/champion/splash/`, `centered/`, `loading/` e `tiles/` são servidos **sem versão na
URL**: eles sempre entregam a arte *atual*. Só `square`, `item`, `spell`, `passive`,
`profileicon` e `map` ficam sob `/cdn/{versão}/` e são realmente históricos.

Consequência direta: para versões anteriores, o índice só poderia oferecer os tipos
versionados — e foi essa incompletude que ajudou a derrubar o histórico inteiro no
[ADR 0013](0013-uma-versao-por-vez-no-indice.md). Splash, loading e tile de patches antigos **não são recuperáveis** por esta
arquitetura — e a interface precisa dizer isso, em vez de servir a arte de hoje com um
rótulo de ontem. A §A.3 previa "squares/splashes de versões antigas": os squares sim, os
splashes não. A única fonte conhecida para o histórico de splash é a wiki, que depende do
consentimento do [ADR 0004](0004-consentimento-da-wiki-e-teto-de-resolucao.md).

## Consequências

- O custo de armazenamento fica constante em ~1,9 GB, independente de quantos patches
  passem. O orçamento nunca é atingido por acúmulo.
- ~~O índice acumula, mas é barato: alguns MB por versão.~~ → **Errado, e é o que o
  [ADR 0013](0013-uma-versao-por-vez-no-indice.md) corrige.** Esta frase foi escrita quando
  o índice ia para um bucket. Com o índice no repositório, "acumular" custa 115 MB/ano que
  todo `git clone` paga, para sempre.
- O front precisa lidar com asset **sem** `storageKey` e com tipos ausentes em versões
  antigas. Isso é contrato, não caso de erro — está no JSON Schema.
- Uma versão antiga depende do ddragon estar no ar. É o mesmo risco que a §A.5 já
  aceitava para a indexação, e afeta só o modo histórico.
- O passo de remoção do patch anterior é destrutivo e roda sozinho no Actions. Precisa de
  teste e de trava: nunca apagar antes do índice novo estar publicado e verificado.
