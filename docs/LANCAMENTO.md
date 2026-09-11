# Checklist de lançamento

O que separa o site que roda na sua máquina do site no ar, aberto por URL para você e alguns
amigos.

> **Estado em 11/09/2026: no ar.** O projeto `biblioteca-de-assets` foi criado na Vercel (time
> `nihon2`), ligado ao repositório, com Root Directory `apps/web`, e o domínio de produção abre
> sem login. Conferido contra a URL publicada: **26 de 26** por HTTP e **9 de 9** no navegador.
> O que falta é o registro na Riot (D6), marcado com 🔑.

## Publicar — o que você faz, na ordem

> Os passos 1 a 3 foram feitos em 11/09/2026, pela CLI da Vercel já logada na sua conta e com a
> sua autorização. Ficam aqui para refazer do zero, se um dia for preciso.

Tudo que depende de código já está no repositório
([ADR 0016](adr/0016-publicacao-na-vercel.md)). O que sobra são contas suas, e nenhum passo
pede para colar segredo em lugar nenhum além do próprio painel.

### 1. Criar o projeto na Vercel

1. Entre em <https://vercel.com> com **Continue with GitHub**, usando a conta dona do
   repositório (`NihonCodingg`). Plano **Hobby**, o gratuito. Tem de ser a mesma conta: no
   Hobby, a Vercel publica commit de quem é dono da conta.
2. **Add New… → Project.** Em *Import Git Repository*, autorize o app da Vercel no GitHub —
   dá para limitar a *Only select repositories* → `lol-assets` — e clique **Import** em
   `NihonCodingg/lol-assets`.
3. Na tela *Configure Project*:

   | Campo | Valor |
   |---|---|
   | Project Name | **`biblioteca-de-assets`** — não o `lol-assets` que ela sugere (ver D7) |
   | Framework Preset | Next.js |
   | Root Directory | **Edit** → `apps/web` |
   | Build and Output Settings | não mexa: o `apps/web/vercel.json` já diz como instalar e buildar |
   | Environment Variables | nenhuma |

4. **Deploy.** O build leva uns 3 minutos. No fim, a Vercel mostra o domínio de produção —
   `biblioteca-de-assets.vercel.app`, se o nome estiver livre.

**Se o build falhar na instalação**, confira em *Settings → Build and Deployment → Root
Directory* se *Include files outside the root directory in the Build Step* está **Enabled** —
é o padrão, e o front depende de `packages/schema`, que mora fora de `apps/web`.

### 2. Conferir

Na pasta do repositório, com a URL que a Vercel deu:

```bash
node apps/web/scripts/conferir-publicacao.mjs https://biblioteca-de-assets.vercel.app
```

Ele confere os dois avisos, o `noindex`, o cache do índice e se o site está no mesmo índice do
seu clone. Tudo `ok` é publicado certo.

E, num navegador de verdade, o que o script não alcança — baixar das duas fontes a partir do
domínio publicado, converter para PNG, montar um zip:

```bash
URL_PUBLICADA=https://biblioteca-de-assets.vercel.app pnpm -C apps/web conferir:navegador
```

No PowerShell: `$env:URL_PUBLICADA="https://biblioteca-de-assets.vercel.app"; pnpm -C apps/web conferir:navegador`.
São 9 cenários, e eles baixam meia dúzia de arquivos do ddragon e do cdragon. Sem
`URL_PUBLICADA`, ele confere o build da sua máquina num domínio falso — tudo menos o HTTPS.

### 3. O que compartilhar — e o que não

- **Só o domínio de produção** (`biblioteca-de-assets.vercel.app`). Ele é aberto, sem senha.
- As URLs longas, com hash — de cada deploy e dos previews de PR — pedem login na Vercel. É a
  *Standard Protection*, que já vem ligada; deixe como está.
- Os endereços com o sufixo do time (`biblioteca-de-assets-nihon2.vercel.app`) também pedem
  login: a proteção do time é `all_except_custom_domains`, e só o domínio de produção fica aberto.
  Conferido em 11/09/2026 — o domínio de produção responde 200, o com sufixo redireciona para o
  login.
- O site não aparece em buscador: toda resposta leva `noindex`. Também não ponha a URL no
  README nem no campo *Website* do repositório, que é público.

### 4. Registrar na Riot

Com a URL em mãos, o passo a passo do D6, mais abaixo — antes de mandar o link para os
amigos.

### Variáveis de ambiente

**Nenhuma obrigatória.** As opcionais vão em *Settings → Environment Variables*, e pedem um
redeploy depois — o Next grava as `NEXT_PUBLIC_` no build:

| Variável | Quando |
|---|---|
| `NEXT_PUBLIC_SITE_INDEXABLE=true` | no dia de divulgar: tira o `noindex` |
| `NEXT_PUBLIC_WIKI_CONSENT_GRANTED=true` | se o consentimento da Weird Gloop chegar (D2) |

### Se um patch novo não chegar ao ar — plano B

O workflow do índice commita como `github-actions[bot]`. Em repositório público a Vercel
publica esse commit. Se um dia deixar de publicar, o sintoma aparece no passo 2: depois de um
`git pull`, o script diz que o site está num índice diferente do repositório. Aí:

1. Vercel → projeto → **Settings → Git → Deploy Hooks**: nome `indice`, branch `main`,
   **Create Hook**. Copie a URL.
2. GitHub → repositório → **Settings → Secrets and variables → Actions → New repository
   secret**: nome `VERCEL_DEPLOY_HOOK`, valor a URL.

Daí em diante o workflow chama o hook depois de cada commit do índice. A URL publica o seu
site: não cole em mais lugar nenhum.

## D1 — Nome público ✅

Decidido em 10/09/2026: **Biblioteca de Assets**
([ADR 0003](adr/0003-nome-publico-do-produto.md)).

Vive num lugar só, `apps/web/src/lib/site-config.ts`, e os avisos legais são derivados dele —
se o nome mudar, os avisos acompanham. Dois testes seguram:

- o nome não contém "Riot", "League of Legends" nem "LoL";
- o nome não é mais o rótulo provisório "Catálogo de Assets".

## D6 — Avisos legais ✅ e registro 🔑

### Os textos

A Riot tem **duas** políticas que alcançam este site, e cada uma pede o seu aviso. Os dois
foram copiados das páginas oficiais em 10/09/2026 e aparecem no rodapé de toda página e em
destaque na página "Sobre".

| | Developer Portal — *General Policies* | *Legal Jibber Jabber* |
|---|---|---|
| Página | <https://developer.riotgames.com/policies/general> | <https://www.riotgames.com/en/legal> |
| Atualizada em | 29/05/2025 | agosto de 2018 |
| O que pede | aviso obrigatório, "readily visible to players" | aviso a incluir de forma visível ao compartilhar o projeto |
| Por que vale aqui | o site usa o Data Dragon, que a política lista entre as ferramentas do portal | o site usa arte da Riot e vai ser compartilhado com amigos |

O que o site publica, nessa ordem:

> Biblioteca de Assets isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

> Biblioteca de Assets was created under Riot Games' "Legal Jibber Jabber" policy using assets owned by Riot Games. Riot Games does not endorse or sponsor this project.

Ficam em inglês. Traduzir seria parafrasear; a página "Sobre" explica em português de onde
cada um vem e leva às duas políticas.

### A comparação

Feita em 10/09/2026 sobre o **HTML** das duas páginas, não sobre cópia de terceiros:

- **Palavra a palavra:** idênticos. A única diferença é o marcador de lugar de cada política —
  `[Your product]` e `[The title of your Project]` — trocado pelo nome.
- **Caractere a caractere:** apóstrofos e aspas são os retos (`'` e `"`), como estão nos bytes
  das duas páginas. Trocar pelos tipográficos dá um texto que parece igual e não é.
- **Espaço:** a página do Legal Jibber Jabber tem um `&nbsp;` depois de "Riot Games." — dois
  espaços na tela. O site usa um. É tipografia, não texto.

Existe uma terceira versão, e ela **não** é a usada: a documentação de League of Legends
(<https://developer.riotgames.com/docs/lol>, seção *Legal Notices*) repete o boilerplate sem
as contrações, sem a vírgula depois de "Riot Games" e sem o ponto final. O site segue a página
de **políticas**, que é a normativa e tem data; a documentação a resume. O sentido é o mesmo.

**O que segura:** `site-config.test.ts` guarda os dois textos oficiais literalmente, e falha se
o que vai para a tela diferir deles em qualquer coisa além do marcador. O registro da conferência
está em [`evidencias/politicas-da-riot-2026-09-10.md`](evidencias/politicas-da-riot-2026-09-10.md).

**Quando conferir de novo:** se a Riot atualizar qualquer uma das duas páginas. A data de
"atualizada em" da tabela acima é o que comparar.

### O registro do produto 🔑

A política geral exige que todo produto seja registrado — e auditado — pelo Developer Portal,
mesmo sem usar a API. É conta sua; ninguém faz por você.

1. Entre em <https://developer.riotgames.com> e clique em **Login**, com a sua conta Riot.
   O primeiro login cria a conta de desenvolvedor e uma chave de desenvolvimento de 24 h —
   **ignore a chave**, o site não usa a API.
2. Na página inicial do portal, clique em **Register Product**.
3. Escolha **produto pessoal** (*Personal*), não o de larga escala (*Production*). A
   documentação do portal reserva o pessoal para produtos do desenvolvedor e de uma comunidade
   pequena e privada — que é "eu e alguns amigos". O pessoal dispensa a etapa de verificação.
   Se um dia o site for divulgado, o caminho é registrar de novo como *Production*.
4. Preencha o formulário. A documentação pública diz que ele pede os detalhes principais do
   produto, e que o pessoal exige uma **descrição detalhada**. O que colar:

   | Campo | Valor |
   |---|---|
   | Nome | `Biblioteca de Assets` |
   | URL | a URL de produção da Vercel — ver D7 |
   | Jogo | League of Legends |
   | Descrição | o texto abaixo, em inglês — o portal é em inglês |

   ```text
   Biblioteca de Assets is a free, non-commercial web catalog of League of Legends visual
   assets (splash arts, loading screens, icons, items, runes, emotes, ward skins) for a small
   private group of friends who edit videos and thumbnails. It is a static site: it publishes
   only a JSON index that points to the original files on Data Dragon and CommunityDragon.
   No image is hosted or re-encoded by us; downloads go straight from the visitor's browser
   to those sources. It does not call the Riot Games API and uses no API key. No ads, no
   paywall, no donations, no accounts, no player data. Every page shows the legal boilerplate
   from the General Policies and the Legal Jibber Jabber notice.
   Source code: https://github.com/NihonCodingg/lol-assets
   ```

5. Leia os termos antes de aceitar — aceitar é você que faz.
6. Envie. A resposta chega nas **mensagens** do próprio portal.
7. Tire um print da página do produto com o status e mande no PR ou numa issue: é o critério 3
   do T-33.

## D7 — Endereço ✅

**No ar desde 11/09/2026**, no domínio de produção `biblioteca-de-assets.vercel.app` — o
endereço limpo, sem sufixo.

**Sem domínio próprio.** Decidido em 10/09/2026: o site fica no endereço que a Vercel dá,
aberto por URL, sem senha e sem divulgação. Domínio próprio continua possível depois, e não
muda nada no código.

**A regra do nome vale para o subdomínio.** O Legal Jibber Jabber (§5) proíbe registrar
domínio que use marca, nome comercial ou nome de personagem da Riot. O nome do projeto na
Vercel **vira** o subdomínio — e o padrão que ela sugere é o nome do repositório, `lol-assets`,
que carrega "LoL". Crie o projeto como **`biblioteca-de-assets`**: o endereço fica
`biblioteca-de-assets.vercel.app`, livre em 10/09/2026. Se estiver ocupado, a Vercel acrescenta
um sufixo — qualquer um serve, desde que sem "lol", "league", "riot" ou nome de campeão.

## D2 — Consentimento da Weird Gloop ⏳

O [ADR 0004](adr/0004-consentimento-da-wiki-e-teto-de-resolucao.md) é a trava: **nenhum
acesso automatizado à wiki sem consentimento**, imposto por código
(`WikiAccessBlockedError`) e coberto por teste.

- **Se o consentimento chegou:** ligar `NEXT_PUBLIC_WIKI_CONSENT_GRANTED=true` e
  `WIKI_CONSENT_GRANTED=true`, e registrar a evidência em `docs/SPIKES.md` com data. O
  crédito à wiki aparece sozinho na página "Sobre" — o código já está lá, desligado.
- **Se não chegou:** nada a fazer. O teto de resolução continua sendo o que as duas fontes
  atuais dão, e a página "Sobre" não cita a Weird Gloop.

> Escrever o adaptador da wiki **não** faz parte deste checklist, nem mesmo com
> consentimento. É ticket próprio, com spike antes.

## Antes de apertar o botão

| | Como conferir |
|---|---|
| Avisos legais visíveis em toda página | Automático: teste do T-27 e do T-33, e o axe do T-28 passa nas quatro telas |
| Avisos literais | Automático: `site-config.test.ts` trava os dois textos oficiais |
| Sem monetização | [ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md). Não há anúncio, afiliado nem paywall no código |
| Tier gratuito respeitado | O índice são ~19 MB de JSON estático; não há função serverless no caminho do usuário |
| `status.json` saudável | `curl https://<endereço>/indice/status.json` — `ok: true` e `gameVersion` no patch corrente |
| Índice fresco | O aviso do T-31 aparece sozinho se passar de 72 h |
| Nenhum marcador solto | Automático: teste que varre `[A DECIDIR]` e `[A CONFIRMAR]` — a lista de pendentes chegou a zero |

## O que o teste não consegue conferir

Três coisas, e todas são 🔑:

1. **Se a Riot mudou as políticas.** O teste compara o site com a cópia de 10/09/2026; só uma
   pessoa relendo as duas páginas descobre que a cópia envelheceu.
2. **Se o produto está registrado.** Não há API pública para verificar.
3. **Se o endereço resolve.** Não há endereço até alguém criar o projeto na Vercel.
