import { describe, expect, it } from "vitest";

import { siteConfig } from "./site-config";

describe("siteConfig", () => {
  it("expõe o aviso legal obrigatório da Riot", () => {
    expect(siteConfig.riotLegalNotice).toContain("Riot Games");
    expect(siteConfig.riotLegalNotice).toContain(siteConfig.displayName);
    expect(siteConfig.riotLegalNotice.length).toBeGreaterThan(100);
  });

  // ADR 0003: o nome público não pode conter "Riot", "League of Legends" nem "LoL".
  it("usa um nome exibido que respeita a política da Riot", () => {
    expect(siteConfig.displayName).not.toMatch(/riot|league of legends|lol/i);
  });
});
