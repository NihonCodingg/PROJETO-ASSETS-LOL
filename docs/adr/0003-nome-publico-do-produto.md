# ADR 0003 — Nome público do produto

- **Status:** aceito — **nome definido em 10/09/2026**
- **Data:** 2026-09-03 · nome escolhido em 2026-09-10
- **Contexto legal:** §B.5.1 do [KICKOFF](../KICKOFF.md) — Developer API Policy da Riot

## Contexto

A política da Riot proíbe usar "Riot" ou "League of Legends" como parte do nome do produto.
O nome de trabalho do projeto é `lol-assets`, e "LoL" é a abreviação corrente de
"League of Legends" — o suficiente para cair na mesma proibição.

Ao mesmo tempo, trocar o nome do repositório, dos pacotes e dos identificadores agora
custaria caro e não resolve nada: a política fala do **nome do produto apresentado aos
jogadores**, não do nome interno de um repositório privado de código.

## Decisão

1. O nome público do produto é **Biblioteca de Assets**, escolhido em 10/09/2026 junto com
   a ingestão do design — o arquivo do Claude Design já vinha nomeado assim, e o marcador
   `[ nome do produto ]` na barra lateral era o espaço reservado para ele.
2. Ele **não pode conter** "Riot", "League of Legends" nem "LoL". *Biblioteca de Assets*
   não contém nenhum dos três, e o teste de `site-config` verifica isso a cada execução.
3. O nome exibido vive em **um único lugar**: `apps/web/src/lib/site-config.ts`. O rótulo
   provisório ("Catálogo de Assets") saiu.
4. **Repositório, pacotes e identificadores ficam como estão**: `lol-assets`,
   `lol_assets_indexer`, `@lol-assets/schema`. Não são o nome do produto — e o repositório
   foi renomeado para `lol-assets` em 09/09/2026 justamente para combinar com eles.
5. O aviso legal obrigatório é gerado **a partir** do nome exibido, então acompanha a
   decisão automaticamente. O texto exato ainda precisa ser copiado literalmente da
   Developer API Policy — marcado `[A CONFIRMAR]` no mesmo arquivo.
6. Registrar o produto no Developer Portal antes do lançamento público, com o nome final.

## Consequências

- Nenhum trabalho de renomeação é necessário agora; o custo fica concentrado em uma
  constante e no dia do lançamento.
- Há exatamente um ponto de mudança quando o nome for escolhido, coberto por teste
  (`site-config.test.ts` verifica que o aviso legal existe e cita "Riot Games").
- Enquanto o placeholder estiver no ar, o site não pode ser divulgado publicamente —
  o lançamento depende desta decisão.
- Se o nome escolhido for muito diferente, o domínio e os handles precisam ser checados
  antes de fechar. Fora do escopo deste ADR.

## Por que este nome

- **Passa na regra sem esforço.** Não há uma palavra proibida perto dele, e não há como
  alguém confundi-lo com um produto da Riot.
- **Diz o que é.** Quem chega sabe em três palavras que é uma biblioteca e que o conteúdo
  são assets. O produto não tem onboarding: o nome é a única explicação que vem de graça.
- **Já era o nome do design.** O arquivo entregue se chama "Biblioteca de Assets v2", e a
  barra lateral tinha `[ nome do produto ]` reservado. Adotá-lo é fechar um ciclo, não
  abrir uma discussão.

## O que ainda depende disto

O **T-33** (checklist de lançamento) estava esperando esta decisão para duas coisas: o
registro do produto no Developer Portal e a conferência do texto legal `[A CONFIRMAR]`
contra a Developer API Policy.
