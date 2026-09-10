# Sessão 10/09/2026 — vamos publicar

O pedido: o site no ar para o dono e alguns amigos, **aberto por URL, sem senha, sem
divulgação**. Executar o T-33, preparar tudo que não depende de conta, verificar se algo quebra
fora do `localhost`, e entregar separada a lista do que só o dono pode fazer.

| PR | Ticket | O que entrega |
|---|---|---|
| [#49](https://github.com/NihonCodingg/lol-assets/pull/49) | **T-33** 🟡 | Os dois avisos da Riot, copiados das políticas |
| [#50](https://github.com/NihonCodingg/lol-assets/pull/50) | **T-42** | O repositório pronto para a Vercel publicar |
| [#51](https://github.com/NihonCodingg/lol-assets/pull/51) | **T-43** | O site conferido fora do `localhost` |

**357 testes de vitest** (eram 338), **36 cenários e2e**, e um **build de produção em todo
PR** — que até hoje nunca tinha rodado na CI. Aberto e não executado: **T-44**, a faixa do topo
no telefone, que depende de design.

## O texto legal: duas políticas, não uma

O checklist mandava comparar o aviso com "a Developer API Policy". Baixei o HTML das páginas da
Riot e comparei caractere a caractere, e a comparação achou mais do que o checklist previa:

| Política | Pede | Estado antes |
|---|---|---|
| *General Policies* do Developer Portal (29/05/2025) | boilerplate obrigatório e visível | ✅ já publicado — bateu palavra por palavra |
| *Legal Jibber Jabber*, §6 (agosto de 2018) | aviso ao compartilhar projeto feito com arte da Riot | ❌ ausente |

As duas alcançam o site: ele usa o Data Dragon, que a política geral lista entre as
ferramentas do portal, e usa arte da Riot compartilhada com amigos. O Community Dragon — uma
das nossas fontes — publica o segundo aviso no próprio rodapé. Os dois ficam agora no rodapé de
toda página e em destaque na página Sobre, **em inglês e com `lang="en"`**.

- **Trava literal:** `site-config.test.ts` guarda os dois textos oficiais e falha se o publicado
  diferir em qualquer coisa além do marcador de lugar — inclusive `’` no lugar de `'`.
- **Variante descartada:** a documentação de LoL repete o boilerplate sem contrações e sem ponto
  final. A página de políticas é a normativa e tem data; é ela que o site segue.
- **O `[A CONFIRMAR]` saiu**, e a lista de marcadores pendentes chegou a zero.

E uma regra do nome passou a valer para o endereço: o *Legal Jibber Jabber* proíbe domínio com
marca da Riot, e o nome do projeto na Vercel **vira** subdomínio. O padrão sugerido seria
`lol-assets`; o projeto se chama **`biblioteca-de-assets`** — livre em 10/09.

## A Vercel e o pnpm que ela não conhece

O projeto usa pnpm 11.8.0; a Vercel suporta do 6 ao 10 e escolhe pela versão do lockfile. Com o
pnpm dela, o `allowBuilds` do workspace seria ignorado sem aviso. O `apps/web/vercel.json`
instala e builda com `npx --yes pnpm@11.8.0`, e um teste segura a versão junto do
`packageManager`. **A única configuração no painel é o Root Directory `apps/web`.**

Simulado com os comandos exatos, a partir de `node_modules` apagados: instalação em 29 s, build
em 33 s. O `conferir-publicacao.mjs` passou as 26 conferências no servidor de produção — e passa
em todo PR desde o #50.

## O cache que quebraria na Vercel

A §9 da Spec pedia 5 min de cache e um dia de `stale-while-revalidate` no manifesto. Na Vercel
isso quebra: cada deploy apaga os arquivos com hash do anterior, e um manifesto velho vindo do
cache apontaria para 404. O [ADR 0016](../adr/0016-publicacao-na-vercel.md) emendou: catálogo e
fatias imutáveis — o hash do nome é o do conteúdo, conferido byte a byte —, manifesto e status
sempre revalidam. Sem divulgação, toda resposta leva `noindex`.

## Fora do `localhost`

| | |
|---|---|
| Fetch do índice | ✅ mesma origem, sem CORS |
| CORS do ddragon e do cdragon | ✅ `*` para origem pública — por `curl` e por download real |
| Conteúdo misto, caminhos | ✅ nada `http://`, tudo relativo à raiz |
| Contexto seguro | ✅ download, PNG e zip não dependem; o "Copiar URL" depende, e a Vercel é HTTPS |
| Deploy com a página aberta | ❌ → ✅ a falha ficava memorizada; agora refaz e diz para recarregar |
| Tela de erro | ❌ → ✅ mandava o visitante rodar o indexador |

A prova foi num Chromium de verdade: `pnpm conferir:navegador` serve o build de produção como
`biblioteca-de-assets.test` e baixa das fontes reais, conferindo os bytes contra o `sha256` do
índice. **8 de 8**; o nono cenário, de HTTPS, só roda contra o site no ar.

Um detalhe do caminho: o Chromium sem janela ignora a flag que fingiria contexto seguro num
domínio HTTP — testado à parte. Em vez de brigar com ela, o cenário de HTTPS ficou para o modo
publicado, e o resto passou **sem** contexto seguro, o que prova mais do que provaria com ele.

## O telefone

Com os dois avisos, a faixa do topo no telefone de 390×844 mede **289 px** — um terço da tela
antes da busca. No desktop 1440×900 o rodapé cabe inteiro sem rolar. Mexer no telefone é
arquitetura de tela, e o design não desenhou telefone: virou o **T-44**, com a medição e os
caminhos anotados, sem executar.

## O que chegou ao `main` por fora

Dois commits entraram durante a sessão, e nenhum conflitou: o README reorganizado pelo dono
(`bafc646`) e um índice regenerado pelo `github-actions[bot]` (`cf5022b`) — justamente o tipo de
commit que a regra do Hobby poderia barrar.

## O que eu decidi sem perguntar

| Decisão | Por quê |
|---|---|
| Publicar os **dois** avisos | as duas políticas alcançam o site; faltar um é o único erro do projeto que não é bug |
| `noindex` por padrão | "sem divulgação"; uma variável desliga no dia de divulgar |
| Manifesto sempre revalida | o cache da Spec apontaria para 404 depois de cada deploy |
| pnpm fixado no `vercel.json`, não Corepack | Corepack é experimental e exigiria uma variável no painel |
| Registro como produto **pessoal** | o portal reserva o pessoal para o desenvolvedor e uma comunidade pequena e privada |
| Deploy hook como plano B **desligado** | a Vercel isenta repositório público da regra do dono; o bot deve publicar sozinho |
| Conferência no navegador **fora da CI** | fala com as fontes de verdade (§10 da Spec) |

## O que ficou com o dono

Tudo em [`docs/LANCAMENTO.md`](../LANCAMENTO.md), no topo, na ordem:

1. Criar o projeto na Vercel como `biblioteca-de-assets`, Root Directory `apps/web`, Deploy.
2. Rodar as duas conferências contra a URL.
3. Registrar no Developer Portal — descrição pronta para colar no D6 — e mandar o print.
4. Mandar o link de produção para os amigos. Só ele: as URLs com hash pedem login.

**Nenhuma variável de ambiente é obrigatória.**

## Riscos anotados

- **O commit do bot no Hobby.** A documentação diz que repositório público está livre da regra
  do dono, mas nenhum deploy existe ainda para confirmar. Se o primeiro patch novo não chegar ao
  ar, o script de conferência acusa, e o plano B é um segredo.
- **O repositório público se chama `lol-assets`.** O ADR 0003 dizia "privado"; corrigido. O §5
  do *Legal Jibber Jabber* fala de domínios e contas, não de repositório — risco baixo, escrito.
- **Página aberta durante um deploy** recebe o aviso de recarregar. A cura de raiz é a *Skew
  Protection*, fora do Hobby.
- **A faixa do topo no telefone** — T-44.

## Próximo passo sugerido

Criar o projeto na Vercel. Dali em diante, o que falta do T-33 é o print do registro — e o site
já está no ar.
