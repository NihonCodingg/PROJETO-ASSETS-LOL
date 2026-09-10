/**
 * Configuração estática do site.
 *
 * [A DECIDIR] `displayName` é o nome público do produto e ainda não foi escolhido.
 * Ele não pode conter "Riot", "League of Legends" nem "LoL" (KICKOFF §B.5.1).
 * Até a decisão fica um rótulo descritivo neutro. Este é o **único** lugar onde o
 * nome exibido existe — repositório e pacotes internos ficam como estão.
 * Ver docs/adr/0003-nome-publico-do-produto.md.
 *
 * [A CONFIRMAR] o texto exato do aviso legal precisa ser copiado da Developer API
 * Policy antes do lançamento: https://developer.riotgames.com/docs/lol
 * O aviso é obrigatório e visível para os jogadores (KICKOFF §A.5 e §B.5.1), assim
 * como o registro do produto no Developer Portal.
 */

const displayName = "Catálogo de Assets";

/** Aviso legal exigido pela Riot, derivado do nome exibido. */
function riotLegalNotice(productName: string): string {
  return (
    `${productName} isn't endorsed by Riot Games and doesn't reflect the views or ` +
    "opinions of Riot Games or anyone officially involved in producing or managing " +
    "Riot Games properties. Riot Games, and all associated properties are trademarks " +
    "or registered trademarks of Riot Games, Inc."
  );
}

/**
 * O consentimento da Weird Gloop, do lado do navegador.
 *
 * Espelha o `WIKI_CONSENT_GRANTED` do indexador, que é o que de fato bloqueia a
 * rede ([ADR 0004]). Aqui ele decide só uma coisa: se o crédito à wiki aparece
 * na página "Sobre". Creditar antes da autorização seria afirmar que usamos
 * conteúdo de quem pediu, nos termos, para não ser usado automatizadamente.
 *
 * `NEXT_PUBLIC_` porque é lido no cliente, e literal em vez de indexado porque o
 * Next substitui essas variáveis no build por correspondência textual exata.
 */
const wikiConsentGranted = process.env.NEXT_PUBLIC_WIKI_CONSENT_GRANTED === "true";

export const siteConfig = {
  displayName,
  wikiConsentGranted,
  description:
    "Assets visuais de League of Legends na melhor fonte disponível, prontos para baixar.",
  repositoryUrl: "https://github.com/NihonCodingg/lol-assets",
  riotLegalNotice: riotLegalNotice(displayName),
} as const;
