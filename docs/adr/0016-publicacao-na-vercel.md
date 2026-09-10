# ADR 0016 — Publicação na Vercel

- **Status:** aceito
- **Data:** 2026-09-10
- **Pedido do dono:** "no ar para mim e alguns amigos, aberto por URL, sem senha, sem divulgação"

## Contexto

O [ADR 0005](0005-arquitetura-estatica-custo-zero.md) escolheu a Vercel Hobby, e o
[ADR 0014](0014-onde-vive-o-indice-gerado.md) pôs o índice em `apps/web/public/indice`,
dentro do app. Faltava a configuração em si, e ela esbarrou em quatro coisas que só aparecem
quando o site sai do `localhost`:

1. **O pnpm.** O projeto usa pnpm 11.8.0 (`packageManager`). A Vercel suporta do 6 ao 10 e
   escolhe pela versão do lockfile: `9.0` vira pnpm 9 ou 10. O pnpm 10 não lê o
   `allowBuilds` do `pnpm-workspace.yaml`, que é sintaxe do 11 — e não avisa.
2. **O cache do índice.** A §9 da Spec pedia `max-age=300, stale-while-revalidate=86400`
   para o manifesto. Na Vercel isso quebra: cada deploy é **atômico**, e os arquivos com hash
   do deploy anterior deixam de existir no endereço de produção. Um manifesto velho vindo do
   cache do navegador aponta para catálogo e fatias que já não existem — 404 na primeira
   categoria aberta, até alguém recarregar. A §9 foi escrita para um bucket, que guardava os
   arquivos antigos; o [ADR 0012](0012-onde-guardar-os-assets.md) tirou o bucket.
3. **A divulgação.** A Vercel marca `noindex` só nos previews. O endereço de produção é
   indexável por padrão.
4. **O commit do bot.** No Hobby, só commit do dono da conta dispara deploy. A documentação da
   Vercel diz que a regra vale para repositório privado, e que a colaboração é livre em
   repositório público — que é o caso. O workflow do índice commita como
   `github-actions[bot]`, e nenhum deploy foi feito ainda para confirmar na prática.

## Decisão

1. **Root Directory `apps/web`**, com a configuração em `apps/web/vercel.json` — é de lá que
   a Vercel lê quando o Root Directory é um subdiretório.
2. **O pnpm do projeto, fixado no `vercel.json`:** instalação e build rodam com
   `npx --yes pnpm@11.8.0`. Um teste compara a versão com o `packageManager`; trocar um sem o
   outro deixa a CI vermelha. O Corepack da Vercel (`ENABLE_EXPERIMENTAL_COREPACK=1`) faria o
   mesmo, mas é marcado experimental e exigiria uma variável no painel — um passo manual a
   mais, invisível no repositório.
3. **Nenhuma variável de ambiente é obrigatória.** Os padrões do código são os de produção.
4. **Cache:** catálogo e fatias — nome com o hash do conteúdo, conferido em teste — levam
   `public, max-age=31536000, immutable`. `manifest.json` e `status.json`, nome fixo, levam
   `public, max-age=0, must-revalidate`: revalidar custa um 304 de 2,5 KB por visita.
   **Emenda a §9 da Spec.**
5. **Sem divulgação por padrão:** `X-Robots-Tag: noindex, nofollow` em toda resposta —
   inclusive nos JSON do índice, que o `<meta>` do HTML não alcança — e `<meta name="robots">`
   no HTML. `NEXT_PUBLIC_SITE_INDEXABLE=true` desliga os dois no dia em que o dono quiser
   divulgar. Não há `robots.txt` com `Disallow`: ele impediria o buscador de ler o `noindex`,
   e um link externo bastaria para a URL aparecer mesmo assim.
6. **A proteção padrão da Vercel fica** (*Standard Protection*): o domínio de produção é
   público; as URLs de cada deploy e os previews pedem login na Vercel. O endereço a
   compartilhar é **só** o de produção.
7. **O commit do bot publica pela integração do Git.** Plano B pronto e desligado: se a
   Vercel recusar o commit do bot, o dono cria um *deploy hook* e guarda a URL no segredo
   `VERCEL_DEPLOY_HOOK`. O workflow do índice chama o hook depois do push; sem o segredo, o
   passo não roda.
8. **A CI passa a buildar para produção.** O e2e sobe `next dev`, e até 10/09/2026 o build de
   produção nunca tinha rodado — passou na primeira, em 85 s. Agora roda em todo PR, e o
   servidor de produção do Next é conferido pelo mesmo script que o dono roda contra a URL
   publicada (`apps/web/scripts/conferir-publicacao.mjs`).

## Consequências

- Publicar é criar o projeto e apontar o Root Directory. O passo a passo está em
  [`docs/LANCAMENTO.md`](../LANCAMENTO.md).
- Trocar a versão do pnpm são dois lugares — `packageManager` e `vercel.json` —, e o teste
  segura os dois juntos.
- Quem está com a página aberta durante um deploy e abre uma categoria que ainda não tinha
  aberto recebe 404: o arquivo do deploy anterior sumiu. A Vercel tem *Skew Protection* para
  isso, fora do plano Hobby. O site trata o 404 dizendo o que aconteceu (T-43).
- `noindex` é o padrão, e continua sendo o padrão para o dia em que alguém esquecer que ele
  existe: divulgar exige ligar uma variável, não um descuido.
- Se o plano B for necessário, ele fica escrito no mesmo lugar em que o problema aparece: o
  script de conferência acusa quando o site no ar está num índice diferente do repositório.
