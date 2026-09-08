import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { examples } from "@lol-assets/schema/examples";
import type { Asset } from "@lol-assets/schema";

import { orderAssets } from "@/lib/asset-panel";

import { PainelDeAsset } from "./painel-de-asset";

/**
 * O painel é onde o RF-09 vive: a ficha aparece **antes** de qualquer clique.
 * E é onde o critério 4 vive: um asset que falha marca o cartão dele e mais
 * nada — são dezenas na tela, e derrubar o painel esconderia os que funcionam.
 */

afterEach(cleanup);

const DO_JAX = examples.shards.champion.assets;
const BASE = "https://assets.exemplo.invalido/lol";

function abrir(assets: readonly Asset[] = DO_JAX, extra: Partial<Parameters<typeof PainelDeAsset>[0]> = {}) {
  const onClose = vi.fn();
  const baixar = vi.fn().mockResolvedValue(undefined);
  const copiar = vi.fn().mockResolvedValue(undefined);
  render(
    <PainelDeAsset
      titulo="Jax"
      assets={assets}
      assetsBaseUrl={BASE}
      onClose={onClose}
      baixar={baixar}
      copiar={copiar}
      {...extra}
    />,
  );
  return { onClose, baixar, copiar };
}

function cartoes(): HTMLElement[] {
  return screen.getAllByRole("article");
}

// --- o que aparece, e em que ordem ------------------------------------------------

describe("todos os tipos do índice, nenhum inventado", () => {
  it("um cartão por asset do índice", () => {
    abrir();
    expect(cartoes()).toHaveLength(DO_JAX.length);
  });

  it("splash_centered é o primeiro (ADR 0002)", () => {
    abrir();
    expect(cartoes()[0].dataset.tipo).toBe("splash_centered");
  });

  it("tipo ausente no índice não renderiza cartão", () => {
    // A fixture não tem `chroma`: ele é do T-20 e ainda não existe no índice.
    abrir();
    expect(cartoes().some((c) => c.dataset.tipo === "chroma")).toBe(false);
    expect(screen.queryByText("chroma")).toBeNull();
  });

  it("com um asset só, ele é o único cartão", () => {
    const square = DO_JAX.find((a) => a.type === "square")!;
    abrir([square]);
    expect(cartoes()).toHaveLength(1);
    expect(screen.getByText("1 asset")).toBeTruthy();
  });
});

// --- a ficha antes do clique (RF-09) ------------------------------------------------

describe("ficha honesta antes de qualquer download", () => {
  it("mostra formato, resolução, bytes e fonte", () => {
    abrir();
    const primeiro = cartoes()[0];
    const asset = DO_JAX.find((a) => a.type === "splash_centered")!;

    const ficha = within(primeiro).getByText(/·/);
    expect(ficha.textContent).toContain(`${asset.width}`);
    expect(ficha.textContent).toContain(asset.format);
    expect(ficha.textContent).toContain(asset.source);
  });

  it("um asset que já é PNG não oferece conversão", () => {
    const square = DO_JAX.find((a) => a.format === "png")!;
    abrir([square]);
    expect(screen.getByRole("button", { name: "já é PNG" }).hasAttribute("disabled")).toBe(true);
  });
});

// --- baixar ---------------------------------------------------------------------------

describe("as duas formas de baixar (ADR 0001)", () => {
  it("original chama o download sem conversão", async () => {
    const { baixar } = abrir([DO_JAX[0]]);
    fireEvent.click(screen.getByRole("button", { name: "Baixar original" }));

    await waitFor(() => expect(baixar).toHaveBeenCalledTimes(1));
    expect(baixar.mock.calls[0][1]).toBe(false);
  });

  it("PNG chama o download pedindo conversão", async () => {
    const jpeg = DO_JAX.find((a) => a.format === "jpeg")!;
    const { baixar } = abrir([jpeg]);
    fireEvent.click(screen.getByRole("button", { name: "Baixar PNG" }));

    await waitFor(() => expect(baixar).toHaveBeenCalledTimes(1));
    expect(baixar.mock.calls[0][1]).toBe(true);
  });
});

// --- copiar URL -------------------------------------------------------------------------

describe("copiar URL", () => {
  it("copia a URL pública do asset", async () => {
    const square = DO_JAX.find((a) => a.type === "square")!;
    const { copiar } = abrir([square]);
    fireEvent.click(screen.getByRole("button", { name: "Copiar URL" }));

    await waitFor(() => expect(copiar).toHaveBeenCalledTimes(1));
    const copiado = copiar.mock.calls[0][0] as string;
    expect(copiado.startsWith("http")).toBe(true);
    // Com storageKey e base pública, a URL é a do bucket; sem, é a da fonte.
    expect(copiado).toBe(square.storageKey ? `${BASE}/${square.storageKey}` : square.sourceUrl);
  });
});

// --- o erro fica no cartão (critério 4) ----------------------------------------------------

describe("um asset que falha não derruba os outros", () => {
  it("só o cartão que falhou mostra o erro", async () => {
    // O painel reordena: o cartão clicado é o primeiro DEPOIS da ordenação.
    const falhando = orderAssets(DO_JAX)[0];
    const baixar = vi.fn(async (asset: Asset) => {
      if (asset.id === falhando.id) throw new Error("rede fora");
    });
    abrir(DO_JAX, { baixar });

    const primeiro = cartoes()[0];
    fireEvent.click(within(primeiro).getByRole("button", { name: "Baixar original" }));

    await waitFor(() => expect(within(primeiro).getByRole("alert")).toBeTruthy());
    expect(primeiro.dataset.estado).toBe("erro");
    // Os outros continuam de pé e sem erro nenhum.
    expect(cartoes()).toHaveLength(DO_JAX.length);
    expect(screen.getAllByRole("alert")).toHaveLength(1);
  });

  it("o cartão que deu certo volta para pronto", async () => {
    abrir([DO_JAX[0]]);
    fireEvent.click(screen.getByRole("button", { name: "Baixar original" }));

    await waitFor(() => expect(cartoes()[0].dataset.estado).toBe("pronto"));
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("os botões ficam desabilitados enquanto baixa", async () => {
    let liberar = () => {};
    const baixar = vi.fn(() => new Promise<void>((resolve) => (liberar = resolve)));
    abrir([DO_JAX[0]], { baixar });

    const botao = screen.getByRole("button", { name: "Baixar original" });
    fireEvent.click(botao);

    await waitFor(() => expect(botao.hasAttribute("disabled")).toBe(true));
    liberar();
    await waitFor(() => expect(botao.hasAttribute("disabled")).toBe(false));
  });
});

// --- fechar ----------------------------------------------------------------------------------

describe("fechar", () => {
  it("Esc fecha", () => {
    const { onClose } = abrir();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("outra tecla não fecha", () => {
    const { onClose } = abrir();
    fireEvent.keyDown(window, { key: "a" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("o botão fechar fecha", () => {
    const { onClose } = abrir();
    fireEvent.click(screen.getByRole("button", { name: "fechar" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("depois de fechado, o Esc não chama mais nada", () => {
    const { onClose } = abrir();
    cleanup();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).not.toHaveBeenCalled();
  });
});
