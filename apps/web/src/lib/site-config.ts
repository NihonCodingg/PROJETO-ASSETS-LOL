/**
 * Configuração estática do site.
 *
 * O aviso legal da Riot é obrigatório e precisa ficar visível para os jogadores
 * (KICKOFF §A.5 e §B.5.1), assim como o registro do produto no Developer Portal
 * antes do lançamento público.
 *
 * [A CONFIRMAR] o texto exato precisa ser copiado da Developer API Policy antes
 * de ir ao ar: https://developer.riotgames.com/docs/lol
 * [A DECIDIR] o nome público do produto não pode conter "Riot" nem
 * "League of Legends" (§B.5.1); "lol-assets" é um nome de trabalho.
 */
export const siteConfig = {
  name: "lol-assets",
  description:
    "Catálogo público de assets visuais de League of Legends em PNG, na melhor qualidade disponível.",
  repositoryUrl: "https://github.com/NihonCodingg/PROJETO-ASSETS-LOL",
  riotLegalNotice:
    "lol-assets isn't endorsed by Riot Games and doesn't reflect the views or opinions of " +
    "Riot Games or anyone officially involved in producing or managing Riot Games properties. " +
    "Riot Games, and all associated properties are trademarks or registered trademarks of " +
    "Riot Games, Inc.",
} as const;
