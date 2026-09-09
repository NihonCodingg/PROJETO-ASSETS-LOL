import { describe, expect, it } from "vitest";

import type { Asset, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

import {
  baseSkin,
  championAssets,
  chromasOf,
  panelAssets,
  skinAssets,
  skinsOf,
} from "./champion-panel";

/**
 * O que o painel mostra, e o que ele **não** mostra.
 *
 * Chroma é o caso perigoso: são 7.037 no catálogo real, e um deles vazando para
 * a lista de skins ou para a grade quebraria o RF-06 sem erro nenhum.
 */

function asset(tipo: string, extra: Partial<Asset> = {}): Asset {
  return {
    id: `${tipo}:${extra.skinId ?? extra.championKey ?? 24}`,
    type: tipo as Asset["type"],
    category: "champion",
    championKey: 24,
    championId: "Jax",
    names: { pt_BR: "Jax" },
    source: "ddragon",
    sourceUrl: `https://exemplo.invalido/${tipo}.png`,
    fileName: `Jax_${tipo}.png`,
    width: 128,
    height: 128,
    format: "png",
    hasAlpha: false,
    bytes: 1000,
    sha256: "0".repeat(64),
    ...extra,
  } as Asset;
}

const ASSETS: Asset[] = [
  asset("square"),
  asset("passive_icon"),
  asset("ability_icon"),
  asset("splash_centered", { skinId: 24000, skinNum: 0, isBaseSkin: true }),
  asset("tile", { skinId: 24000, skinNum: 0, isBaseSkin: true }),
  asset("splash_centered", { skinId: 24007, skinNum: 7, id: "splash_centered:24007" }),
  asset("tile", { skinId: 24007, skinNum: 7, id: "tile:24007" }),
  asset("chroma", { skinId: 24009, skinNum: 9, parentSkinNum: 7, id: "chroma:24009" }),
  asset("chroma", { skinId: 24010, skinNum: 10, parentSkinNum: 7, id: "chroma:24010" }),
  asset("chroma", { skinId: 24043, skinNum: 43, parentSkinNum: 42, id: "chroma:24043" }),
];

function skin(num: number, nome: string, base = false): CatalogSkin {
  return {
    skinId: 24000 + num,
    skinNum: num,
    championKey: 24,
    names: { pt_BR: nome },
    isBase: base,
  };
}

const SKINS: CatalogSkin[] = [
  skin(7, "Nemesis Jax"),
  skin(0, "Jax", true),
  skin(42, "Prestige Magma Chamber Jax"),
  { ...skin(3, "Lux"), championKey: 99 },
];

const JAX: CatalogChampion = {
  championKey: 24,
  championId: "Jax",
  names: { pt_BR: "Jax" },
  skinCount: 3,
  baseSkinId: 24000,
};

// --- o que é do campeão e o que é da skin ------------------------------------------

describe("assets do campeão", () => {
  it("são os que valem para qualquer skin", () => {
    expect(championAssets(ASSETS).map((a) => a.type).sort()).toEqual([
      "ability_icon",
      "passive_icon",
      "square",
    ]);
  });

  it("nenhum deles tem skinNum", () => {
    expect(championAssets(ASSETS).every((a) => a.skinNum === undefined)).toBe(true);
  });
});

describe("assets de uma skin", () => {
  it("traz só os da skin pedida", () => {
    expect(skinAssets(ASSETS, 7).map((a) => a.id).sort()).toEqual([
      "splash_centered:24007",
      "tile:24007",
    ]);
  });

  it("não traz chroma, mesmo o da skin pedida", () => {
    expect(skinAssets(ASSETS, 7).some((a) => a.type === "chroma")).toBe(false);
  });

  it("skin sem asset devolve lista vazia", () => {
    expect(skinAssets(ASSETS, 99)).toEqual([]);
  });
});

describe("o painel junta os dois", () => {
  it("assets da skin mais os do campeão", () => {
    const nomes = panelAssets(ASSETS, 0).map((a) => a.type);
    expect(nomes).toContain("splash_centered");
    expect(nomes).toContain("square");
    expect(nomes).not.toContain("chroma");
  });

  it("trocar de skin troca só a parte da skin", () => {
    const naBase = panelAssets(ASSETS, 0);
    const naOutra = panelAssets(ASSETS, 7);
    const doCampeao = championAssets(ASSETS).map((a) => a.id);

    for (const id of doCampeao) {
      expect(naBase.map((a) => a.id)).toContain(id);
      expect(naOutra.map((a) => a.id)).toContain(id);
    }
    expect(naBase.map((a) => a.id)).not.toEqual(naOutra.map((a) => a.id));
  });
});

// --- chroma (RF-06) -------------------------------------------------------------------

describe("chromas", () => {
  it("saem por parentSkinNum, não por skinNum", () => {
    expect(chromasOf(ASSETS, 7).map((a) => a.id)).toEqual(["chroma:24009", "chroma:24010"]);
  });

  it("skin sem chroma devolve lista vazia", () => {
    expect(chromasOf(ASSETS, 0)).toEqual([]);
  });

  it("o chroma de outra skin não vaza", () => {
    expect(chromasOf(ASSETS, 42).map((a) => a.id)).toEqual(["chroma:24043"]);
  });

  it("nunca aparecem no painel sem alguém pedir", () => {
    for (const num of [0, 7, 42]) {
      expect(panelAssets(ASSETS, num).some((a) => a.type === "chroma")).toBe(false);
    }
  });
});

// --- as skins de um campeão -------------------------------------------------------------

describe("lista de skins do painel", () => {
  it("traz só as do campeão, com a base primeiro", () => {
    expect(skinsOf(SKINS, JAX).map((s) => s.skinNum)).toEqual([0, 7, 42]);
  });

  it("não traz skin de outro campeão", () => {
    expect(skinsOf(SKINS, JAX).every((s) => s.championKey === 24)).toBe(true);
  });

  it("a base é a marcada como base", () => {
    expect(baseSkin(SKINS, JAX)?.skinNum).toBe(0);
  });

  it("sem base marcada, cai na primeira", () => {
    const semBase = SKINS.map((s) => ({ ...s, isBase: false }));
    expect(baseSkin(semBase, JAX)?.skinNum).toBe(0);
  });

  it("campeão sem skin nenhuma não quebra", () => {
    expect(baseSkin([], JAX)).toBeUndefined();
  });
});
