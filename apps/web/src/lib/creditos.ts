/**
 * Crédito por fonte e as duas licenças que convivem aqui (RF-22, RNF-10).
 *
 * O site não hospeda imagem nenhuma ([ADR 0012]) — o que ele publica é um índice
 * apontando para as fontes. Ainda assim o crédito é obrigatório: a obrigação vem
 * da política da Riot e dos termos de cada fonte, não de onde os bytes moram.
 *
 * ## Duas licenças, e a confusão que elas causam
 *
 * A **arte é da Riot** em todas as fontes. O que muda por fonte é o texto e a
 * curadoria em volta dela: o da wiki é CC BY-SA 3.0, o das outras não é
 * licenciado separadamente. Misturar as duas seria dizer que a splash é CC
 * BY-SA, o que é falso e é o risco anotado no §"Riscos" do KICKOFF.
 *
 * ## Fonte nova não entra sem crédito
 *
 * A tabela é indexada por `AssetSource` do contrato. Um teste percorre **todos**
 * os valores do tipo e exige entrada para cada um: fonte nova sem crédito
 * quebra o build antes de chegar na tela.
 */
import type { AssetSource } from "@lol-assets/schema";

export interface Credito {
  readonly fonte: AssetSource;
  readonly nome: string;
  readonly url: string;
  /** O que esta fonte traz que as outras não trazem. */
  readonly papel: string;
  /** A licença do que **não** é arte da Riot. `undefined` quando não há. */
  readonly licencaDoTexto?: string;
  /**
   * Fonte que só pode ser creditada quando o acesso for autorizado.
   *
   * Creditar antes seria pior que não creditar: diria que usamos conteúdo de
   * quem pediu, nos termos, para não ser usado automatizadamente ([ADR 0004]).
   */
  readonly exigeConsentimento?: boolean;
}

export const CREDITOS: Readonly<Record<AssetSource, Credito>> = {
  ddragon: {
    fonte: "ddragon",
    nome: "Data Dragon",
    url: "https://developer.riotgames.com/docs/lol#data-dragon",
    papel: "CDN oficial da Riot. É de onde vem a maior parte da arte de campeão, item e runa.",
  },
  cdragon: {
    fonte: "cdragon",
    nome: "Community Dragon",
    url: "https://communitydragon.org/",
    papel:
      "Projeto comunitário mantido por voluntários. É a única fonte de chromas, " +
      "loading vintage, emotes e ward skins.",
  },
  riot_static: {
    fonte: "riot_static",
    nome: "Riot static",
    url: "https://static.developer.riotgames.com/",
    papel: "Arquivos estáticos publicados pela Riot fora do Data Dragon.",
  },
  wiki: {
    fonte: "wiki",
    nome: "League of Legends Wiki (Weird Gloop)",
    url: "https://wiki.leagueoflegends.com/",
    papel: "Artes em alta definição e curadoria de nomes.",
    licencaDoTexto: "CC BY-SA 3.0 (o texto; as imagens continuam sendo da Riot)",
    exigeConsentimento: true,
  },
};

/**
 * Os créditos que aparecem na tela.
 *
 * `consentimentoDaWiki` vem de variável de ambiente e é `false` até o
 * consentimento existir — a mesma trava que o `WikiAccessBlockedError` impõe no
 * indexador, do lado de cá.
 */
export function creditosVisiveis(consentimentoDaWiki: boolean): Credito[] {
  return Object.values(CREDITOS).filter(
    (credito) => !credito.exigeConsentimento || consentimentoDaWiki,
  );
}
