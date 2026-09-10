import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import JSZip from "jszip";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Asset, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

import { LIMITE_DE_ARQUIVOS } from "@/lib/selecao";
import { montarZip } from "@/lib/zip";

import { BarraDeLote } from "./barra-de-lote";
import { PainelDeAsset } from "./painel-de-asset";
import { PainelDoCampeao } from "./painel-do-campeao";

/**
 * O lote do RF-17 e o "tudo do Jax" do RF-18, na tela.
 *
 * O caminho aqui é o real de ponta a ponta: `montarZip` de verdade, JSZip de
 * verdade, e o zip relido no fim. O único ponto trocado é o `fetch` — que é
 * exatamente o ponto onde o critério 2 quer olhar.
 */

afterEach(cleanup);

function asset(id: string, extra: Partial<Asset> = {}): Asset {
  return {
    id,
    type: "splash_centered",
    category: "champion",
    championKey: 24,
    championId: "Jax",
    names: { pt_BR: id },
    source: "ddragon",
    sourceUrl: `https://ddragon.leagueoflegends.com/cdn/img/${id}.jpg`,
    fileName: `${id}.jpg`,
    width: 1280,
    height: 720,
    format: "jpeg",
    hasAlpha: false,
    bytes: 120_000,
    sha256: "0".repeat(64),
    ...extra,
  } as Asset;
}

function servidor() {
  const pedidas: string[] = [];
  return {
    pedidas,
    buscar: async (url: string) => {
      pedidas.push(url);
      return new Blob([`bytes de ${url}`]);
    },
  };
}

// --- critério 1: N selecionados, N arquivos ---------------------------------------------

describe("baixar a seleção", () => {
  it("monta um zip com os arquivos selecionados e o salva com nome de campeão", async () => {
    const { buscar, pedidas } = servidor();
    const salvos: { nome: string; blob: Blob }[] = [];

    render(
      <BarraDeLote
        assets={[asset("Jax_000"), asset("Jax_007")]}
        rotulo="Jax"
        onLimpar={() => {}}
        montar={(assets, base, deps) => montarZip(assets, base, { ...deps, buscar })}
        salvar={(blob, nome) => salvos.push({ nome, blob })}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Baixar 2 como zip/ }));
    await waitFor(() => expect(salvos).toHaveLength(1));

    expect(salvos[0].nome).toBe("lol-assets-jax.zip");
    const lido = await JSZip.loadAsync(await salvos[0].blob.arrayBuffer());
    expect(Object.keys(lido.files).sort()).toEqual(["Jax_000.jpg", "Jax_007.jpg"]);
    // Critério 2, de novo na tela: só as URLs das fontes.
    expect(pedidas.every((url) => url.startsWith("https://ddragon.leagueoflegends.com/"))).toBe(
      true,
    );
  });

  it("diz quantos arquivos entraram quando termina", async () => {
    const { buscar } = servidor();
    render(
      <BarraDeLote
        assets={[asset("a"), asset("b"), asset("c")]}
        onLimpar={() => {}}
        montar={(assets, base, deps) => montarZip(assets, base, { ...deps, buscar })}
        salvar={() => {}}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Baixar 3 como zip/ }));
    await waitFor(() => expect(screen.getByRole("status").textContent).toContain("3 arquivos"));
  });

  it("o que não veio é dito na tela, não só dentro do zip", async () => {
    render(
      <BarraDeLote
        assets={[asset("a"), asset("morto")]}
        onLimpar={() => {}}
        montar={(assets, base, deps) =>
          montarZip(assets, base, {
            ...deps,
            buscar: async (url) => {
              if (url.includes("morto")) throw new Error("HTTP 404");
              return new Blob(["x"]);
            },
          })
        }
        salvar={() => {}}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Baixar 2 como zip/ }));
    await waitFor(() => {
      const texto = screen.getByRole("status").textContent ?? "";
      expect(texto).toContain("1 arquivo");
      expect(texto).toContain("FALHAS.txt");
    });
  });

  it("seleção vazia não desenha barra nenhuma", () => {
    const { container } = render(<BarraDeLote assets={[]} onLimpar={() => {}} />);
    expect(container.firstChild).toBeNull();
  });

  it("falha na montagem aparece e não trava a barra", async () => {
    render(
      <BarraDeLote
        assets={[asset("a")]}
        onLimpar={() => {}}
        montar={async () => {
          throw new Error("sem memória");
        }}
        salvar={() => {}}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Baixar 1 como zip/ }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("sem memória"));
    expect((screen.getByRole("button", { name: /Baixar 1/ }) as HTMLButtonElement).disabled).toBe(
      false,
    );
  });
});

// --- critério 3: o aviso informa, não bloqueia -------------------------------------------

describe("acima do limite", () => {
  const muitos = Array.from({ length: LIMITE_DE_ARQUIVOS + 1 }, (_, i) => asset(`a${i}`));

  it("avisa com a estimativa de tempo", () => {
    render(<BarraDeLote assets={muitos} onLimpar={() => {}} />);
    const alerta = screen.getByRole("alert").textContent ?? "";
    expect(alerta).toContain("301 arquivos");
    expect(alerta).toMatch(/\d+ s/);
    expect(alerta).toContain("Dá para continuar");
  });

  it("o botão continua habilitado — é aviso, não bloqueio", () => {
    render(<BarraDeLote assets={muitos} onLimpar={() => {}} />);
    const botao = screen.getByRole("button", { name: /Baixar 301 como zip/ }) as HTMLButtonElement;
    expect(botao.disabled).toBe(false);
  });

  it("no limite exato, não avisa", () => {
    render(<BarraDeLote assets={muitos.slice(0, LIMITE_DE_ARQUIVOS)} onLimpar={() => {}} />);
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

// --- progresso --------------------------------------------------------------------------

describe("progresso durante a montagem", () => {
  it("mostra quantos de quantos, porque 31 s sem sinal parece travado", async () => {
    let avisar: ((p: { feitos: number; total: number; falhas: number }) => void) | undefined;
    const nuncaTermina = new Promise<never>(() => {});

    render(
      <BarraDeLote
        assets={[asset("a"), asset("b"), asset("c")]}
        onLimpar={() => {}}
        montar={(_assets, _base, deps) => {
          avisar = deps?.onProgresso;
          return nuncaTermina;
        }}
        salvar={() => {}}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Baixar 3 como zip/ }));
    await waitFor(() => expect(screen.getByRole("status")).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    avisar?.({ feitos: 2, total: 3, falhas: 0 });
    await waitFor(() => expect(screen.getByRole("status").textContent).toContain("2 de 3"));

    const barra = within(screen.getByRole("status")).getByRole("progressbar");
    expect(barra.getAttribute("value")).toBe("2");
    expect(barra.getAttribute("max")).toBe("3");
  });
});

// --- critério 4: tudo deste campeão (RF-18) ---------------------------------------------

describe("tudo deste campeão", () => {
  const ASSETS: Asset[] = [
    asset("square", { type: "square", skinNum: undefined }),
    asset("splash0", { type: "splash_centered", skinId: 24000, skinNum: 0, isBaseSkin: true }),
    asset("tile0", { type: "tile", skinId: 24000, skinNum: 0 }),
    asset("chroma1", { type: "chroma", skinId: 24009, skinNum: 9, parentSkinNum: 0 }),
    asset("chroma2", { type: "chroma", skinId: 24010, skinNum: 10, parentSkinNum: 0 }),
  ];
  const SKINS: CatalogSkin[] = [
    { skinId: 24000, skinNum: 0, championKey: 24, names: { pt_BR: "Jax" }, isBase: true },
  ];
  const JAX: CatalogChampion = {
    championKey: 24,
    championId: "Jax",
    names: { pt_BR: "Jax" },
    skinCount: 1,
    baseSkinId: 24000,
  };

  function painel() {
    return render(
      <PainelDoCampeao champion={JAX} skins={SKINS} assets={ASSETS} onClose={() => {}} />,
    );
  }

  it("com os chromas escondidos, leva só o que está na tela (RF-06)", () => {
    painel();
    fireEvent.click(screen.getByRole("button", { name: /^Tudo de Jax/ }));
    expect(screen.getByLabelText("Seleção").textContent).toContain("3 selecionados");
  });

  it("com os chromas revelados, leva os chromas junto", () => {
    painel();
    fireEvent.click(screen.getByRole("button", { name: /Mostrar 2 chromas/ }));
    fireEvent.click(screen.getByRole("button", { name: /^Tudo de Jax/ }));
    expect(screen.getByLabelText("Seleção").textContent).toContain("5 selecionados");
  });

  it("marcar um por um também soma, e a caixa desmarca", () => {
    painel();
    fireEvent.click(screen.getByLabelText("Selecionar splash0.jpg"));
    expect(screen.getByLabelText("Seleção").textContent).toContain("1 selecionado");
    fireEvent.click(screen.getByLabelText("Selecionar tile0.jpg"));
    expect(screen.getByLabelText("Seleção").textContent).toContain("2 selecionados");
    fireEvent.click(screen.getByLabelText("Selecionar splash0.jpg"));
    expect(screen.getByLabelText("Seleção").textContent).toContain("1 selecionado");
  });

  it("limpar zera e a barra some", () => {
    painel();
    fireEvent.click(screen.getByRole("button", { name: /^Tudo de Jax/ }));
    fireEvent.click(screen.getByRole("button", { name: "Limpar seleção" }));
    expect(screen.queryByLabelText("Seleção")).toBeNull();
  });

  it("trocar de campeão não carrega a seleção do anterior junto", () => {
    const { rerender } = painel();
    fireEvent.click(screen.getByRole("button", { name: /^Tudo de Jax/ }));
    expect(screen.getByLabelText("Seleção")).toBeTruthy();

    const lux: CatalogChampion = { ...JAX, championKey: 99, championId: "Lux", names: { pt_BR: "Lux" } };
    rerender(<PainelDoCampeao champion={lux} skins={[]} assets={[]} onClose={() => {}} />);
    expect(screen.queryByLabelText("Seleção")).toBeNull();
  });

  it("sem `onAlternar`, o painel de asset não desenha caixa nenhuma", () => {
    render(<PainelDeAsset titulo="Jax" assets={ASSETS} onClose={vi.fn()} />);
    expect(screen.queryByLabelText(/^Selecionar /)).toBeNull();
    // Os botões de download continuam lá: lote é adicional, não substituto.
    expect(screen.getAllByRole("button", { name: "Baixar original" })).toHaveLength(5);
  });
});
