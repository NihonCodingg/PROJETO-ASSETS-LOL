import { describe, expect, it } from "vitest";

import { siteConfig } from "./site-config";

describe("siteConfig", () => {
  it("expõe o aviso legal obrigatório da Riot", () => {
    expect(siteConfig.riotLegalNotice).toContain("Riot Games");
    expect(siteConfig.riotLegalNotice.length).toBeGreaterThan(100);
  });
});
