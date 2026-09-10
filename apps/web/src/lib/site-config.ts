/**
 * Configuração estática do site.
 *
 * `displayName` é o nome público do produto, **decidido em 10/09/2026**:
 * *Biblioteca de Assets* ([ADR 0003](../../../../docs/adr/0003-nome-publico-do-produto.md)).
 * Ele não contém "Riot", "League of Legends" nem "LoL", como o KICKOFF §B.5.1
 * exige, e há teste garantindo que continue assim. Este é o **único** lugar onde
 * o nome exibido existe — repositório e pacotes internos ficam como estão.
 *
 * ## Os dois avisos da Riot
 *
 * São dois porque são duas políticas, e as duas alcançam este site:
 *
 * | Política | O que ela pede | Por que vale aqui |
 * |---|---|---|
 * | Developer Portal, *General Policies* | "readily visible to players" | o site usa o Data Dragon, que a política lista como ferramenta do portal |
 * | *Legal Jibber Jabber*, §6 | "conspicuously include" | o site usa arte da Riot e é compartilhado com outras pessoas |
 *
 * Os dois textos foram **copiados** das páginas oficiais em 10/09/2026 e ficam
 * guardados com o marcador de lugar que cada política usa. A única
 * transformação permitida é trocar o marcador pelo nome do produto; o teste
 * confere que todo o resto é idêntico, caractere a caractere. A comparação, com a
 * variante que a documentação de LoL traz, está em `docs/LANCAMENTO.md` (D6).
 */

const displayName = "Biblioteca de Assets";

/** As páginas de onde os dois avisos foram copiados. */
export const RIOT_POLICY_URLS = {
  portal: "https://developer.riotgames.com/policies/general",
  jibberJabber: "https://www.riotgames.com/en/legal",
} as const;

/**
 * Developer Portal → Policies → General → Core Policies (atualizada em
 * 29/05/2025): "You must post the following legal boilerplate to your product in
 * a location that is readily visible to players".
 */
export const RIOT_PORTAL_BOILERPLATE =
  "[Your product] isn't endorsed by Riot Games and doesn't reflect the views or " +
  "opinions of Riot Games or anyone officially involved in producing or managing " +
  "Riot Games properties. Riot Games, and all associated properties are trademarks " +
  "or registered trademarks of Riot Games, Inc.";

/**
 * Legal Jibber Jabber, §6 (atualizada em agosto de 2018): "If you share your
 * Project with others, please conspicuously include the following notice (e.g.,
 * on your Project's website)".
 */
export const RIOT_JIBBER_JABBER_NOTICE =
  "[The title of your Project] was created under Riot Games' \"Legal Jibber Jabber\" " +
  "policy using assets owned by Riot Games. Riot Games does not endorse or sponsor " +
  "this project.";

/** Troca o marcador de lugar da política pelo nome. Não mexe em mais nada. */
function fillPlaceholder(template: string, placeholder: string, productName: string): string {
  if (!template.includes(placeholder)) {
    throw new Error(`o texto oficial não traz o marcador ${placeholder}`);
  }
  return template.replace(placeholder, productName);
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
  /** O boilerplate do Developer Portal. Rodapé de toda página e página Sobre (RF-21). */
  riotLegalNotice: fillPlaceholder(RIOT_PORTAL_BOILERPLATE, "[Your product]", displayName),
  /** O aviso do Legal Jibber Jabber. Vai junto do outro, nos mesmos dois lugares. */
  riotJibberJabberNotice: fillPlaceholder(
    RIOT_JIBBER_JABBER_NOTICE,
    "[The title of your Project]",
    displayName,
  ),
} as const;
