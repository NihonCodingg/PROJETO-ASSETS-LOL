# ADR 0003 — Nome público do produto

- **Status:** aceito (o nome em si fica **[A DECIDIR]**)
- **Data:** 2026-09-03
- **Contexto legal:** §B.5.1 do [KICKOFF](../KICKOFF.md) — Developer API Policy da Riot

## Contexto

A política da Riot proíbe usar "Riot" ou "League of Legends" como parte do nome do produto.
O nome de trabalho do projeto é `lol-assets`, e "LoL" é a abreviação corrente de
"League of Legends" — o suficiente para cair na mesma proibição.

Ao mesmo tempo, trocar o nome do repositório, dos pacotes e dos identificadores agora
custaria caro e não resolve nada: a política fala do **nome do produto apresentado aos
jogadores**, não do nome interno de um repositório privado de código.

## Decisão

1. O **nome público do produto está [A DECIDIR]** e será definido antes do lançamento.
2. Ele **não pode conter** "Riot", "League of Legends" nem "LoL".
3. O marcador `[A DECIDIR]` vive em **um único lugar**: o nome exibido, em
   `apps/web/src/lib/site-config.ts`. Até a decisão, a interface usa um rótulo
   descritivo e neutro ("Catálogo de Assets"), que é claramente um placeholder e já
   respeita a restrição.
4. **Repositório, pacotes e identificadores ficam como estão**: `PROJETO-ASSETS-LOL`,
   `lol-assets`, `lol_assets_indexer`, `@lol-assets/schema`. Não são o nome do produto.
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
