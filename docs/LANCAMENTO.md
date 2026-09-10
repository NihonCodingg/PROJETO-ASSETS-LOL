# Checklist de lançamento

O que separa o site de hoje — que roda em preview e é uso privado — do site público.

> **Estado em 10/09/2026:** tudo que dá para automatizar está feito e coberto por teste. O
> que falta **depende da sua conta e do seu dinheiro**, e está marcado com 🔑. Nenhum item
> 🔑 pode ser feito por mim, e nenhum deles é opcional.

## D1 — Nome público ✅

Decidido em 10/09/2026: **Biblioteca de Assets**
([ADR 0003](adr/0003-nome-publico-do-produto.md)).

Vive num lugar só, `apps/web/src/lib/site-config.ts`, e o aviso legal é derivado dele — se o
nome mudar, o aviso acompanha. Dois testes seguram:

- o nome não contém "Riot", "League of Legends" nem "LoL";
- o nome não é mais o rótulo provisório "Catálogo de Assets".

## D6 — Aviso legal e registro 🔑

### O texto do aviso

O que o site publica hoje, gerado a partir do nome:

> Biblioteca de Assets isn't endorsed by Riot Games and doesn't reflect the views or opinions
> of Riot Games or anyone officially involved in producing or managing Riot Games properties.
> Riot Games, and all associated properties are trademarks or registered trademarks of Riot
> Games, Inc.

**O que falta:** abrir a
[Developer API Policy](https://developer.riotgames.com/docs/lol) e a página
[Legal Jibber Jabber](https://www.riotgames.com/en/legal), copiar o texto oficial e comparar
**palavra a palavra** com o de cima. A comparação é manual de propósito: é o único item do
projeto cujo erro não é bug, é problema jurídico.

Se divergir, o ajuste é em `riotLegalNotice()` no `site-config.ts` — e o marcador
`[A CONFIRMAR]` no topo do arquivo sai junto.

### O registro do produto

🔑 Registrar **Biblioteca de Assets** no Developer Portal, com o nome final e a URL, antes
de tornar o site público. Print no PR que fechar este item.

## D7 — Domínio 🔑

Contratar o domínio e apontar para a Vercel. Depende do D1, que já fechou.

Enquanto não houver domínio, o site continua em preview — que é uso privado e não dispara
obrigação nenhuma da política.

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
| Aviso legal visível em toda página | Automático: teste do T-27, e o axe do T-28 passa nas quatro telas |
| Sem monetização | [ADR 0005](adr/0005-arquitetura-estatica-custo-zero.md). Não há anúncio, afiliado nem paywall no código |
| Tier gratuito respeitado | O índice são ~19 MB de JSON estático; não há função serverless no caminho do usuário |
| `status.json` saudável | `curl https://<domínio>/indice/status.json` — `ok: true` e `gameVersion` no patch corrente |
| Índice fresco | O aviso do T-31 aparece sozinho se passar de 72 h |
| Nenhum marcador solto | Automático: teste que varre `[A DECIDIR]` e `[A CONFIRMAR]` |

## O que o teste não consegue conferir

Três coisas, e todas são 🔑:

1. **Se o texto legal está literal.** O teste compara o nosso texto com ele mesmo; só uma
   pessoa comparando com a fonte oficial fecha o D6.
2. **Se o produto está registrado.** Não há API pública para verificar.
3. **Se o domínio resolve.** Não há domínio até alguém contratar um.
