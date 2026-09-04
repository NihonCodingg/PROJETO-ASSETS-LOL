import { describe, expect, it, vi } from "vitest";

import { examples } from "@lol-assets/schema/examples";
import type { Asset } from "@lol-assets/schema";

import {
  assetSummary,
  assetUrl,
  canConvertToPng,
  convertToPng,
  formatBytes,
  pngFileName,
  sha256Hex,
  type Bitmap,
  type CanvasLike,
  type PngDeps,
} from "./asset-file";

const BASE = "https://assets.exemplo.invalido/lol";
const assets = examples.shards.champion.assets;
const square = assets.find((a) => a.type === "square")!;
const splash = assets.find((a) => a.type === "splash_centered")!;

describe("URL do asset", () => {
  it("usa o storageKey quando o asset foi copiado para o bucket", () => {
    expect(assetUrl(square, BASE)).toBe(`${BASE}/${square.storageKey}`);
  });

  // ADR 0007: versões anteriores existem só no índice, sem storageKey.
  it("cai para o sourceUrl quando não há storageKey", () => {
    const semCopia: Asset = { ...square, storageKey: undefined };
    expect(assetUrl(semCopia, BASE)).toBe(square.sourceUrl);
  });

  it("cai para o sourceUrl quando não há base pública configurada", () => {
    expect(assetUrl(square, undefined)).toBe(square.sourceUrl);
  });
});

describe("conversão para PNG", () => {
  it("não é oferecida para asset que já é PNG", () => {
    expect(canConvertToPng(square)).toBe(false);
    expect(canConvertToPng(splash)).toBe(true);
  });

  it("troca só a extensão do nome", () => {
    expect(pngFileName("Jax_000_splash_centered.jpg")).toBe("Jax_000_splash_centered.png");
    expect(pngFileName("Jax_square.png")).toBe("Jax_square.png");
  });

  it("desenha o bitmap num canvas do tamanho da origem e devolve image/png", async () => {
    const desenhado: Bitmap[] = [];
    let tamanho: [number, number] | null = null;

    const deps: PngDeps = {
      toBitmap: async () => ({ width: 1280, height: 720, close: vi.fn() }),
      makeCanvas: (width, height) => {
        tamanho = [width, height];
        const canvas: CanvasLike = {
          width,
          height,
          getContext: () => ({ drawImage: (imagem) => desenhado.push(imagem) }),
          toBlob: (callback) => callback(new Blob([new Uint8Array([1, 2])], { type: "image/png" })),
        };
        return canvas;
      },
    };

    const png = await convertToPng(new Blob(["origem"]), deps);

    expect(tamanho).toEqual([1280, 720]);
    expect(desenhado).toHaveLength(1);
    expect(png.type).toBe("image/png");
  });

  it("fecha o bitmap mesmo quando a conversão falha", async () => {
    const close = vi.fn();
    const deps: PngDeps = {
      toBitmap: async () => ({ width: 10, height: 10, close }),
      makeCanvas: () => ({
        width: 10,
        height: 10,
        getContext: () => null,
        toBlob: (callback) => callback(null),
      }),
    };

    await expect(convertToPng(new Blob(["x"]), deps)).rejects.toThrow(/contexto/);
    expect(close).toHaveBeenCalledOnce();
  });
});

describe("integridade e ficha", () => {
  it("o sha256 dos bytes recebidos é comparável ao do índice", async () => {
    // Prova que o front consegue verificar RF-10 com o dado que o índice traz.
    const bytes = new TextEncoder().encode("conteúdo qualquer");
    const digest = await sha256Hex(new Blob([bytes]));
    expect(digest).toMatch(/^[0-9a-f]{64}$/);
    expect(digest).toBe(await sha256Hex(new Blob([bytes])));
    expect(digest).not.toBe(await sha256Hex(new Blob(["outro"])));
  });

  // RF-09: formato, resolução, tamanho e fonte, antes de qualquer clique.
  it("a ficha traz os quatro dados", () => {
    const ficha = assetSummary(splash);
    expect(ficha).toContain("1280×720");
    expect(ficha).toContain("jpeg");
    expect(ficha).toContain("ddragon");
    expect(ficha).toMatch(/\d+ (B|KB|MB)/);
  });

  it("formata bytes de forma legível", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(27107)).toBe("26 KB");
    expect(formatBytes(5 * 1024 * 1024)).toBe("5.0 MB");
  });
});
