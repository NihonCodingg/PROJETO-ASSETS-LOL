# ADR 0005 — Arquitetura estática por padrão, custo de operação zero

- **Status:** aceito
- **Data:** 2026-09-03
- **Decidido por:** dono do projeto (mudança de escopo)
- **Afeta:** §A.5, §A.6, §A.7 e §0.3 do [KICKOFF](../KICKOFF.md)

## Contexto

O escopo mudou: o site é para **uso pessoal e de um pequeno grupo de amigos**, sem
monetização e sem ambição de público amplo. O custo de operação precisa ser **zero**, não
"próximo de zero".

Isso invalida a premissa por trás de metas como "custo próximo de zero até ~10 k
usuários/mês" (§A.7) e de um back-end no caminho crítico: um serviço sempre ligado exige
plano pago em qualquer host sério, e um plano gratuito que hiberna transforma o primeiro
acesso do dia em vários segundos de espera — exatamente o oposto da §A.4 item 6
("funciona com o Premiere aberto").

## Decisão

**Tudo o que o usuário toca é estático.**

1. **Front:** Next.js na **Vercel, plano Hobby**, que exige uso **não comercial** — o que
   este projeto satisfaz por decisão explícita (ver regra 6 abaixo).
2. **Assets e índice:** **Cloudflare R2**, tier gratuito — 10 GB de armazenamento e
   **egress zero**. O orçamento de 10 GB é tratado no [ADR 0007](0007-politica-de-versoes-e-orcamento.md).
3. **Indexação:** **GitHub Actions** em repositório público, onde os minutos são gratuitos.
   Roda por patch, publica no R2 e abre/atualiza o índice.
4. **A API FastAPI sai do caminho crítico.** O site precisa funcionar inteiro sem ela —
   busca, preview, download individual, download por categoria e download de seleção.
   Ver [ADR 0006](0006-api-como-componente-opcional.md).
5. **Zips:** por categoria são **pré-gerados pelo indexador** e ficam no R2 como qualquer
   outro arquivo estático. Seleção customizada é zipada **no cliente com JSZip**, usando os
   mesmos bytes que o navegador já baixou.
6. **O produto não será monetizado.** Sem anúncios, sem assinatura, sem doação vinculada
   aos assets. Isso mantém a conformidade com o plano Hobby da Vercel e simplifica a
   política da Riot, que exige registro e aprovação para qualquer monetização.

## Consequências

**Boas**

- Não existe servidor para cair, escalar, atualizar ou pagar. A resiliência da §A.5 passa
  a ser uma propriedade da arquitetura, não um requisito a perseguir.
- O JSZip deixa de ser "fallback offline" (§0.3) e vira o caminho principal da seleção
  customizada — menos código, não mais.
- Sem servidor no meio, o rate limit da §A.5 e o "cache por hash da seleção" deixam de
  existir como problema: não há o que abusar.
- O egress zero do R2 remove o último item de custo variável. Splash em alta deixa de ser
  risco financeiro.

**Ruins / custos aceitos**

- Zip de seleção customizada gasta memória do navegador. Para dezenas de splashes é
  tranquilo; para "tudo de todos os campeões" não é — por isso o zip **por categoria** é
  pré-gerado e servido pronto, e a interface deve empurrar o usuário para ele.
- O plano Hobby da Vercel proíbe uso comercial. Se um dia o projeto for monetizado, este
  ADR precisa ser revisado **antes**, junto com a política da Riot (§B.5.2).
- Sem back-end, não há como esconder nada: todo o índice é público. Não é problema — não
  há dado privado no projeto.
- Publicar no R2 exige credenciais no GitHub Actions. Ficam em secrets do repositório,
  nunca no código (regra 7).

## Alternativas descartadas

- **API sempre ligada em plano gratuito** (Fly, Railway, Render): hiberna, e o primeiro
  acesso paga o cold start. Custo zero só até o plano mudar de ideia.
- **Zip inteiramente no cliente, sem pré-gerar por categoria:** obriga o navegador a baixar
  centenas de MB para montar um arquivo que poderia estar pronto. Desperdiça banda do
  usuário para economizar espaço que o R2 dá de graça.
- **Servir os assets direto do ddragon, sem bucket:** joga o tráfego dos usuários na Riot,
  o que a §A.6 proíbe desde o início, e perde o controle sobre disponibilidade.
