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

export const siteConfig = {
  displayName,
  description:
    "Assets visuais de League of Legends na melhor fonte disponível, prontos para baixar.",
  repositoryUrl: "https://github.com/NihonCodingg/PROJETO-ASSETS-LOL",
  riotLegalNotice: riotLegalNotice(displayName),
} as const;
