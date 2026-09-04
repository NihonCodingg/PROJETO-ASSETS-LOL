/**
 * Resolução de URL, download e conversão para PNG — o coração do ADR 0001.
 *
 * O CDN entrega os bytes de origem; o PNG é gerado **no navegador**, no clique.
 * Nada aqui re-encoda no servidor, e nada aqui converte antes de o usuário pedir.
 *
 * As primitivas do navegador entram por injeção para o módulo ser testável fora
 * dele. O caminho real com canvas de verdade é coberto pelo e2e (T-29).
 */
import type { Asset } from "@lol-assets/schema";

export interface Bitmap {
  readonly width: number;
  readonly height: number;
  close: () => void;
}

export interface CanvasLike {
  width: number;
  height: number;
  getContext: (id: "2d") => { drawImage: (image: Bitmap, x: number, y: number) => void } | null;
  toBlob: (callback: (blob: Blob | null) => void, type?: string) => void;
}

export interface PngDeps {
  toBitmap: (blob: Blob) => Promise<Bitmap>;
  makeCanvas: (width: number, height: number) => CanvasLike;
}

/**
 * A URL pública do asset.
 *
 * Sem `storageKey` o asset não foi copiado para o bucket — é o caso das versões
 * anteriores (ADR 0007). Aí vale a URL da fonte, e o download funciona igual.
 */
export function assetUrl(asset: Asset, assetsBaseUrl?: string): string {
  if (asset.storageKey && assetsBaseUrl) {
    return `${assetsBaseUrl.replace(/\/+$/, "")}/${asset.storageKey}`;
  }
  return asset.sourceUrl;
}

/** Só faz sentido converter o que ainda não é PNG (ADR 0001 regra 4). */
export function canConvertToPng(asset: Asset): boolean {
  return asset.format !== "png";
}

/** `Jax_000_splash_centered.jpg` → `Jax_000_splash_centered.png`. */
export function pngFileName(fileName: string): string {
  return fileName.replace(/\.[^.]+$/, "") + ".png";
}

export function formatBytes(total: number): string {
  if (total < 1024) return `${total} B`;
  if (total < 1024 * 1024) return `${Math.round(total / 1024)} KB`;
  return `${(total / 1024 / 1024).toFixed(1)} MB`;
}

/** A ficha que o RF-09 exige aparecer **antes** de qualquer download. */
export function assetSummary(asset: Asset): string {
  return `${asset.width}×${asset.height} · ${asset.format} · ${formatBytes(asset.bytes)} · ${asset.source}`;
}

function defaultDeps(): PngDeps {
  return {
    toBitmap: (blob) => createImageBitmap(blob),
    makeCanvas: (width, height) => {
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      return canvas as unknown as CanvasLike;
    },
  };
}

/**
 * Converte para PNG no cliente, no clique.
 *
 * O bitmap vem de um `Blob` obtido por `fetch`, não de um `<img>` de outra
 * origem — é por isso que o canvas não é contaminado, como medido nos spikes.
 */
export async function convertToPng(blob: Blob, deps: PngDeps = defaultDeps()): Promise<Blob> {
  const bitmap = await deps.toBitmap(blob);
  try {
    const canvas = deps.makeCanvas(bitmap.width, bitmap.height);
    const contexto = canvas.getContext("2d");
    if (!contexto) throw new Error("canvas sem contexto 2d");
    contexto.drawImage(bitmap, 0, 0);
    return await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((resultado) => {
        if (resultado) resolve(resultado);
        else reject(new Error("o canvas não devolveu um PNG"));
      }, "image/png");
    });
  } finally {
    bitmap.close();
  }
}

/** Hash dos bytes recebidos, para conferir contra o `sha256` do índice. */
export async function sha256Hex(blob: Blob): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", await blob.arrayBuffer());
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

/** Entrega o arquivo ao usuário. Fora do navegador, é no-op testável. */
export function saveBlob(blob: Blob, fileName: string): void {
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(href), 2000);
}
