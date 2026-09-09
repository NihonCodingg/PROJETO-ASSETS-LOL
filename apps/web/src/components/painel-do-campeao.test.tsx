import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Asset, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

import { PainelDoCampeao } from "./painel-do-campeao";

/**
 * T-19 e T-20 no nível do componente.
 *
 * O que pode quebrar em silêncio aqui: chroma aparecendo na lista de skins
 * (RF-06), e trocar de skin sem trocar os assets — os dois passam por qualquer
 * teste de renderização ingênuo.
 */

afterEach(cleanup);

function asset(tipo: string, extra: Partial<Asset> = {}): Asset {
  return {
    id: `${tipo}:${extra.skinId ?? 24}`,
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
  // `fileName` com o número da skin, como a convenção do §6.2 da Spec manda —
  // é ele que o painel usa como rótulo do cartão.
  asset("splash_centered", {
    skinId: 24000,
    skinNum: 0,
    id: "splash_centered:24000",
    fileName: "Jax_000_splash_centered.jpg",
  }),
  asset("splash_centered", {
    skinId: 24007,
    skinNum: 7,
    id: "splash_centered:24007",
    fileName: "Jax_007_splash_centered.jpg",
  }),
  asset("chroma", {
    skinId: 24009,
    skinNum: 9,
    parentSkinNum: 7,
    id: "chroma:24009",
    fileName: "Jax_009_chroma.png",
  }),
  asset("chroma", { skinId: 24010, skinNum: 10, parentSkinNum: 7, id: "chroma:24010" }),
];

const SKINS: CatalogSkin[] = [
  { skinId: 24000, skinNum: 0, championKey: 24, names: { pt_BR: "Jax" }, isBase: true },
  {
    skinId: 24007,
    skinNum: 7,
    championKey: 24,
    names: { pt_BR: "Nemesis Jax" },
    isBase: false,
    chromaCount: 2,
  },
  { skinId: 99003, skinNum: 3, championKey: 99, names: { pt_BR: "Lux" }, isBase: false },
];

const JAX: CatalogChampion = {
  championKey: 24,
  championId: "Jax",
  names: { pt_BR: "Jax" },
  skinCount: 2,
  baseSkinId: 24000,
};

function abrir(props: Partial<Parameters<typeof PainelDoCampeao>[0]> = {}) {
  const onClose = vi.fn();
  render(
    <PainelDoCampeao
      champion={JAX}
      skins={SKINS}
      assets={ASSETS}
      onClose={onClose}
      {...props}
    />,
  );
  return { onClose };
}

function seletor(): HTMLSelectElement {
  return screen.getByLabelText("Selecionar skin") as HTMLSelectElement;
}

function tiposVisiveis(): string[] {
  const painel = screen.getAllByRole("article");
  return painel.map((c) => c.dataset.tipo ?? "");
}

// --- o seletor de skin (T-19) --------------------------------------------------------

describe("seletor de skin", () => {
  it("lista as skins do campeão, com a base primeiro", () => {
    abrir();
    const opcoes = within(seletor()).getAllByRole("option");
    expect(opcoes.map((o) => o.textContent)).toEqual(["Jax", "Nemesis Jax"]);
  });

  it("não lista skin de outro campeão", () => {
    abrir();
    expect(within(seletor()).queryByText("Lux")).toBeNull();
  });

  it("abre na skin base quando ninguém pediu outra", () => {
    abrir();
    expect(seletor().value).toBe("0");
  });

  it("abre na skin que a busca pediu", () => {
    abrir({ skinInicial: 7 });
    expect(seletor().value).toBe("7");
    expect(screen.getByRole("heading", { name: "Nemesis Jax" })).toBeTruthy();
  });

  it("trocar de skin troca os assets exibidos", () => {
    abrir();
    const idsNaBase = screen.getAllByRole("article").map((c) => c.getAttribute("aria-label"));

    fireEvent.change(seletor(), { target: { value: "7" } });
    const idsNaOutra = screen.getAllByRole("article").map((c) => c.getAttribute("aria-label"));

    expect(seletor().value).toBe("7");
    expect(idsNaOutra).not.toEqual(idsNaBase);
  });

  it("o asset do campeão sobrevive à troca de skin", () => {
    abrir();
    expect(tiposVisiveis()).toContain("square");
    fireEvent.change(seletor(), { target: { value: "7" } });
    expect(tiposVisiveis()).toContain("square");
  });
});

// --- chroma atrás de toggle (T-20 / RF-06) ---------------------------------------------

describe("chromas", () => {
  it("não aparecem sem alguém pedir", () => {
    abrir({ skinInicial: 7 });
    expect(tiposVisiveis()).not.toContain("chroma");
  });

  it("o controle revela exatamente os da skin selecionada", () => {
    abrir({ skinInicial: 7 });
    fireEvent.click(screen.getByRole("button", { name: /Mostrar 2 chromas/ }));

    const chromas = screen.getAllByRole("article").filter((c) => c.dataset.tipo === "chroma");
    expect(chromas).toHaveLength(2);
  });

  it("a contagem revelada bate com o chromaCount do catálogo", () => {
    abrir({ skinInicial: 7 });
    const doCatalogo = SKINS.find((s) => s.skinNum === 7)?.chromaCount;
    expect(screen.getByRole("button", { name: new RegExp(`Mostrar ${doCatalogo} chromas`) })).toBeTruthy();
  });

  it("skin sem chroma não mostra o controle", () => {
    abrir({ skinInicial: 0 });
    expect(screen.queryByRole("button", { name: /chroma/ })).toBeNull();
  });

  it("o chroma revelado baixa com o fileName do índice", () => {
    abrir({ skinInicial: 7 });
    fireEvent.click(screen.getByRole("button", { name: /Mostrar 2 chromas/ }));
    expect(screen.getByLabelText("Jax_009_chroma.png")).toBeTruthy();
  });

  it("trocar de skin fecha os chromas da anterior", () => {
    abrir({ skinInicial: 7 });
    fireEvent.click(screen.getByRole("button", { name: /Mostrar 2 chromas/ }));
    expect(screen.getAllByRole("article").some((c) => c.dataset.tipo === "chroma")).toBe(true);

    fireEvent.change(seletor(), { target: { value: "0" } });
    expect(screen.queryByRole("button", { name: /chroma/ })).toBeNull();
  });
});

// --- estados ------------------------------------------------------------------------------

describe("estados do painel", () => {
  it("sem a fatia carregada, avisa em vez de mostrar vazio", () => {
    abrir({ assets: null });
    expect(screen.getByText("carregando os assets…")).toBeTruthy();
  });

  it("com erro, mostra o erro e não finge que carregou", () => {
    abrir({ assets: null, erro: "HTTP 500" });
    expect(screen.getByRole("alert").textContent).toContain("HTTP 500");
    expect(screen.queryByText("carregando os assets…")).toBeNull();
  });

  it("o seletor existe mesmo antes de a fatia chegar", () => {
    abrir({ assets: null });
    expect(seletor()).toBeTruthy();
  });
});
