import { describe, expect, it } from "vitest";

import { championAliases } from "@lol-assets/schema/aliases";
import type { Catalog, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

import { buildSearchIndex, hitId, normalize, rotulo, search, type SearchHit } from "./search";

/**
 * O catálogo dos testes é sintético de propósito: a fixture do contrato tem três
 * campeões, e o que precisa ser provado aqui são apóstrofos, apelidos, termos
 * transversais e escala. Os nomes e as grafias são os reais.
 */

function campeao(
  championKey: number,
  championId: string,
  pt: string,
  skinCount = 1,
): CatalogChampion {
  return {
    championKey,
    championId,
    names: { pt_BR: pt, en_US: pt },
    skinCount,
    baseSkinId: championKey * 1000,
  };
}

function skin(championKey: number, skinNum: number, pt: string): CatalogSkin {
  return {
    skinId: championKey * 1000 + skinNum,
    skinNum,
    championKey,
    names: { pt_BR: pt, en_US: pt },
    isBase: skinNum === 0,
  };
}

const CAMPEOES: CatalogChampion[] = [
  campeao(24, "Jax", "Jax", 18),
  campeao(145, "Kaisa", "Kai'Sa", 16),
  campeao(350, "Belveth", "Bel'Veth", 5),
  campeao(31, "Chogath", "Cho'Gath", 12),
  campeao(21, "MissFortune", "Miss Fortune", 24),
  campeao(4, "TwistedFate", "Twisted Fate", 15),
  campeao(59, "JarvanIV", "Jarvan IV", 16),
  campeao(136, "AurelionSol", "Aurelion Sol", 7),
  campeao(103, "Ahri", "Ahri", 22),
  campeao(84, "Akali", "Akali", 22),
  campeao(28, "Evelynn", "Evelynn", 17),
  campeao(99, "Lux", "Lux", 23),
];

const SKINS: CatalogSkin[] = [
  skin(24, 0, "Jax"),
  skin(24, 4, "Jax Deus da Guerra"),
  skin(24, 11, "O Super Jax"),
  skin(145, 0, "Kai'Sa"),
  skin(145, 7, "K/DA ALL OUT Kai'Sa"),
  skin(103, 0, "Ahri"),
  skin(103, 13, "K/DA Ahri"),
  skin(103, 30, "K/DA ALL OUT Ahri Prestígio"),
  skin(84, 0, "Akali"),
  skin(84, 15, "K/DA Akali"),
  skin(84, 41, "K/DA Akali Prestígio"),
  skin(28, 0, "Evelynn"),
  skin(28, 10, "K/DA Evelynn"),
  skin(99, 0, "Lux"),
  skin(99, 25, "Lux Bruxa Estelar Prestígio"),
];

const CATALOGO: Catalog = {
  schemaVersion: "1.1.0",
  gameVersion: "16.17.1",
  generatedAt: "2026-09-08T00:00:00Z",
  champions: CAMPEOES,
  skins: SKINS,
};

const indice = buildSearchIndex(CATALOGO);

function primeiro(consulta: string): SearchHit | undefined {
  return search(indice, consulta)[0];
}

function rotuloDoPrimeiro(consulta: string): string | undefined {
  const hit = primeiro(consulta);
  return hit && rotulo(hit);
}

// --- normalização ------------------------------------------------------------------

describe("normalização", () => {
  it.each([
    ["Kai'Sa", "kaisa"],
    ["Bel'Veth", "belveth"],
    ["Cho'Gath", "chogath"],
    ["KAI'SA", "kaisa"],
    ["Prestígio", "prestigio"],
    ["K/DA ALL OUT Ahri", "kdaalloutahri"],
    ["Jarvan IV", "jarvaniv"],
    ["  Lux  ", "lux"],
    ["Nunu e Willump", "nunuewillump"],
  ])("%s vira %s", (entrada, esperado) => {
    expect(normalize(entrada)).toBe(esperado);
  });

  it("é a mesma normalização das chaves do arquivo de apelidos", () => {
    // Se divergirem, apelido nenhum resolve — e o sintoma seria só "não acha".
    for (const chave of Object.keys(championAliases)) {
      expect(normalize(chave)).toBe(chave);
    }
  });
});

// --- acerto em primeiro lugar --------------------------------------------------------

describe("acerta em primeiro lugar", () => {
  it.each([
    ["kaisa", "Kai'Sa"],
    ["Kai'Sa", "Kai'Sa"],
    ["KAI'SA", "Kai'Sa"],
    ["belveth", "Bel'Veth"],
    ["bel'veth", "Bel'Veth"],
    ["chogath", "Cho'Gath"],
    ["cho gath", "Cho'Gath"],
    ["jax", "Jax"],
    ["JAX", "Jax"],
    ["lux", "Lux"],
    ["ahri", "Ahri"],
    ["jarvan iv", "Jarvan IV"],
    ["jarvaniv", "Jarvan IV"],
    ["miss fortune", "Miss Fortune"],
    ["aurelion sol", "Aurelion Sol"],
    ["evelynn", "Evelynn"],
    ["twisted fate", "Twisted Fate"],
  ])("%s → %s", (consulta, esperado) => {
    expect(rotuloDoPrimeiro(consulta)).toBe(esperado);
  });
});

describe("apelidos mantidos à mão (ADR 0009)", () => {
  it.each([
    ["mf", "Miss Fortune"],
    ["tf", "Twisted Fate"],
    ["j4", "Jarvan IV"],
    ["asol", "Aurelion Sol"],
    ["eve", "Evelynn"],
  ])("%s → %s", (consulta, esperado) => {
    expect(rotuloDoPrimeiro(consulta)).toBe(esperado);
  });

  it("acrescentar uma linha ao JSON passa a valer sem tocar em código", () => {
    const comNovo = buildSearchIndex(CATALOGO, { ...championAliases, jaxinho: "Jax" });
    expect(rotulo(search(comNovo, "jaxinho")[0])).toBe("Jax");
    // E sem a linha, não resolve — é o que prova que veio do arquivo.
    expect(search(indice, "jaxinho")).toHaveLength(0);
  });

  it("o apelido ganha de um casamento por prefixo", () => {
    // "eve" também é prefixo de "Evelynn"; o apelido é intenção declarada.
    const hit = search(indice, "eve")[0];
    expect(hit.kind).toBe("champion");
    expect(rotulo(hit)).toBe("Evelynn");
  });
});

// --- os dois níveis do ADR 0010 -------------------------------------------------------

describe("campeão casado vira uma entrada, não dezoito (RF-05)", () => {
  it("jax devolve uma entrada de campeão", () => {
    const resultados = search(indice, "jax");
    expect(resultados).toHaveLength(1);
    expect(resultados[0].kind).toBe("champion");
  });

  it("as skins do campeão que casou não aparecem, mesmo casando por substring", () => {
    // "O Super Jax" e "Jax Deus da Guerra" contêm "jax".
    expect(search(indice, "jax").some((h) => h.kind === "skin")).toBe(false);
  });

  it("lux não traz as skins de Lux", () => {
    expect(search(indice, "lux").map(hitId)).toEqual(["champion:99"]);
  });
});

describe("termo transversal devolve skins de campeões diferentes (RF-24)", () => {
  it("kda", () => {
    const resultados = search(indice, "kda");
    const donos = new Set(
      resultados.filter((h) => h.kind === "skin").map((h) => h.skin.championKey),
    );
    expect(donos.size).toBeGreaterThanOrEqual(3);
    expect(resultados.every((h) => h.kind === "skin")).toBe(true);
  });

  it("prestigio", () => {
    const resultados = search(indice, "prestigio");
    const donos = new Set(
      resultados.filter((h) => h.kind === "skin").map((h) => h.skin.championKey),
    );
    expect(donos.size).toBeGreaterThanOrEqual(3);
  });

  it("cada skin vem rotulada com o campeão de origem", () => {
    for (const hit of search(indice, "kda")) {
      if (hit.kind !== "skin") continue;
      expect(hit.championName).toBeTruthy();
      expect(hit.championId).toBeTruthy();
    }
  });

  it("acento no termo não muda o resultado", () => {
    expect(search(indice, "prestígio").map(hitId)).toEqual(search(indice, "prestigio").map(hitId));
  });
});

// --- ranqueamento ---------------------------------------------------------------------

describe("ranqueamento", () => {
  it("exato de campeão ganha de prefixo de campeão", () => {
    // "Ahri" é exato; nenhuma outra entrada de campeão começa com "ahri".
    expect(rotuloDoPrimeiro("ahri")).toBe("Ahri");
  });

  it("empate favorece campeão, que é o nível de navegação", () => {
    const resultados = search(indice, "a");
    const primeiroSkin = resultados.findIndex((h) => h.kind === "skin");
    const ultimoCampeao = resultados.map((h) => h.kind).lastIndexOf("champion");
    if (primeiroSkin >= 0) expect(ultimoCampeao).toBeLessThan(primeiroSkin);
  });

  it("consulta vazia não devolve nada", () => {
    expect(search(indice, "")).toHaveLength(0);
    expect(search(indice, "   ")).toHaveLength(0);
  });

  it("consulta sem casamento nenhum devolve lista vazia", () => {
    expect(search(indice, "zzzzzzzz")).toHaveLength(0);
  });
});

// --- escala (RNF-01) --------------------------------------------------------------------

describe("escala real: 173 campeões e 2.118 skins", () => {
  const grande: Catalog = {
    ...CATALOGO,
    champions: Array.from({ length: 173 }, (_, i) => campeao(i + 1, `Campeao${i}`, `Campeão ${i}`, 12)),
    skins: Array.from({ length: 2118 }, (_, i) =>
      skin((i % 173) + 1, i, i % 7 === 0 ? `K/DA Skin ${i}` : `Skin ${i}`),
    ),
  };

  it("o índice cobre os dois níveis", () => {
    expect(buildSearchIndex(grande).size).toBe(173 + 2118);
  });

  it("responde em menos de 50 ms", () => {
    const indiceGrande = buildSearchIndex(grande);
    const consultas = ["kda", "campeao1", "skin 42", "zzz", "a", "prestigio"];

    const inicio = performance.now();
    for (const consulta of consultas) search(indiceGrande, consulta);
    const decorrido = (performance.now() - inicio) / consultas.length;

    expect(decorrido).toBeLessThan(50);
  });
});
