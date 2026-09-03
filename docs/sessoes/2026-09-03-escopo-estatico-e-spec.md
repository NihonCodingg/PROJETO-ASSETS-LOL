# Sessão 03/09/2026 — escopo estático, contrato do índice e Spec v1

Fecha a etapa 3 e entrega a etapa 4. Continuação de
[2026-09-03-adrs-e-prototipo](2026-09-03-adrs-e-prototipo.md).

## O que foi feito

### Mudança de escopo (commit `67a179a`)

Site de uso pessoal e de um pequeno grupo, sem monetização, custo de operação zero.

- **ADR 0005** — tudo que o usuário toca é estático: Vercel Hobby (não comercial),
  Cloudflare R2 (10 GB, egress zero), GitHub Actions em repositório público. Zips por
  categoria pré-gerados; seleção customizada zipada no cliente com JSZip. Produto não
  monetizado, o que mantém a conformidade com o Hobby e simplifica a política da Riot.
- **ADR 0006** — a API FastAPI sai do caminho crítico e vira componente opcional de
  portfólio, com Docker e testes, rodando localmente. Ticket próprio, depois do caminho
  estático. O `/health` fica, porque é o que mantém o toolchain Python vivo na CI.
- **ADR 0007** — só a versão atual tem assets copiados (~1,9 GB medidos, 19 % do tier
  gratuito). Anteriores existem só no índice. `pt_BR` primeiro, `en_US` se couber.
- KICKOFF: §0.3, §A.3, §A.5, §A.6 e §A.7 reescritas. As metas de escala de usuários e de
  custo por 10 k usuários saíram; entrou **R$ 0,00 por mês**.

### Contrato do índice e decisões da Spec (commit `10db262`)

- **ADR 0008** — a unidade do catálogo passa a ser a **skin** (~2.149), não o campeão
  (173). Seletor de skin na v1, gastando a folga do terceiro clique. Chromas (7.037) ficam
  dentro da skin-mãe, atrás de um toggle.
- **ADR 0009** — apelidos de busca em JSON estático mantido à mão, com **55 entradas**
  validadas contra o `champion.json` do patch 16.17.1. Sem gerador, sem script: o
  `apps/web` importa em tempo de build, então editar e dar merge já publica.
- **Contrato 1.0.0** em `packages/schema/schemas/`: `index-manifest.schema.json` e
  `index-shard.schema.json`. Cinco testes novos, incluindo um negativo.

### Spec v1 (commit `912b373`)

`docs/SPEC.md`: visão e não-objetivos, personas e 6 jobs to be done, **23 RF** com critério
de aceite testável, **12 RNF** com meta mensurável, arquitetura com 4 diagramas Mermaid,
contrato do índice, contrato resumido da API opcional, modelo de dados e política de
versões, cache e CDN, testes, observabilidade sem servidor, riscos e 7 decisões em aberto.

## O que foi assumido

- **Fatiamento do índice por categoria**, com hash no nome. A fatia `champion` é a única
  carregada na home e tem orçamento de 1,5 MB comprimida (RNF-03). O KICKOFF falava em
  NDJSON acima de 10 MB; fatiar resolve melhor, porque o problema real é a carga inicial.
- **Busca por normalização + tabela de apelidos**, não Fuse.js. O KICKOFF §0.3 previa
  Fuse.js; o protótipo mostrou que normalizar resolve quase tudo, e fuzzy tende a piorar a
  precisão do primeiro resultado, que é justamente a meta da §A.7. Fuse.js fica como
  segunda camada só quando não houver resultado.
- **Testes de rede nunca rodam em PR.** São lentos, instáveis e barulhentos com as fontes.
  Rodam agendados e a falha abre issue em vez de bloquear deploy.
- **Publicação atômica pela ordem**, sem transação: o `manifest.json` é o último a subir e
  o primeiro a ser lido; a remoção do patch anterior só acontece depois dele verificado.
- **Observabilidade sem servidor** = `status.json` no bucket + resumo do job + issue
  automática + aviso no site quando o índice passa de 72 h.
- **Emotes e ward skins entram na v1**, mas os bytes não foram medidos — é o único buraco
  do orçamento do RNF-05, e virou a decisão D4.

## Descoberta importante desta sessão

**Histórico de splash não existe.** Os spikes já tinham registrado que
`img/champion/splash/`, `centered/`, `loading/` e `tiles/` são servidos **sem versão na
URL**; ao escrever o ADR 0007 ficou claro o que isso implica: para versões anteriores, o
índice só pode oferecer os tipos realmente versionados (square, item, spell, passive,
profile_icon, map). Splash, loading e tile de patches antigos **não são recuperáveis** por
esta arquitetura. A §A.3 previa "squares/splashes de versões antigas" — os squares sim, os
splashes não. Está no RF-20: a UI diz por quê, em vez de servir a arte de hoje com rótulo
de ontem.

## Correção de bug

O padrão `data/` no `.gitignore` era amplo demais e escondia
`packages/schema/data/champion-aliases.json`, que é contrato e precisa ser versionado.
Ancorado na raiz (`/data/`).

## O que ficou pendente

As 7 decisões da §13 da Spec. As que travam alguma coisa:

1. **D3 — mover o repositório para caminho ASCII.** Trava o desenvolvimento web local.
   O passo a passo está na resposta desta sessão e no README.
2. **D1 e D6 — nome público e texto legal.** Travam o lançamento.
3. **D2 — consentimento da Weird Gloop.** Trava o tier de alta resolução.
4. **D4 — medir emotes e ward skins.** Trava fechar o orçamento do RNF-05.

## Próximo passo sugerido

Etapa 5 — quebrar a Spec em `docs/TICKETS.md`, em ondas. A primeira onda deve entregar o
caminho mais fino de ponta a ponta: indexar 1 campeão do ddragon → publicar índice → o
front buscar e baixar 1 square. O primeiro ticket apaga `prototype/`.
