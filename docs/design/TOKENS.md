# Tokens do design

> **Extraídos por leitura, não por estimativa.** Todo valor desta página foi lido de
> [`telas/biblioteca-de-assets-v2.html`](telas/biblioteca-de-assets-v2.html) — o
> [README desta pasta](README.md) pediu HTML justamente para que este documento fosse exato,
> e o critério 1 do **T-34** é o tema do Tailwind bater com ele **valor a valor**, verificado
> por teste.
>
> A `v1` fica como histórico. Quando o design mudar, muda aqui primeiro e o teste de paridade
> diz o que ficou para trás.

## Cor

A paleta é a escala **zinc** do Tailwind mais **violet** como acento, com quatro superfícies
quase-pretas próprias que não existem na escala. Os nomes abaixo são os do tema; a coluna
"no design" é onde o valor aparece.

### Superfícies

| Token | Valor | No design |
|---|---|---|
| `fundo` | `#09090b` | `html, body`, fundo da grade |
| `fundo-barra` | `#0a0a0c` | faixa do título da grade |
| `superficie` | `#0b0b0d` | barra lateral, painel do asset |
| `superficie-alta` | `#0f0f11` | paleta de busca (⌘K) |
| `superficie-lote` | `#101012` | bandeja do lote |
| `campo` | `#18181b` | `input`, cartão da bandeja, `hover` de item |
| `campo-alto` | `#212124` | tecla `/` do campo de busca |
| `selecionado` | `#1c1c1f` | categoria ativa na barra lateral |
| `acento-suave` | `#1e1b2e` | linha destacada da paleta |

### Bordas

| Token | Valor | No design |
|---|---|---|
| `borda` | `#1c1c1f` | divisórias entre seções |
| `borda-forte` | `#27272a` | contorno de campo, botão e painel |
| `borda-tecla` | `#2c2c30` | contorno da tecla `/` |
| `borda-fraca` | `#3f3f46` | caixa de seleção não marcada |

### Texto

Contraste calculado pela fórmula da WCAG 2.1, contra os dois fundos em que cada cor aparece.
**Os números são computados, não estimados** — o mesmo cálculo roda no teste do T-34.

| Token | Valor | s/ `#09090b` | s/ `#18181b` | AA? | No design |
|---|---|---:|---:|---|---|
| `texto` | `#fafafa` | 19,06 | 16,97 | ✅ | texto principal |
| `texto-forte` | `#e4e4e7` | 15,68 | 13,96 | ✅ | títulos de seção, rótulo de variante |
| `texto-medio` | `#d4d4d8` | 13,46 | 11,99 | ✅ | nome do asset no cartão |
| `texto-suave` | `#a1a1aa` | 7,76 | 6,91 | ✅ | rótulo secundário, botão fantasma |
| `texto-fraco` | `#71717a` | 4,12 | 3,67 | ❌ | metadado, nota, tecla |
| `texto-tenue` | `#52525b` | 2,57 | 2,29 | ❌ | rótulo de seção, contagem, dica |

> ⚠️ **Dois tokens do design não passam em AA. Divergência levantada e decidida.**
>
> `texto-fraco` (4,12) e `texto-tenue` (2,57) ficam abaixo do mínimo de **4,5:1** para texto
> normal, e não alcançam a exceção de texto grande (≥ 18pt, ou ≥ 14pt em negrito) porque no
> design aparecem em **9–11px**. O critério 4 do T-34 e o RNF-11 pedem AA, e a suíte de axe do
> **T-28** roda `color-contrast` como violação *serious* em quatro telas: aplicar essas cores
> em texto deixaria a CI vermelha. Não era questão de gosto.
>
> **Decisão de 10/09/2026 — clarear as duas.**
>
> | Uso no design | Cor do design | Cor que vai para a tela |
> |---|---|---|
> | metadado, nota, tecla, contagem, dica | `#71717a` / `#52525b` | **`#a1a1aa`** (6,91:1) |
> | borda, divisória, caixa não marcada, placa | `#52525b` / `#3f3f46` | inalterado — não é texto |
>
> `texto-fraco` e `texto-tenue` continuam **no tema**, porque são fiéis ao design e o teste de
> paridade os verifica. O que muda é onde podem ser usados: `--cor-texto-tenue` é reservado a
> borda e decoração, e há teste garantindo que nenhum componente o aplique a `color`.
>
> O custo é real e está aceito: a hierarquia de cinza fica um degrau mais rasa que a do
> desenho. O ganho é que a menor letra do produto continua legível.

### Acento — **um só**

| Token | Valor | No design |
|---|---|---|
| `acento` | `#8b5cf6` | botão primário, foco, `caret`, anel de seleção, `kicker` do painel |
| `acento-claro` | `#a78bfa` | `hover` do botão primário, link, subtítulo de skin |
| `acento-mais-claro` | `#c4b5fd` | `hover` de link, etiqueta "skin" |

Os três são o mesmo violeta em claridades diferentes (`violet-500/400/300`). O critério 3 do
T-34 — **uma** cor de destaque — está satisfeito: não há um segundo matiz de acento no
arquivo.

### Transparências

| Token | Valor | No design |
|---|---|---|
| `selecao-de-texto` | `rgba(139,92,246,0.35)` | `::selection` |
| `veu` | `rgba(9,9,11,0.6)` | fundo atrás do painel |
| `veu-forte` | `rgba(9,9,11,0.7)` | fundo atrás da paleta; caixa de seleção |
| `etiqueta-skin` | `rgba(30,27,46,0.85)` | fundo da etiqueta "skin" |
| `sombra-paleta` | `0 24px 60px rgba(0,0,0,0.6)` | elevação da paleta |
| `placa-texto` | `rgba(250,250,250,0.30 · 0.32 · 0.34)` | nome sobre a placa de miniatura |

## Tipografia

Duas famílias, e a divisão entre elas é semântica, não decorativa:

| Token | Família | Para quê |
|---|---|---|
| `fonte-interface` | `"Inter Tight", system-ui, sans-serif` | tudo que é linguagem |
| `fonte-mono` | `"JetBrains Mono", monospace` | **metadado técnico**: resolução, formato, bytes, contagem, tecla, rótulo de seção |

Pesos usados: **400**, **500**, **600**. Nenhum outro aparece no arquivo.

### Escala

| Token | Tamanho | No design |
|---|---:|---|
| `texto-9` | 9px | nome curto no strip de skins, etiqueta "skin" |
| `texto-10` | 10px | rótulo de seção, contagem, tecla, nota |
| `texto-11` | 11px | metadado, nome no cartão, dica |
| `texto-12` | 12px | botão, título de seção |
| `texto-13` | 13px | corpo, campo de busca, item de lista |
| `texto-14` | 14px | base do documento, campo da paleta, estado vazio |
| `texto-19` | 19px | título do painel |

### Entrelinha e espacejamento

| Token | Valor | Onde |
|---|---|---|
| `entrelinha-apertada` | `1.2` | título do painel |
| `entrelinha-cartao` | `1.25` / `1.3` | nome sobre a placa / nome do cartão |
| `entrelinha-solta` | `1.7` | rodapé da barra lateral |
| `espacejamento-titulo` | `-0.02em` | título do painel (19px) |
| `espacejamento-marca` | `-0.01em` | nome do produto |
| `espacejamento-rotulo` | `0.06em` | rótulo de seção em caixa alta |

## Raio

| Token | Valor | Onde |
|---|---:|---|
| `raio-min` | 3px | etiqueta "skin" |
| `raio-tecla` | 4px | tecla, placa da paleta |
| `raio-marca` | 5px | quadrado da marca |
| `raio` | 6px | **o padrão**: botão, campo, cartão, item de lista |
| `raio-medio` | 8px | prévia grande do painel |
| `raio-grande` | 10px | caixa da paleta |

## Altura de controle

| Token | Valor | Onde |
|---|---:|---|
| `controle-min` | 17px | caixa de seleção no cartão |
| `controle-xs` | 24px | seta de skin anterior/próxima |
| `controle-sm` | 26px | fechar painel |
| `controle-md` | 28px | botão de variante, botão do rodapé do painel |
| `controle` | 30px | botão da bandeja |
| `controle-lg` | 32px | campo de busca, botão do cabeçalho |
| `barra` | 36px | faixa do título da grade |
| `paleta-rodape` | 34px | rodapé da paleta |
| `paleta-campo` | 44px | campo da paleta |
| `cabecalho` | 48px | cabeçalho e topo da barra lateral |
| `bandeja` | 52px | bandeja do lote |

## Espaçamento

O design usa uma escala de 4 com dois valores ímpares deliberados (5 e 7) em espaços
apertados de cartão. `gap` da grade: **6px**. `padding` de seção: **14px**.

| Valor | Onde |
|---|---|
| 2, 3, 4 | ajustes finos dentro de cartão e etiqueta |
| 5, 6, 7 | `gap` da grade, espaço entre botões, respiro do cartão |
| 8, 10, 12, 14 | `gap` de seção e `padding` de container |
| 18, 24, 26 | respiros grandes do painel |

## Largura

| Token | Valor | Onde |
|---|---:|---|
| `barra-lateral` | 208px | coluna da esquerda |
| `busca-max` | 560px | campo de busca do cabeçalho |
| `paleta-max` | `min(620px, 88%)` | caixa da paleta |
| `painel` | `min(540px, 74%)` | painel do asset |
| `alvo-cartao-denso` | 152px | largura-alvo do cartão (modo denso) |
| `alvo-cartao-confortavel` | 210px | largura-alvo do cartão (modo confortável) |

## Movimento

Uma animação só no arquivo inteiro:

```css
@keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.45 } }
```

`1.2s ease-in-out infinite`, com atraso escalonado por coluna (`0.06s` por índice), usada
**só** no esqueleto de carregamento.

## Foco

```css
:focus { outline: none }
:focus-visible { outline: 2px solid #8b5cf6; outline-offset: 1px }
```

O anel de foco é o acento. Cartão e item selecionados usam `outline: 2px solid #8b5cf6` com
`outline-offset: 2px` — o mesmo desenho, aplicado a estado em vez de foco.

## Os rótulos das variantes, corrigidos

O mock rotula **1280×720** como "corte do cliente" e **1215×717** como "corte centralizado" —
o inverso do [ADR 0002](../adr/0002-nomes-canonicos-de-corte-de-splash.md), que é medido e
reverificado todo dia pelos testes de contrato das fontes.

**Decisão de 10/09/2026:** as palavras do design ficam, no tipo certo. A troca no mock é dado
de exemplo errado, não decisão de design.

| Tipo no índice | Resolução medida | Rótulo na tela |
|---|---|---|
| `splash_centered` | 1280×720 | Splash — corte centralizado |
| `splash_wide` | 1215×717 | Splash — corte do cliente |

## O que este documento **não** decide

O design não desenhou quatro coisas que os requisitos exigem. Elas **não** são inventadas
aqui — o T-30 as desenha com os tokens desta página e os padrões que já existem no arquivo,
sem criar um segundo sistema:

1. **Rodapé legal da Riot** (RF-21) — obrigatório em toda página, e o layout do design é
   `100vh` sem rodapé. **Decidido em 10/09/2026:** vai no pé da barra lateral, onde hoje
   ficam as contagens, com link para a página "Sobre".
2. **Chromas atrás de um controle** (RF-06).
3. **Filtros de categoria** (RF-08) — a barra lateral navega categorias, mas não filtra
   dentro delas.
4. **Aviso de índice velho** (T-31) e **erro por asset**.

O design também expõe uma densidade de grade (`densa` / `confortável`) que nenhum requisito
pede. Fica registrada como **T-40**, não construída no T-30.
