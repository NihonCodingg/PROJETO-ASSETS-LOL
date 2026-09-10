# Checklist de lançamento

O que separa o site que roda na sua máquina do site no ar, aberto por URL para você e alguns
amigos.

> **Estado em 10/09/2026:** tudo que dá para fazer sem a sua conta está feito e coberto por
> teste. O que falta **depende de conta sua**, e está marcado com 🔑.

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

## D7 — Endereço 🔑

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
