# Sessão 10/09/2026 — o design entra

O bloqueio mais antigo do projeto caiu. `docs/design/` deixou de estar vazio, e com ele
saíram os dois últimos tickets de produto.

| PR | Ticket | O que entrega |
|---|---|---|
| [#42](https://github.com/NihonCodingg/lol-assets/pull/42) | **T-34** | Tokens, base de componentes e o nome público |
| [#43](https://github.com/NihonCodingg/lol-assets/pull/43) | **T-30** | O design aplicado sobre o comportamento já testado |
| [#44](https://github.com/NihonCodingg/lol-assets/pull/44) | **T-33** 🟡 | Checklist de lançamento — a metade que não depende de conta |

**334 testes de vitest**, **328 Python** e **32 cenários e2e**, com o axe varrendo cinco
telas.

## Os tokens foram lidos, não estimados

O README de `docs/design/` pedia HTML em vez de PNG, e o pedido se pagou: `TOKENS.md` saiu
por leitura do arquivo — 22 cores, 6 raios, 11 alturas de controle, 7 tamanhos de texto,
nenhum aproximado. O teste de paridade compara nos dois sentidos, porque token no tema que
não está no documento e token no documento que não está no tema são defeitos diferentes com
a mesma causa.

## Três divergências, levantadas antes de executar

O README daquela pasta manda levantar e perguntar em vez de adaptar qualquer lado em
silêncio. Foram três, e as três foram decididas pelo dono:

### Contraste — a que travava a CI

`#71717a` dá **4,12:1** e `#52525b` dá **2,57:1** contra o mínimo de 4,5, nos 9–11px em que o
design os usa. Não era gosto: a suíte de axe do T-28 roda `color-contrast` como *serious*, e
aplicá-los deixaria a CI vermelha.

**Decidido clarear.** Metadado e contagem passam a `#a1a1aa` (6,91:1). Os dois cinzas
continuam no tema — o teste de paridade os verifica — e há teste garantindo que não virem
`color`. O custo está aceito e escrito: a hierarquia de cinza fica um degrau mais rasa.

### ADR 0002 — a inversão que o ADR existe para impedir

O mock rotulava **1280×720** como "corte do cliente" e **1215×717** como "corte
centralizado" — o inverso do contrato medido e reverificado todo dia pelos testes das fontes.
**Decidido corrigir o mapeamento**, mantendo as palavras do design, que são boas.

### Rodapé legal — o que o design não desenhou

Layout `100vh` em duas colunas, sem rodapé; o RF-21 exige o aviso em toda página.
**Decidido: pé da barra lateral.**

## §B.5.1 — o design não imita o cliente do jogo

Conferido antes de vestir: violeta `#8b5cf6` sobre zinc, Inter Tight e JetBrains Mono, raios
de 6px, superfícies chapadas. O cliente do LoL é dourado sobre azul-marinho, tipografia
serifada e moldura hextech. Não há proximidade a discutir.

## Três coisas que o axe pegou e nenhum teste de unidade pegaria

1. **O botão primário tinha perdido a cor do texto.** `cn("bg-acento text-superficie",
   "text-12")` — o `tailwind-merge` não sabe que `text-12` é tamanho e `text-superficie` é
   cor, e descartou a segunda. O botão herdou o branco do corpo: **3,1:1** sobre o violeta em
   vez de 4,64:1. O teste de tokens compara valores e passou. Quem viu foi o axe, no
   navegador, onde as classes viram cor.
2. **Link distinguível só por cor** (WCAG 1.4.1). O design usa `text-decoration: none`; dentro
   de bloco de texto isso reprova.
3. **O `Dialog` do Radix mudou comportamento sem avisar.** Passou a fechar por `Escape`
   atropelando a ordem chroma-primeiro, e por clique fora, que o painel nunca teve. Dois
   testes de onda anterior caíram na hora — que é exatamente para isso que o critério 1 do
   T-30 existe.

## A prova de que só a aparência mudou

Os **325 testes de vitest e os 28 cenários e2e** das ondas anteriores passam **sem uma linha
alterada**. Foi o critério 1 do T-30, e é o que separa "vestir" de "reescrever".

Quatro cenários novos cobrem tela estreita a 375px, incluindo *nada transborda na
horizontal* e *o aviso legal continua inteiro* — "visível" com reticências não é visível.

## Uma adaptação ao dado real

O cartão do campeão é **1:1**, não o 16:9 do mock. A miniatura é o `square` de 128×128 do
ddragon; cortá-la em 16:9 tiraria 44% da altura, que é onde está o rosto. O mock usava splash
art, que já nasce 16:9.

## O nome público

**Biblioteca de Assets** — o nome do próprio arquivo do design, e o que o marcador
`[ nome do produto ]` da barra lateral reservava. Fecha o **ADR 0003**, que estava
`[A DECIDIR]` desde 03/09, e destrava o T-33.

## O lançamento, e o que ele espera de gente

O gatilho do T-33 foi puxado. Tudo que não depende de conta ou dinheiro está feito;
[`docs/LANCAMENTO.md`](../LANCAMENTO.md) marca com 🔑 os três itens que não:

1. comparar o aviso com a Developer API Policy **palavra a palavra**;
2. registrar o produto no Developer Portal;
3. contratar o domínio.

O teste de marcadores não fica vermelho por causa do `[A CONFIRMAR]` que resta — ele falha
por marcador **novo** sem justificativa, e por lista desatualizada. Suíte vermelha por
semanas é suíte que ninguém lê.

## Ficou pendente

Três tickets, todos com o gatilho escrito:

- **T-39** — a fatia `champion` está a 5,4% do limite do RNF-03; estoura em ~33 patches.
- **T-40** — a densidade de grade que o design expõe e nenhum requisito pede.
- **T-41** — a navegação unificada na barra lateral. O design trata "Campeões" como a
  primeira categoria e mostra uma grade por vez; hoje são duas navegações empilhadas. O T-30
  não fez porque mudaria o que os testes do T-19 e do T-24 afirmam — e o critério 1 dele
  proibia alterá-los. **É a única divergência de arquitetura de informação que sobrou entre o
  design e o site.**

Uma observação de suíte: um teste de componente falhou **uma vez**, rodando junto com a
suíte Python na mesma máquina, e não reproduziu em três execuções isoladas nem na CI. Fica
anotado como sensibilidade a disputa de CPU, não como defeito conhecido.
