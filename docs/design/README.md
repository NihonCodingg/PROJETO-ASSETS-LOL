# docs/design — o desenho da interface

Esta pasta é o **destino do design feito no Claude Design** e a referência que o ticket
[T-30](../TICKETS.md) usa para vestir as telas. Até ela ter conteúdo, **T-34 e T-30 ficam
bloqueados**; todos os outros tickets de UI seguem executáveis, porque especificam
comportamento e não decisão visual.

> Estado atual: **vazia**. O commit das telas ainda não chegou ao repositório.

## Prefira código a imagem

**Mande HTML/CSS, não PNG.** A diferença não é de conveniência, é de exatidão:

| | HTML/CSS | PNG |
|---|---|---|
| Cores | valor exato (`#0b0b0e`) | estimado por amostragem, e o que se lê depende de compressão e de perfil de cor |
| Espaçamento | valor exato (`12px`, `1.5rem`) | medido a olho, em pixels de uma tela específica |
| Tipografia | família, peso, tamanho e entrelinha declarados | inferido da forma da letra |
| Raio, sombra, borda | declarados | aproximados |
| Estados (foco, hover, vazio, erro) | no mesmo arquivo | uma imagem por estado, ou nenhuma |

Um PNG obriga a **adivinhar** o sistema de design e depois escrever "cinza escuro ~#0b0b0e"
num documento que deveria ser exato. Com o HTML, `docs/design/TOKENS.md` sai por leitura,
não por estimativa — e o critério de aceite do T-34 é que o tema do Tailwind bata **valor a
valor** com ele, o que só é verificável se os valores forem exatos na origem.

Se só houver imagem, mande mesmo assim: serve para conferir layout e hierarquia. Mas os
tokens ficam marcados como estimados, e alguém vai ter que confirmá-los depois.

## O que vai aqui

```
docs/design/
├── README.md          este arquivo
├── TOKENS.md          escrito no T-34 a partir das telas (não à mão)
├── telas/             o HTML/CSS exportado, uma tela por arquivo
└── referencia/        o que o design importa: support.js, fontes, ícones
```

## Telas que os requisitos pedem

Cada linha aponta o requisito da [Spec](../SPEC.md) que depende dela. Falta de tela não
impede o ticket — impede só a etapa de vestir.

| Tela | Cobre |
|---|---|
| Home: grade de **campeões** (173), com arte da skin base e contagem de skins | RF-04 |
| Busca aberta, com resultado de **campeão** e de **skin** lado a lado | RF-01, RF-05 |
| Busca por termo transversal ("K/DA"), com skins de campeões diferentes | RF-24 |
| Painel do campeão com o **seletor de skin** | RF-25 |
| Painel com os **chromas** revelados pelo toggle | RF-06 |
| Ficha do asset: formato, resolução, tamanho e fonte, com **os dois botões** (original e PNG) | RF-09, RF-10, RF-11, RF-12 |
| Categoria com filtros | RF-08 |
| Seleção múltipla e download em lote | RF-17, RF-18 |
| Seletor de versão e o **modo histórico**, com os tipos ausentes explicados | RF-19, RF-20 |
| Estados: vazio, erro por asset, índice desatualizado | RF-20, T-31 |
| Rodapé legal e página "Sobre" | RF-21, RF-22 |

## Dois limites que o design precisa respeitar

1. **Não imitar o cliente do League of Legends** (§B.5.1 do [KICKOFF](../KICKOFF.md)). A
   política da Riot proíbe o produto se parecer com produtos dela em estilo ou função. Vale
   olhar com atenção a cor de destaque e a tipografia.
2. **Uma cor de destaque só.** É critério de aceite do T-34: um segundo acento faz o teste
   falhar.

Se alguma tela contradisser a Spec ou um ADR — em especial o
[ADR 0010](../adr/0010-navegacao-por-campeao-busca-por-skin.md) (navegação por campeão,
busca por skin) ou o [ADR 0001](../adr/0001-formato-de-entrega-dos-assets.md) (formato,
resolução e tamanho visíveis antes do download, com os dois botões), a divergência é
levantada e decidida — **a Spec não é adaptada ao design em silêncio**.
