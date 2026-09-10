# Sessão 09/09/2026 — Onda 4: categorias, filtros e lote

Dois tickets e uma correção de orçamento que apareceu no meio. Três PRs, CI verde antes de
cada merge.

| PR | Tickets | O que entrega |
|---|---|---|
| [#28](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/28) | **ADR 0015** | Teto do índice vai a 24 MiB, com os números medidos |
| [#29](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/29) | **T-24** | Navegação por categoria, filtros e listas virtuais |
| [#30](https://github.com/NihonCodingg/PROJETO-ASSETS-LOL/pull/30) | **T-25** | Seleção múltipla e zip montado no cliente |

**266 testes de vitest** (eram 180) e 298 Python. T-23 e T-26 seguem suspensos pelos
ADRs 0012 e 0013; T-30 e T-34 seguem bloqueados pelo design.

## A guarda que parou a primeira indexação completa

A primeira execução com **as duas fontes e as oito categorias** bateu no teto do RNF-05 e
**não escreveu nada** — local no 16.17.1 e de novo em produção no 16.18.1, que abriu sozinha
a issue #27 pelo T-12. Medido: **18.588,8 KiB** contra o teto de 15.360,0 KiB.

A guarda funcionou como projetada. O errado era o número: dos 15 MiB, **4,4 eram reserva
para versões antigas que o ADR 0013 eliminou** dois dias depois de o teto ser escrito, e a
conta nunca foi refeita.

Manter o teto custaria **chroma** (RF-06), **emote** ou **ward** — coisas que a pessoa vê e
baixa. Mudá-lo custa bytes de clone, que o ADR 0014 já mediu e aceitou nessa ordem de
grandeza: ~21 MiB/ano estimados contra os ~12 MiB/ano medidos, ~63 MiB em três anos. O
gatilho do plano B do 0014 continua onde estava.

**D4 da Spec fecha com "sim":** emotes (2.338) e wards (530) entram na v1, agora com os
bytes medidos em vez de prometidos.

De onde vêm os 8.429.360 bytes a mais, no 16.18.1:

| Categoria | Sem cdragon | Com cdragon | Diferença |
|---|---:|---:|---:|
| `champion` | 9.522 | 18.389 | **+8.867** |
| `emote` | — | 2.338 | **+2.338** |
| `ward` | — | 530 | **+530** |
| demais cinco | 6.026 | 6.026 | 0 |

## Dois filtros do RF-08 não existem, e isso está escrito

O RF-08 pedia filtros de "função, lane, comprável, mapa, árvore de runa e elo". Dois deles
não têm de onde sair:

- **`elo`** — a categoria `rank` saiu da v1 com o ADR 0012.
- **`lane`** — **nenhuma das duas fontes declara posição.** ddragon e cdragon dão as seis
  classes de campeão, não a lane. Escrever "Top/Jungle/Mid/ADC/Sup" à mão seria inventar
  dado, que é a única coisa que este projeto não faz.

O RF-08, o ticket e a Spec foram corrigidos com essa justificativa, em vez de deixar dois
filtros fantasma numa tabela de requisitos.

**`função` ficou, e mudou de lugar:** é atributo de campeão, e campeão é a home
(ADR 0010) — então o filtro vive na grade. Medido no catálogo real: Mago 75, Lutador 60,
Assassino 46, Tanque 46, Suporte 43, Atirador 33.

## Os grupos de filtro saem dos dados, não de uma lista

Um grupo é o que vem antes do `:` de uma `tag` que o T-21 escreveu; a opção é o que vem
depois. Nada é declarado no front: se a fonte parar de trazer `classe:*`, o grupo some
sozinho, sem código morto e sem filtro que não filtra nada.

O rótulo segue a mesma regra: `arvore:8000` vira "Precisão" **lendo o nome do próprio ícone
da árvore** na mesma fatia. A tabela fixa cobre só o vocabulário que o indexador inventou
(`mapa:sr`, `arvore:nenhuma`). `classe:damage` sai cru, em inglês — traduzir 30 tags à mão
seria inventar rótulo. A exceção são as **seis** funções de campeão, e a linha está escrita
no código: conjunto fechado, estável há dez anos, e o cliente do jogo em pt-BR usa
exatamente essas palavras.

## Duas coisas que quebrariam em silêncio

**5.042 nós no DOM.** O painel agora virtualiza acima de 200 cartões. Com os 5.042 ícones de
perfil e uma janela de 700 px, o DOM tem **12 `<article>`**. O teste empresta `offsetHeight`
ao jsdom de propósito: sem layout o virtualizador desenha **zero**, e zero passaria numa
asserção de "poucos nós" sem provar coisa nenhuma.

**Nome repetido no zip.** `zip.file()` sobrescreve em silêncio: 300 selecionados virariam
299 arquivos sem erro nenhum, e ninguém contaria. Colisão agora vira `(2)`, `(3)`.

## O lote, e o que ele faz quando algo falha

Falha de um arquivo **não derruba o lote** — abortar 300 por causa de um 404 é hostil. O que
não veio vai para um `FALHAS.txt` **dentro do zip**, com motivo e URL. Quem abrir vê o que
falta, em vez de contar 299 e não saber qual sumiu.

Chroma só entra em "tudo do Jax" **se estiver revelado**: com os chromas escondidos leva 3
assets, com o controle aberto leva 5. É o RF-06 valendo também para a seleção.

O aviso acima de 300 arquivos **informa e não bloqueia**, porque desde o ADR 0012 não há
zip por categoria para onde mandar quem selecionou demais.

## Correções de números

- A §6.1 da Spec dizia "3 minutos e meio" para os 5.042 ícones de perfil. Pela taxa que a
  própria linha declara (28 arquivos/s) são **3 min 1 s**. Corrigido junto com o teste.
- O RNF-05 dizia "10,6 MB medidos". Com as duas fontes são **19,0 MB**.

## Ficou pendente

- **T-38** (novo): o `decide` do `scheduling.py` compara só a versão do jogo, então T-21
  (etiquetas) e T-22 (emotes/wards) não chegariam ao índice publicado até a Riot lançar
  patch. A saída hoje é `workflow_dispatch` com `force`, que foi o que se usou. Fica para a
  Onda 5, ao lado do T-31, que também é sobre frescor do índice.
- **T-30 e T-34** seguem bloqueados: o design nunca chegou em `docs/design/`.
