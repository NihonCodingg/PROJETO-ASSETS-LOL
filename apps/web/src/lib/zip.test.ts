import JSZip from "jszip";
import { describe, expect, it, vi } from "vitest";

import type { Asset } from "@lol-assets/schema";

import { CONCORRENCIA, montarZip, relatorioDeFalhas, ZipCanceladoError } from "./zip";

/**
 * O zip do RF-17, montado de verdade e **relido de verdade**.
 *
 * Não adianta afirmar que o zip tem N arquivos: o teste gera com o JSZip real e
 * abre com o JSZip real, comparando a lista de nomes e os bytes. Foi assim que
 * o [ADR 0012] provou que o caminho existe, e é assim que ele continua provado.
 */

function asset(id: string, extra: Partial<Asset> = {}): Asset {
  return {
    id,
    type: "item_icon",
    category: "item",
    names: { pt_BR: id },
    source: "ddragon",
    sourceUrl: `https://ddragon.leagueoflegends.com/cdn/img/${id}.png`,
    fileName: `${id}.png`,
    width: 64,
    height: 64,
    format: "png",
    hasAlpha: true,
    bytes: 1000,
    sha256: "0".repeat(64),
    ...extra,
  } as Asset;
}

/** Bytes previsíveis por arquivo, para dar para conferir o conteúdo de volta. */
function conteudoDe(url: string): string {
  return `bytes de ${url}`;
}

function servidor(falhar: readonly string[] = []) {
  const pedidas: string[] = [];
  const buscar = vi.fn(async (url: string) => {
    pedidas.push(url);
    if (falhar.some((parte) => url.includes(parte))) throw new Error("HTTP 404");
    return new Blob([conteudoDe(url)], { type: "image/png" });
  });
  return { buscar, pedidas };
}

async function reler(blob: Blob): Promise<JSZip> {
  return JSZip.loadAsync(await blob.arrayBuffer());
}

// --- critério 1: N selecionados, N arquivos, com os nomes certos ----------------------

describe("montar o zip", () => {
  it("N assets viram N arquivos, com os fileName do índice", async () => {
    const assets = [asset("Item_3031"), asset("Item_1001"), asset("Rune_8005")];
    const { buscar } = servidor();

    const resultado = await montarZip(assets, undefined, { buscar });
    const lido = await reler(resultado.blob);

    expect(resultado.arquivos).toBe(3);
    expect(Object.keys(lido.files).sort()).toEqual([
      "Item_1001.png",
      "Item_3031.png",
      "Rune_8005.png",
    ]);
  });

  it("os bytes chegam inteiros do outro lado", async () => {
    const alvo = asset("Item_3031");
    const { buscar } = servidor();

    const lido = await reler((await montarZip([alvo], undefined, { buscar })).blob);

    expect(await lido.file("Item_3031.png")?.async("string")).toBe(
      conteudoDe(alvo.sourceUrl),
    );
  });

  it("nome repetido não sobrescreve em silêncio", async () => {
    const assets = [
      asset("a", { fileName: "Jax_000.jpg" }),
      asset("b", { fileName: "Jax_000.jpg" }),
      asset("c", { fileName: "Jax_000.jpg" }),
    ];
    const { buscar } = servidor();

    const lido = await reler((await montarZip(assets, undefined, { buscar })).blob);

    expect(Object.keys(lido.files).sort()).toEqual([
      "Jax_000 (2).jpg",
      "Jax_000 (3).jpg",
      "Jax_000.jpg",
    ]);
  });

  it("seleção vazia gera um zip vazio, não um erro", async () => {
    const { buscar } = servidor();
    const resultado = await montarZip([], undefined, { buscar });
    expect(resultado.arquivos).toBe(0);
    expect(buscar).not.toHaveBeenCalled();
  });

  it("guarda sem comprimir: JPEG e PNG já vêm comprimidos", async () => {
    const gerar = vi.fn(async () => new Blob(["zip"]));
    await montarZip([asset("a")], undefined, {
      buscar: servidor().buscar,
      novoZip: () => ({ file: vi.fn(), generateAsync: gerar }),
    });
    expect(gerar).toHaveBeenCalledWith({ type: "blob", compression: "STORE" });
  });
});

// --- critério 2: nenhum servidor próprio ------------------------------------------------

describe("nenhuma requisição a servidor próprio", () => {
  it("só as URLs das fontes são tocadas", async () => {
    const assets = [
      asset("ddragon", { sourceUrl: "https://ddragon.leagueoflegends.com/cdn/img/a.png" }),
      asset("cdragon", {
        source: "cdragon",
        sourceUrl: "https://raw.communitydragon.org/latest/plugins/b.png",
      }),
    ];
    const { buscar, pedidas } = servidor();

    await montarZip(assets, undefined, { buscar });

    expect(pedidas).toEqual([
      "https://ddragon.leagueoflegends.com/cdn/img/a.png",
      "https://raw.communitydragon.org/latest/plugins/b.png",
    ]);
    for (const url of pedidas) {
      expect(new URL(url).host).toMatch(/leagueoflegends\.com$|communitydragon\.org$/);
    }
  });

  it("com storageKey e bucket, usa o bucket — e nunca uma rota /api", async () => {
    const assets = [asset("a", { storageKey: "16.18.1/item/a.png" })];
    const { buscar, pedidas } = servidor();

    await montarZip(assets, "https://bucket.exemplo.invalido", { buscar });

    expect(pedidas).toEqual(["https://bucket.exemplo.invalido/16.18.1/item/a.png"]);
    expect(pedidas.some((url) => url.includes("/api"))).toBe(false);
  });
});

// --- falha de um arquivo ------------------------------------------------------------------

describe("um arquivo que não vem", () => {
  it("não derruba o lote: o resto entra", async () => {
    const assets = [asset("a"), asset("morto"), asset("c")];
    const { buscar } = servidor(["morto"]);

    const resultado = await montarZip(assets, undefined, { buscar });
    const lido = await reler(resultado.blob);

    expect(resultado.arquivos).toBe(2);
    expect(resultado.falhas).toHaveLength(1);
    expect(resultado.falhas[0].fileName).toBe("morto.png");
    expect(lido.file("a.png")).not.toBeNull();
    expect(lido.file("morto.png")).toBeNull();
  });

  it("o que faltou vai escrito dentro do zip", async () => {
    const { buscar } = servidor(["morto"]);
    const lido = await reler(
      (await montarZip([asset("a"), asset("morto")], undefined, { buscar })).blob,
    );

    const relatorio = await lido.file("FALHAS.txt")?.async("string");
    expect(relatorio).toContain("morto.png");
    expect(relatorio).toContain("HTTP 404");
  });

  it("sem falha nenhuma, não existe FALHAS.txt", async () => {
    const { buscar } = servidor();
    const lido = await reler((await montarZip([asset("a")], undefined, { buscar })).blob);
    expect(lido.file("FALHAS.txt")).toBeNull();
  });

  it("o relatório nomeia cada arquivo, o motivo e a URL", () => {
    const texto = relatorioDeFalhas([
      { fileName: "a.png", url: "https://exemplo.invalido/a.png", motivo: "HTTP 404" },
    ]);
    expect(texto).toContain("1 arquivo não veio");
    expect(texto).toContain("a.png");
    expect(texto).toContain("HTTP 404");
    expect(texto).toContain("https://exemplo.invalido/a.png");
  });
});

// --- progresso e cancelamento --------------------------------------------------------------

describe("progresso", () => {
  it("avisa a cada arquivo, até o total", async () => {
    const assets = Array.from({ length: 10 }, (_, i) => asset(`a${i}`));
    const { buscar } = servidor();
    const passos: number[] = [];

    await montarZip(assets, undefined, {
      buscar,
      onProgresso: (p) => passos.push(p.feitos),
    });

    expect(passos).toHaveLength(10);
    expect(passos.at(-1)).toBe(10);
    expect([...passos].sort((a, b) => a - b)).toEqual(passos);
  });

  it("conta as falhas junto", async () => {
    const { buscar } = servidor(["morto"]);
    const vistos: number[] = [];
    await montarZip([asset("a"), asset("morto")], undefined, {
      buscar,
      onProgresso: (p) => vistos.push(p.falhas),
    });
    expect(vistos.at(-1)).toBe(1);
  });

  it("no máximo 4 buscas ao mesmo tempo (regra 4 do CLAUDE.md)", async () => {
    const assets = Array.from({ length: 20 }, (_, i) => asset(`a${i}`));
    let vivas = 0;
    let pico = 0;
    const buscar = async () => {
      vivas += 1;
      pico = Math.max(pico, vivas);
      await Promise.resolve();
      vivas -= 1;
      return new Blob(["x"]);
    };

    await montarZip(assets, undefined, { buscar });

    expect(pico).toBeLessThanOrEqual(CONCORRENCIA);
  });

  it("cancelar interrompe em vez de baixar os 5.042", async () => {
    const assets = Array.from({ length: 100 }, (_, i) => asset(`a${i}`));
    const controle = new AbortController();
    const { buscar, pedidas } = servidor();

    const promessa = montarZip(assets, undefined, {
      buscar,
      sinal: controle.signal,
      onProgresso: (p) => {
        if (p.feitos >= 8) controle.abort();
      },
    });

    await expect(promessa).rejects.toBeInstanceOf(ZipCanceladoError);
    expect(pedidas.length).toBeLessThan(assets.length);
  });
});
