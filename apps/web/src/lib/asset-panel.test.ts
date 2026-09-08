import { describe, expect, it } from "vitest";

import { examples } from "@lol-assets/schema/examples";
import type { Asset, AssetType } from "@lol-assets/schema";

import { TYPE_ORDER, availableTypes, orderAssets } from "./asset-panel";

const DO_JAX = examples.shards.champion.assets;

function asset(tipo: AssetType, skinNum?: number, id = `${tipo}:${skinNum ?? 0}`): Asset {
  const base = DO_JAX.find((a) => (skinNum === undefined ? a.skinNum === undefined : true))!;
  return { ...base, id, type: tipo, skinNum, skinId: skinNum === undefined ? undefined : 24000 + skinNum };
}

describe("ordem do painel", () => {
  it("splash_centered primeiro, por ser o maior corte (ADR 0002)", () => {
    expect(orderAssets(DO_JAX)[0].type).toBe("splash_centered");
  });

  it("a ordem não depende da ordem que veio do índice", () => {
    const invertido = [...DO_JAX].reverse();
    expect(orderAssets(invertido).map((a) => a.id)).toEqual(orderAssets(DO_JAX).map((a) => a.id));
  });

  it("dentro do tipo, a skin base vem primeiro", () => {
    const splashes = orderAssets(DO_JAX).filter((a) => a.type === "splash_centered");
    expect(splashes.length).toBeGreaterThan(1);
    expect(splashes.map((a) => a.skinNum)).toEqual([...splashes.map((a) => a.skinNum)].sort((x, y) => (x ?? 0) - (y ?? 0)));
  });

  it("não perde nem duplica asset", () => {
    const ordenados = orderAssets(DO_JAX);
    expect(ordenados).toHaveLength(DO_JAX.length);
    expect(new Set(ordenados.map((a) => a.id)).size).toBe(DO_JAX.length);
  });

  it("não altera a lista recebida", () => {
    const original = [...DO_JAX];
    orderAssets(DO_JAX);
    expect(DO_JAX).toEqual(original);
  });

  it("lista vazia continua vazia", () => {
    expect(orderAssets([])).toEqual([]);
  });

  it("tipo desconhecido vai para o fim, não some", () => {
    const estranho = { ...DO_JAX[0], id: "x:1", type: "tipo_novo" as AssetType, skinNum: undefined };
    const ordenados = orderAssets([estranho, ...DO_JAX]);
    expect(ordenados).toHaveLength(DO_JAX.length + 1);
    expect(ordenados[ordenados.length - 1].id).toBe("x:1");
  });
});

describe("tipos disponíveis", () => {
  it("são só os que existem no índice", () => {
    const tipos = availableTypes(DO_JAX);
    expect(new Set(tipos)).toEqual(new Set(DO_JAX.map((a) => a.type)));
  });

  it("vêm na ordem do painel", () => {
    const tipos = availableTypes(DO_JAX);
    const posicoes = tipos.map((t) => TYPE_ORDER.indexOf(t));
    expect(posicoes).toEqual([...posicoes].sort((a, b) => a - b));
  });

  it("nenhum tipo é inventado", () => {
    // A fixture não tem chroma nem emote: eles não podem aparecer do nada.
    expect(availableTypes(DO_JAX)).not.toContain("chroma");
    expect(availableTypes(DO_JAX)).not.toContain("emote_icon");
  });

  it("sem asset, não há tipo", () => {
    expect(availableTypes([])).toEqual([]);
  });
});

describe("a tabela de ordem", () => {
  it("não tem tipo repetido", () => {
    expect(new Set(TYPE_ORDER).size).toBe(TYPE_ORDER.length);
  });

  it("cobre todos os tipos que o índice real produz hoje", () => {
    for (const asset of DO_JAX) expect(TYPE_ORDER).toContain(asset.type);
  });
});

describe("ordenação sintética, sem depender da fixture", () => {
  it("respeita a tabela mesmo com tipos fora de ordem", () => {
    const bagunca = [
      asset("square"),
      asset("tile", 3),
      asset("splash_centered", 1),
      asset("ability_icon"),
      asset("splash_centered", 0),
    ];
    expect(orderAssets(bagunca).map((a) => a.id)).toEqual([
      "splash_centered:0",
      "splash_centered:1",
      "tile:3",
      "square:0",
      "ability_icon:0",
    ]);
  });
});
