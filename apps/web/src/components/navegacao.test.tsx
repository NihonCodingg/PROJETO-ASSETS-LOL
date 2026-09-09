import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Asset, Catalog, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

import { GradeDeCampeoes } from "./grade-de-campeoes";
import { PainelDoCampeao } from "./painel-do-campeao";
import { PaletaDeBusca } from "./paleta-de-busca";

/**
 * Os quatro caminhos do [ADR 0010], contados em cliques, e a escala em que a
 * navegação tem que aguentar: 173 campeões na grade e 2.118 skins na busca.
 *
 * O orçamento de 3 cliques fecha **exatamente** no ADR. Não é folga: qualquer
 * passo a mais estoura, e estourar é o tipo de coisa que só se percebe usando.
 */

afterEach(cleanup);

// --- um catálogo do tamanho do real ---------------------------------------------------

const CAMPEOES: CatalogChampion[] = Array.from({ length: 173 }, (_, i) => ({
  championKey: i + 1,
  championId: `Campeao${i + 1}`,
  names: { pt_BR: `Campeão ${i + 1}` },
  skinCount: 12,
  baseSkinId: (i + 1) * 1000,
}));

const SKINS: CatalogSkin[] = Array.from({ length: 2118 }, (_, i) => {
  const championKey = (i % 173) + 1;
  const skinNum = Math.floor(i / 173);
  return {
    skinId: championKey * 1000 + skinNum,
    skinNum,
    championKey,
    names: { pt_BR: skinNum === 0 ? `Campeão ${championKey}` : `Skin Prestígio ${i}` },
    isBase: skinNum === 0,
  };
});

const CATALOGO: Catalog = {
  schemaVersion: "1.1.0",
  gameVersion: "16.18.1",
  generatedAt: "2026-09-09T00:00:00Z",
  champions: CAMPEOES,
  skins: SKINS,
};

// --- a grade (critério 1) ---------------------------------------------------------------

describe("grade de campeões", () => {
  it("tem exatamente um cartão por campeão", () => {
    render(<GradeDeCampeoes champions={CAMPEOES} onAbrir={vi.fn()} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(173);
  });

  it("cada cartão conta skins", () => {
    render(<GradeDeCampeoes champions={CAMPEOES} onAbrir={vi.fn()} />);
    expect(screen.getAllByText("12 skins")).toHaveLength(173);
  });

  it("nenhuma skin solta aparece na grade — foi o erro que o ADR 0010 corrigiu", () => {
    render(<GradeDeCampeoes champions={CAMPEOES} onAbrir={vi.fn()} />);
    expect(screen.queryByText(/Skin Prestígio/)).toBeNull();
  });

  it("clicar num cartão abre aquele campeão", () => {
    const onAbrir = vi.fn();
    render(<GradeDeCampeoes champions={CAMPEOES} onAbrir={onAbrir} />);
    fireEvent.click(screen.getByRole("button", { name: /Campeão 42/ }));

    expect(onAbrir).toHaveBeenCalledTimes(1);
    expect(onAbrir.mock.calls[0][0].championKey).toBe(42);
  });
});

// --- a virtualização (critério 7) ---------------------------------------------------------

describe("resultados de busca de skin", () => {
  function buscar(consulta: string) {
    render(<PaletaDeBusca catalog={CATALOGO} onChampion={vi.fn()} onSkin={vi.fn()} />);
    const campo = screen.getByRole("combobox");
    fireEvent.change(campo, { target: { value: consulta } });
    return document.querySelector("[data-resultados]") as HTMLElement;
  }

  it("acha todas as skins que casam", () => {
    const scroller = buscar("prestigio");
    expect(Number(scroller.dataset.resultados)).toBeGreaterThan(1000);
  });

  it("com milhares de resultados, o DOM fica na casa das dezenas", () => {
    const scroller = buscar("prestigio");
    const nos = document.querySelectorAll("[cmdk-item]").length;

    expect(Number(scroller.dataset.resultados)).toBeGreaterThan(1000);
    expect(nos).toBeLessThan(100);
    expect(scroller.dataset.virtual).toBe("true");
  });

  it("com poucos resultados, não paga o custo da virtualização", () => {
    const scroller = buscar("Campeão 42");
    expect(scroller.dataset.virtual).toBe("false");
  });
});

// --- os quatro caminhos do ADR 0010 (critério 6) --------------------------------------------

function asset(tipo: string, extra: Partial<Asset> = {}): Asset {
  return {
    id: `${tipo}:${extra.skinId ?? 24}`,
    type: tipo as Asset["type"],
    category: "champion",
    championKey: 24,
    championId: "Jax",
    names: { pt_BR: "Jax" },
    source: "ddragon",
    sourceUrl: "https://exemplo.invalido/x.png",
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

const JAX: CatalogChampion = {
  championKey: 24,
  championId: "Jax",
  names: { pt_BR: "Jax" },
  skinCount: 2,
  baseSkinId: 24000,
};

const SKINS_DO_JAX: CatalogSkin[] = [
  { skinId: 24000, skinNum: 0, championKey: 24, names: { pt_BR: "Jax" }, isBase: true },
  {
    skinId: 24004,
    skinNum: 4,
    championKey: 24,
    names: { pt_BR: "Jax Deus da Guerra" },
    isBase: false,
  },
];

const ASSETS_DO_JAX: Asset[] = [
  asset("square", { id: "square:24" }),
  asset("splash_centered", {
    skinId: 24000,
    skinNum: 0,
    id: "splash_centered:24000",
    fileName: "Jax_000_splash_centered.jpg",
  }),
  asset("splash_centered", {
    skinId: 24004,
    skinNum: 4,
    id: "splash_centered:24004",
    fileName: "Jax_004_splash_centered.jpg",
  }),
];

const CATALOGO_DO_JAX: Catalog = { ...CATALOGO, champions: [JAX], skins: SKINS_DO_JAX };

/** Conta cliques de verdade: cada `fireEvent.click` passa por aqui. */
function contador() {
  let cliques = 0;
  return {
    clicar(elemento: Element) {
      cliques += 1;
      fireEvent.click(elemento);
    },
    get total() {
      return cliques;
    },
  };
}

describe("orçamento de 3 cliques", () => {
  it('buscar "deus da guerra" → skin → baixar = 2', () => {
    const cliques = contador();
    const onSkin = vi.fn();
    render(<PaletaDeBusca catalog={CATALOGO_DO_JAX} onChampion={vi.fn()} onSkin={onSkin} />);

    // Digitar não é clique.
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "deus da guerra" } });
    cliques.clicar(document.querySelector("[cmdk-item]")!);
    expect(onSkin).toHaveBeenCalledTimes(1);
    expect(onSkin.mock.calls[0][0].skinNum).toBe(4);

    // O painel abre JÁ na skin certa — é o atalho que o ADR 0010 comprou.
    cleanup();
    render(
      <PainelDoCampeao
        champion={JAX}
        skins={SKINS_DO_JAX}
        assets={ASSETS_DO_JAX}
        skinInicial={4}
        onClose={vi.fn()}
      />,
    );
    const cartao = screen.getByLabelText("Jax_004_splash_centered.jpg");
    cliques.clicar(within(cartao).getByRole("button", { name: "Baixar original" }));

    expect(cliques.total).toBe(2);
  });

  it('buscar "jax" → campeão → baixar o square = 2', () => {
    const cliques = contador();
    const onChampion = vi.fn();
    render(<PaletaDeBusca catalog={CATALOGO_DO_JAX} onChampion={onChampion} onSkin={vi.fn()} />);

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "jax" } });
    cliques.clicar(document.querySelector("[cmdk-item]")!);
    expect(onChampion).toHaveBeenCalledTimes(1);

    cleanup();
    render(
      <PainelDoCampeao
        champion={JAX}
        skins={SKINS_DO_JAX}
        assets={ASSETS_DO_JAX}
        onClose={vi.fn()}
      />,
    );
    const cartao = screen.getByLabelText("Jax_square.png");
    cliques.clicar(within(cartao).getByRole("button", { name: "Baixar original" }));

    expect(cliques.total).toBe(2);
  });

  it('buscar "jax" → campeão → escolher a skin → baixar = 3', () => {
    const cliques = contador();
    render(<PaletaDeBusca catalog={CATALOGO_DO_JAX} onChampion={vi.fn()} onSkin={vi.fn()} />);

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "jax" } });
    cliques.clicar(document.querySelector("[cmdk-item]")!);

    cleanup();
    render(
      <PainelDoCampeao
        champion={JAX}
        skins={SKINS_DO_JAX}
        assets={ASSETS_DO_JAX}
        onClose={vi.fn()}
      />,
    );
    // Escolher a skin conta como um clique.
    cliques.clicar(screen.getByLabelText("Selecionar skin"));
    fireEvent.change(screen.getByLabelText("Selecionar skin"), { target: { value: "4" } });

    const cartao = screen.getByLabelText("Jax_004_splash_centered.jpg");
    cliques.clicar(within(cartao).getByRole("button", { name: "Baixar original" }));

    expect(cliques.total).toBe(3);
  });

  it("navegar sem digitar → campeão → escolher a skin → baixar = 3", () => {
    const cliques = contador();
    const onAbrir = vi.fn();
    render(<GradeDeCampeoes champions={[JAX]} onAbrir={onAbrir} />);

    cliques.clicar(screen.getByRole("button", { name: /Jax/ }));
    expect(onAbrir).toHaveBeenCalledTimes(1);

    cleanup();
    render(
      <PainelDoCampeao
        champion={JAX}
        skins={SKINS_DO_JAX}
        assets={ASSETS_DO_JAX}
        onClose={vi.fn()}
      />,
    );
    cliques.clicar(screen.getByLabelText("Selecionar skin"));
    fireEvent.change(screen.getByLabelText("Selecionar skin"), { target: { value: "4" } });

    const cartao = screen.getByLabelText("Jax_004_splash_centered.jpg");
    cliques.clicar(within(cartao).getByRole("button", { name: "Baixar original" }));

    expect(cliques.total).toBe(3);
  });
});
