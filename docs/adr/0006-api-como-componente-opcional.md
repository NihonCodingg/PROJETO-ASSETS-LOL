# ADR 0006 — A API FastAPI é componente opcional, não infraestrutura

- **Status:** aceito
- **Data:** 2026-09-03
- **Depende de:** [ADR 0005](0005-arquitetura-estatica-custo-zero.md)

## Contexto

A §A.6 do KICKOFF colocava a API FastAPI no caminho crítico: servir índices, gerar zips sob
demanda e expor metadados. A justificativa era dupla — funcionalidade e **portfólio de
back-end**.

Com o ADR 0005, a parte de funcionalidade desapareceu: índice e zips por categoria são
arquivos estáticos no R2, e seleção customizada é zipada no navegador. Sobra a
justificativa de portfólio, que é legítima mas não é infraestrutura.

## Decisão

1. A API **continua no repositório e no roadmap**, em `apps/api`, com Docker e testes.
2. Ela **roda localmente** (ou em qualquer host, quando alguém quiser), e **nada no site
   depende dela**. Nenhum fluxo do usuário pode assumir que ela existe.
3. Ela vira **um ticket próprio**, executado **depois** do caminho estático estar completo.
   Não bloqueia a v1 e não entra na primeira onda de tickets.
4. Escopo quando for feita: servir o índice a partir do bucket, gerar zip de seleção sob
   demanda, `/health` e `/versions`. Ou seja, uma alternativa ao caminho estático, não um
   complemento.
5. O `/health` que já existe fica: é o teste de fumaça que mantém o toolchain Python
   exercitado na CI.

## Consequências

- `apps/api` permanece na estrutura do monorepo (§0.3) e na CI. Custo: alguns segundos de
  pipeline. Benefício: o esqueleto não apodrece.
- O front **não pode** ganhar código que chame a API sem fallback estático. Isso vira
  critério de revisão de PR.
- O `.env.example` marca as variáveis da API como opcionais, para ninguém achar que
  precisa configurá-las para rodar o site.
- Se um dia a API for para produção, o ADR 0005 precisa ser revisitado antes — não por
  causa da API em si, mas por causa do custo que ela reintroduz.
