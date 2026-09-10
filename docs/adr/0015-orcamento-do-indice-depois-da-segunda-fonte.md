# ADR 0015 — O orçamento do índice depois da segunda fonte

- **Status:** aceito
- **Data:** 09/09/2026
- **Emenda:** [ADR 0007](0007-politica-de-versoes-e-orcamento.md) e
  [ADR 0013](0013-uma-versao-por-vez-no-indice.md) na parte do teto de 15 MiB
- **Decorre de:** [ADR 0012](0012-onde-guardar-os-assets.md) (o índice mora no repositório)
- **Toca:** RNF-05, D4 da Spec, `packages/indexer/src/lol_assets_indexer/limits.py`

## Contexto

A primeira indexação com **todas as fontes e todas as categorias** — ddragon mais cdragon,
emotes e ward skins incluídos — parou na guarda do RNF-05 e **não escreveu nada**. Duas
vezes: local, no 16.17.1, e em produção, no 16.18.1
([execução 34406397338](https://github.com/NihonCodingg/lol-assets/actions/runs/34406397338),
que abriu sozinha a issue #27 pelo T-12).

```
orçamento do índice estourado; nada foi escrito:
  - o índice desta versão tem 18.588,8 KiB escritos, 3.228,8 KiB acima do
    limite de 15.360,0 KiB (RNF-05)
```

A guarda funcionou exatamente como projetada: mediu, recusou, disse o número e avisou. A
pergunta que sobra é qual dos dois lados está errado — o índice ou o limite.

### O que foi medido

| | Patch | Assets | Bytes escritos |
|---|---|---:|---:|
| Só ddragon, sem etiquetas (o que está publicado) | 16.18.1 | 15.548 | 10.605.571 |
| Só ddragon, com as etiquetas do T-21 | 16.17.1 | 15.515 | 10.725.235 |
| ddragon + cdragon, 8 categorias | 16.17.1 | 27.250 | 19.013.632 |
| **ddragon + cdragon, 8 categorias (produção)** | **16.18.1** | **27.283** | **≈19.034.931** |
| Limite do RNF-05 | — | — | 15.728.640 |

De onde vêm os 8.429.360 bytes a mais, no 16.18.1. Só três categorias mudam, e nenhuma
delas por acaso:

| Categoria | Sem cdragon | Com cdragon | Diferença |
|---|---:|---:|---:|
| `champion` | 9.522 | 18.389 | **+8.867** (chromas, `loading_vintage`, splashes exclusivos) |
| `emote` | — | 2.338 | **+2.338** |
| `ward` | — | 530 | **+530** |
| `item`, `map`, `profile_icon`, `rune`, `summoner_spell` | 6.026 | 6.026 | 0 |
| **total** | **15.548** | **27.283** | **+11.735** |

Os 8.867 registros de campeão a mais são **6.994 chromas** (RF-06) mais os tipos que só o
cdragon declara. Emotes e wards são a resposta ao **D4 da Spec**, que sempre foi "sim,
mas meça os bytes primeiro" — os bytes foram medidos e são estes.

Entre os dois patches o índice completo cresceu **21.299 bytes** (33 assets). É a escala
real de crescimento por patch, e é ela que dimensiona a folga escolhida abaixo.

### De onde veio o 15 MiB

Do T-10, e a conta está escrita no `limits.py`: 10,6 MB medidos no 16.17.1 **mais ~3 MB
que o T-11 ia empilhar por versão antiga**. O [ADR 0013](0013-uma-versao-por-vez-no-indice.md)
matou as versões antigas dois dias depois e o teto nunca foi refeito: desde então, 4,4 MiB
dos 15 estavam reservados para uma coisa que não existe mais.

O 15 MiB nunca foi um limite do produto. É a guarda contra um bug que duplique registros ou
uma fonte que exploda — o mesmo papel de um `assert`, com o número escolhido para dar folga
sobre a medição da época.

## Decisão

**O teto do RNF-05 passa de 15 MiB para 24 MiB de bytes escritos por versão.**

Os outros dois limites do RNF-03 **não mudam**: o catálogo continua em 150 KiB gzip e a
maior fatia em 1,5 MiB gzip. Ela é a próxima a apertar, e é de propósito que o limite dela
não subiu junto: essa é a que o navegador paga.

> **Medido na publicação real** (16.18.1, execução 34425113348): índice de **19.034.271
> bytes** (18,15 MiB) — a estimativa deste ADR errou por 660 bytes. Catálogo em 63,5 KiB
> gzip, com folga larga. A fatia `champion` ficou em **1.488.627 bytes gzip contra o limite
> de 1.572.864**: passa com **5,4% de folga**, não os 8% estimados acima. A ~2,5 KiB gzip
> por patch, ela estoura em cerca de **33 patches** — pouco mais de um ano. Ver o T-39.

## Por quê

1. **Manter o teto mudaria o produto; mudar o teto não muda.** Para caber em 15 MiB seria
   preciso cortar os chromas (RF-06), ou emotes e wards (D4), ou os ícones de perfil. Todos
   são coisas que a pessoa vê e baixa. O teto é um número interno.
2. **O número velho estava errado pela metade.** 4,4 MiB dele eram reserva para versões
   antigas que o ADR 0013 eliminou.
3. **24 MiB é folga de alarme, não de conforto.** Sobre os 18,15 MiB medidos são ~32%.
   Medido entre 16.17.1 e 16.18.1, um patch acrescenta ~21 KiB: a folga dá para **cerca de
   280 patches**, ou mais de dez anos, e continua pequena o bastante para um bug que
   duplique a fatia `champion` estourar na hora.
4. **O custo é de clone, e já foi aceito nessa ordem de grandeza.** O
   [ADR 0014](0014-onde-vive-o-indice-gerado.md) mediu 78 patches simulados: ~12 MiB/ano de
   histórico com o índice em 10,6 MB. Escalando pelo tamanho — **estimativa, não medição** —
   um índice de 19,0 MB dá ~21 MiB/ano, ~63 MiB em três anos. É um limite superior: os
   registros que o cdragon acrescenta (chroma, emote, ward) mudam **menos** entre patches
   que os splashes, então o delta real cresce menos que proporcionalmente. O gatilho do
   plano B do ADR 0014 — branch órfão com force-push — continua onde estava, e 63 MiB não
   chega perto dele.

## Consequências

- O diretório do índice passa de ~10,6 MB para **~19,0 MB**, constante (ADR 0013 continua
  valendo: uma versão só).
- A publicação do índice fica **maior que o limite antigo**: quem tinha o índice publicado
  antes desta mudança precisa de uma indexação forçada para ganhar chromas, emotes e wards.
- O RNF-03 vira o limite que aperta primeiro, e ele é o que importa mais: é o navegador que
  paga. Quando a fatia `champion` estourar 1,5 MiB gzip, a saída não é subir o número — é
  fatiar `champion` por tipo, e isso é ticket, não emenda de ADR.
- A guarda continua sendo a única coisa que impede o índice de crescer sem ninguém ver.
  Ela parou uma execução de 22 minutos sem escrever um byte, que é exatamente o
  comportamento pedido.

## Alternativas consideradas

- **Cortar os ícones de perfil** (5.042 registros, 2,7 MB). Era o corte previsto pelo
  ADR 0007 quando o orçamento era de armazenamento. Economiza 2,7 dos 3,2 MB que faltavam —
  não resolve sozinho, e tira uma categoria inteira do produto para poupar bytes que o Git
  nem sente.
- **Cortar os chromas.** Resolveria com folga (6.994 registros), e mata o RF-06.
- **Não indexar emotes e wards.** Reabriria o D4 já respondido, com a medição em mãos
  dizendo que cabem.
- **Comprimir o índice em disco** (`.json.gz` commitado). O Git já comprime o que guarda; o
  ganho seria no *working tree*, não no clone, e o front passaria a precisar descomprimir à
  mão o que a Vercel já entrega comprimido.
- **Subir o teto para 20 MiB.** Cabe hoje com 10% de folga, o que faz a guarda virar alarme
  falso na primeira temporada de skins.
