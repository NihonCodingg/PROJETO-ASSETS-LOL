import { describe, expect, it } from "vitest";

import { examples } from "./examples";
import { SCHEMA_VERSION } from "./index";

describe("fixture do contrato", () => {
  it("o manifesto aponta para o catálogo e para as fatias", () => {
    const versao = examples.manifest.versions[0];
    expect(examples.manifest.currentVersion).toBe(versao.gameVersion);
    expect(versao.catalog.url).toBe("catalog.json");
    expect(versao.catalog.champions).toBe(examples.catalog.champions.length);
    expect(versao.catalog.skins).toBe(examples.catalog.skins.length);
    expect(versao.shards.map((s) => s.category).sort()).toEqual(["champion", "item", "rune"]);
  });

  it("todo documento declara a versão do contrato em uso", () => {
    expect(examples.catalog.schemaVersion).toBe(SCHEMA_VERSION);
    expect(examples.manifest.schemaVersion).toBe(SCHEMA_VERSION);
  });

  // ADR 0010: navegação por campeão, busca por skin. A fixture precisa exercitar
  // os dois níveis, senão o front não tem como testar o modelo híbrido.
  it("traz os dois níveis, com a skin ligada ao campeão", () => {
    expect(examples.catalog.champions.length).toBeGreaterThanOrEqual(3);
    expect(examples.catalog.skins.length).toBeGreaterThan(examples.catalog.champions.length);

    const chaves = new Set(examples.catalog.champions.map((c) => c.championKey));
    for (const skin of examples.catalog.skins) {
      expect(chaves.has(skin.championKey)).toBe(true);
    }
    for (const campeao of examples.catalog.champions) {
      const suas = examples.catalog.skins.filter((s) => s.championKey === campeao.championKey);
      expect(suas.length).toBe(campeao.skinCount);
      expect(suas.filter((s) => s.isBase)).toHaveLength(1);
    }
  });

  // ADR 0002: os nomes canônicos, nunca os das fontes.
  it("usa os nomes canônicos de corte de splash", () => {
    const tipos = new Set(examples.shards.champion.assets.map((a) => a.type));
    expect(tipos.has("splash_centered")).toBe(true);
    expect(tipos.has("splash_wide")).toBe(true);

    const centered = examples.shards.champion.assets.find((a) => a.type === "splash_centered");
    const wide = examples.shards.champion.assets.find((a) => a.type === "splash_wide");
    expect([centered?.width, centered?.height]).toEqual([1280, 720]);
    expect([wide?.width, wide?.height]).toEqual([1215, 717]);
  });

  // ADR 0001 regra 4: o que tem alfa é PNG, e o front usa isso para desabilitar
  // o botão de converter.
  it("marca alfa só onde ele existe de verdade", () => {
    const runa = examples.shards.rune.assets[0];
    const item = examples.shards.item.assets[0];
    expect(runa.hasAlpha).toBe(true);
    expect(runa.format).toBe("png");
    expect(item.hasAlpha).toBe(false);

    for (const asset of examples.shards.champion.assets) {
      if (asset.hasAlpha) expect(asset.format).toBe("png");
    }
  });

  it("nem toda skin do catálogo tem asset na fatia", () => {
    // De propósito: é o caso que o front precisa saber tratar.
    const comAsset = new Set(
      examples.shards.champion.assets.map((a) => a.skinId).filter(Boolean),
    );
    expect(comAsset.size).toBeLessThan(examples.catalog.skins.length);
  });
});
