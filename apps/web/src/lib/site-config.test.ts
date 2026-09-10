import { describe, expect, it } from "vitest";

import { RIOT_JIBBER_JABBER_NOTICE, RIOT_PORTAL_BOILERPLATE, siteConfig } from "./site-config";

/**
 * Os textos oficiais, como estavam nas páginas da Riot em 10/09/2026.
 *
 * Estão **duplicados** aqui de propósito: este arquivo é uma trava literal. Quem
 * "melhorar" a redação de um aviso em `site-config.ts` quebra o teste, e para
 * consertá-lo precisa mexer no texto oficial também — que é a hora de reabrir a
 * política e conferir. Origem de cada um: `RIOT_POLICY_URLS`.
 */
const OFICIAL_DO_PORTAL =
  "[Your product] isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.";

const OFICIAL_DO_JIBBER_JABBER =
  '[The title of your Project] was created under Riot Games\' "Legal Jibber Jabber" policy using assets owned by Riot Games. Riot Games does not endorse or sponsor this project.';

describe("siteConfig", () => {
  // ADR 0003: o nome público não pode conter "Riot", "League of Legends" nem "LoL".
  it("usa um nome exibido que respeita a política da Riot", () => {
    expect(siteConfig.displayName).not.toMatch(/riot|league of legends|lol/i);
  });
});

describe("os avisos da Riot são cópia, não paráfrase (T-33, D6)", () => {
  it("o boilerplate do Developer Portal é o texto oficial", () => {
    expect(RIOT_PORTAL_BOILERPLATE).toBe(OFICIAL_DO_PORTAL);
  });

  it("o aviso do Legal Jibber Jabber é o texto oficial", () => {
    expect(RIOT_JIBBER_JABBER_NOTICE).toBe(OFICIAL_DO_JIBBER_JABBER);
  });

  it("o texto publicado só troca o marcador de lugar pelo nome", () => {
    expect(siteConfig.riotLegalNotice).toBe(
      OFICIAL_DO_PORTAL.replace("[Your product]", siteConfig.displayName),
    );
    expect(siteConfig.riotJibberJabberNotice).toBe(
      OFICIAL_DO_JIBBER_JABBER.replace("[The title of your Project]", siteConfig.displayName),
    );
  });

  it("nenhum marcador de lugar sobra no que vai para a tela", () => {
    for (const aviso of [siteConfig.riotLegalNotice, siteConfig.riotJibberJabberNotice]) {
      expect(aviso).not.toMatch(/\[[^\]]*\]/);
    }
  });

  it("aspas e apóstrofos são os retos das páginas, não os tipográficos", () => {
    // As duas páginas usam ' e " retos — conferido nos bytes do HTML. Um editor
    // que "corrige" para ’ ou “ ” produz um texto que parece igual e não é.
    for (const aviso of [siteConfig.riotLegalNotice, siteConfig.riotJibberJabberNotice]) {
      expect(aviso).not.toMatch(/[‘’“”]/);
    }
  });
});
