import { describe, expect, it, vi } from "vitest";

import { examples } from "@lol-assets/schema/examples";

import { AssetsClient, AssetsFetchError, indexAgeHours } from "./assets-client";

const BASE = "https://assets.exemplo.invalido/lol";

function servidorDaFixture() {
  const manifesto = examples.manifest;
  const versao = manifesto.versions[0];
  const corpos: Record<string, unknown> = {
    "manifest.json": manifesto,
    [versao.catalog.url]: examples.catalog,
  };
  for (const shard of versao.shards) {
    corpos[shard.url] = examples.shards[shard.category as "champion" | "item" | "rune"];
  }

  const chamadas: string[] = [];
  const fetchImpl = vi.fn(async (url: string) => {
    chamadas.push(url);
    const caminho = url.replace(`${BASE}/`, "");
    const corpo = corpos[caminho];
    if (!corpo) return new Response("não encontrado", { status: 404 });
    return new Response(JSON.stringify(corpo), { status: 200 });
  });
  return { fetchImpl, chamadas };
}

describe("AssetsClient", () => {
  it("carrega manifesto e catálogo sem tocar a fatia de assets", async () => {
    const { fetchImpl, chamadas } = servidorDaFixture();
    const cliente = new AssetsClient(BASE, fetchImpl);

    const manifesto = await cliente.loadManifest();
    const catalogo = await cliente.loadCatalog(manifesto);

    expect(catalogo.champions.length).toBeGreaterThan(0);
    // ADR 0010: a home desenha a grade sem baixar registro de asset nenhum.
    expect(chamadas.some((url) => url.includes("index-"))).toBe(false);
    expect(chamadas).toHaveLength(2);
  });

  it("busca a fatia só quando pedida, e uma vez só", async () => {
    const { fetchImpl, chamadas } = servidorDaFixture();
    const cliente = new AssetsClient(BASE, fetchImpl);
    const manifesto = await cliente.loadManifest();

    const primeira = await cliente.loadShard(manifesto, "champion");
    const segunda = await cliente.loadShard(manifesto, "champion");

    expect(primeira).toBe(segunda);
    expect(chamadas.filter((url) => url.includes("index-champion"))).toHaveLength(1);
  });

  it("nenhuma requisição vai para o ddragon ou o cdragon", async () => {
    const { fetchImpl, chamadas } = servidorDaFixture();
    const cliente = new AssetsClient(BASE, fetchImpl);
    const manifesto = await cliente.loadManifest();
    await cliente.loadCatalog(manifesto);
    await cliente.loadShard(manifesto, "champion");

    for (const url of chamadas) {
      expect(url.startsWith(BASE)).toBe(true);
      expect(url).not.toContain("ddragon");
      expect(url).not.toContain("communitydragon");
    }
  });

  it("erro de rede vira erro com a URL e o status", async () => {
    const cliente = new AssetsClient(BASE, async () => new Response("x", { status: 503 }));
    await expect(cliente.loadManifest()).rejects.toBeInstanceOf(AssetsFetchError);
  });

  it("categoria ausente na versão atual falha explicando", async () => {
    const { fetchImpl } = servidorDaFixture();
    const cliente = new AssetsClient(BASE, fetchImpl);
    const manifesto = await cliente.loadManifest();
    await expect(cliente.loadShard(manifesto, "emote")).rejects.toThrow(/emote/);
  });
});

describe("idade do índice", () => {
  it("mede em horas desde generatedAt", () => {
    const manifesto = { ...examples.manifest, generatedAt: "2026-09-04T00:00:00Z" };
    const idade = indexAgeHours(manifesto, new Date("2026-09-07T00:00:00Z"));
    expect(idade).toBeCloseTo(72, 1);
  });
});
