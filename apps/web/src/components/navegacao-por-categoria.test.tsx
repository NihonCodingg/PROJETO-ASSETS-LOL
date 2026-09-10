import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useEffect, useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Asset, AssetCategory, CatalogChampion, IndexShard } from "@lol-assets/schema";

import { AssetsClient } from "@/lib/assets-client";
import { categoriasDisponiveis } from "@/lib/categorias";

import { GradeDeCampeoes } from "./grade-de-campeoes";
import { ProvedorDeNavegacao, useNavegacao } from "./navegacao-context";
import { NavegacaoPorCategoria } from "./navegacao-por-categoria";
import { PainelDeAsset } from "./painel-de-asset";
import { Rodape } from "./rodape";

/**
 * O RF-08 na escala real: 5.042 ícones de perfil numa categoria e 868 itens que
 * abrem filtrados por decisão da §B.1.6 do KICKOFF.
 *
 * Os dois números que mais importam aqui não são de tela, são de rede e de DOM:
 * **nenhuma fatia é buscada antes do clique** (RNF-03) e **nenhuma lista grande
 * vira 5.042 nós** ([ADR 0011]).
 */

afterEach(cleanup);

// --- fixture --------------------------------------------------------------------------

function asset(id: string, extra: Partial<Asset> = {}): Asset {
  return {
    id,
    type: "item_icon",
    category: "item",
    names: { pt_BR: id },
    source: "ddragon",
    sourceUrl: `https://exemplo.invalido/${id}.png`,
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

const ITENS: Asset[] = [
  asset("botas", {
    names: { pt_BR: "Botas de Velocidade" },
    tags: ["compravel", "mapa:sr", "mapa:aram", "classe:boots"],
  }),
  asset("elmo", { names: { pt_BR: "Elmo de Aço" }, tags: ["compravel", "mapa:sr"] }),
  asset("poro", { names: { pt_BR: "Petisco de Poro" }, tags: ["compravel", "mapa:aram"] }),
  asset("missao", { names: { pt_BR: "Item de Missão" }, tags: ["mapa:sr"] }),
];

const RUNAS: Asset[] = [
  asset("8005", {
    type: "rune_icon",
    category: "rune",
    refId: "8005",
    names: { pt_BR: "Ataque Letal" },
    tags: ["arvore:8000", "slot:0"],
  }),
  asset("statmod", {
    type: "stat_mod_icon",
    category: "rune",
    refId: "statmod",
    names: { pt_BR: "Adaptável" },
    tags: ["arvore:nenhuma"],
  }),
];

/** 5.042 — o tamanho medido da categoria no patch 16.18.1. */
const ICONES: Asset[] = Array.from({ length: 5042 }, (_, i) =>
  asset(`icone-${i}`, {
    type: "profile_icon",
    category: "profile_icon",
    names: { pt_BR: `Ícone ${i}` },
  }),
);

function fatia(category: AssetCategory, assets: Asset[]): IndexShard {
  return {
    schemaVersion: "1.1.0",
    gameVersion: "16.18.1",
    category,
    generatedAt: "2026-09-09T00:00:00Z",
    assets,
  };
}

const FATIAS: Partial<Record<AssetCategory, IndexShard>> = {
  item: fatia("item", ITENS),
  rune: fatia("rune", RUNAS),
  profile_icon: fatia("profile_icon", ICONES),
};

const SHARDS = [
  { category: "champion" },
  { category: "item" },
  { category: "rune" },
  { category: "profile_icon" },
];

/**
 * O palco: o que a barra lateral faz de verdade, em miniatura.
 *
 * Desde o **T-41** os botões de categoria vivem na barra lateral, e este
 * componente é o conteúdo. O palco reproduz o mínimo — uma lista de botões que
 * controla a prop `aberta` — para que os testes de comportamento continuem
 * escritos em cliques, que é como alguém usa a tela.
 *
 * Quem prova que a **barra lateral de verdade** desenha os botões certos é o
 * bloco "barra lateral" no fim deste arquivo, montando o `Rodape` com provedor.
 */
function Palco({
  shards,
  carregar,
}: {
  shards: readonly { category: string }[];
  carregar: (c: AssetCategory) => Promise<IndexShard>;
}) {
  const [aberta, setAberta] = useState<AssetCategory | null>(null);
  return (
    <>
      {categoriasDisponiveis(shards).map((categoria) => (
        <button
          key={categoria.category}
          type="button"
          onClick={() => setAberta(categoria.category)}
        >
          {categoria.rotulo}
        </button>
      ))}
      <NavegacaoPorCategoria
        aberta={aberta}
        carregar={carregar}
        onFechar={() => setAberta(null)}
      />
    </>
  );
}

function montar(shards = SHARDS) {
  const pedidas: AssetCategory[] = [];
  const carregar = vi.fn(async (category: AssetCategory) => {
    pedidas.push(category);
    const shard = FATIAS[category];
    if (!shard) throw new Error(`sem fatia ${category}`);
    return shard;
  });
  const tela = render(<Palco shards={shards} carregar={carregar} />);
  return { ...tela, pedidas, carregar };
}

async function abrir(rotulo: string) {
  fireEvent.click(screen.getByRole("button", { name: rotulo }));
  await waitFor(() => expect(screen.queryByText(/^carregando /)).toBeNull());
}

// --- carga sob demanda (critérios 1 e 3) ---------------------------------------------

describe("carga sob demanda", () => {
  it("nada é buscado antes do primeiro clique", () => {
    const { carregar } = montar();
    expect(carregar).not.toHaveBeenCalled();
  });

  it("abrir uma categoria busca só a fatia dela", async () => {
    const { pedidas } = montar();
    await abrir("Itens");
    expect(pedidas).toEqual(["item"]);
  });

  it("abrir outra categoria não rebusca a primeira", async () => {
    const { pedidas } = montar();
    await abrir("Itens");
    await abrir("Runas");
    expect(pedidas).toEqual(["item", "rune"]);
  });

  it("a fatia champion nunca é pedida por aqui", async () => {
    const { pedidas } = montar();
    await abrir("Itens");
    await abrir("Runas");
    await abrir("Ícones de perfil");
    expect(pedidas).not.toContain("champion");
  });

  it("erro de carga aparece sem derrubar a navegação", async () => {
    const carregar = vi.fn(async () => {
      throw new Error("HTTP 503");
    });
    render(<Palco shards={SHARDS} carregar={carregar} />);
    fireEvent.click(screen.getByRole("button", { name: "Itens" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("HTTP 503"));
    expect(screen.getByRole("button", { name: "Runas" })).toBeTruthy();
  });
});

// --- pela rede de verdade, com o AssetsClient no meio ----------------------------------

describe("uma fatia por categoria, contado em requisições", () => {
  it("só a URL da categoria aberta é buscada", async () => {
    const manifesto = {
      schemaVersion: "1.1.0",
      generatedAt: "2026-09-09T00:00:00Z",
      currentVersion: "16.18.1",
      versions: [
        {
          gameVersion: "16.18.1",
          indexedAt: "2026-09-09T00:00:00Z",
          assetsCopied: false,
          catalog: { url: "catalog-a.json", champions: 173, skins: 2121, bytes: 1 },
          shards: [
            { category: "champion", url: "index-champion-a.json", assets: 18389, bytes: 1 },
            { category: "item", url: "index-item-a.json", assets: 4, bytes: 1 },
            { category: "rune", url: "index-rune-a.json", assets: 2, bytes: 1 },
          ],
        },
      ],
    };
    const corpos: Record<string, unknown> = {
      "manifest.json": manifesto,
      "index-item-a.json": FATIAS.item,
      "index-rune-a.json": FATIAS.rune,
    };
    const chamadas: string[] = [];
    const cliente = new AssetsClient("https://exemplo.invalido", async (url) => {
      chamadas.push(url);
      const corpo = corpos[url.split("/").pop() ?? ""];
      return corpo
        ? new Response(JSON.stringify(corpo), { status: 200 })
        : new Response("não", { status: 404 });
    });
    const manifest = await cliente.loadManifest();
    chamadas.length = 0;

    render(
      <Palco
        shards={manifest.versions[0].shards}
        carregar={(category) => cliente.loadShard(manifest, category)}
      />,
    );
    await abrir("Itens");

    expect(chamadas).toEqual(["https://exemplo.invalido/index-item-a.json"]);

    // Voltar para a mesma categoria não gera requisição nova: o cliente memoiza.
    await abrir("Runas");
    await abrir("Itens");
    expect(chamadas.filter((url) => url.includes("index-item"))).toHaveLength(1);
    expect(chamadas.some((url) => url.includes("index-champion"))).toBe(false);
  });
});

// --- os filtros (critério 2) -----------------------------------------------------------

describe("filtros", () => {
  it("item abre marcado em comprável e SR (§B.1.6)", async () => {
    montar();
    await abrir("Itens");
    expect((screen.getByLabelText(/^sim/) as HTMLInputElement).checked).toBe(true);
    expect((screen.getByLabelText(/Summoner's Rift/) as HTMLInputElement).checked).toBe(true);
    // botas, elmo e missão estão no SR; só os dois primeiros são compráveis.
    expect(screen.getByText("2 de 4")).toBeTruthy();
  });

  it("mostrar tudo desmarca e a lista volta inteira", async () => {
    montar();
    await abrir("Itens");
    fireEvent.click(screen.getByRole("button", { name: "Mostrar tudo" }));
    expect(screen.getByText("4 de 4")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Mostrar tudo" })).toBeNull();
  });

  it("marcar duas opções do mesmo grupo é OU", async () => {
    montar();
    await abrir("Itens");
    fireEvent.click(screen.getByRole("button", { name: "Mostrar tudo" }));
    fireEvent.click(screen.getByLabelText(/Summoner's Rift/));
    expect(screen.getByText("3 de 4")).toBeTruthy();
    fireEvent.click(screen.getByLabelText(/ARAM/));
    expect(screen.getByText("4 de 4")).toBeTruthy();
  });

  it("marcar em grupos diferentes é E", async () => {
    montar();
    await abrir("Itens");
    fireEvent.click(screen.getByRole("button", { name: "Mostrar tudo" }));
    fireEvent.click(screen.getByLabelText(/ARAM/));
    expect(screen.getByText("2 de 4")).toBeTruthy();
    fireEvent.click(screen.getByLabelText(/^boots/));
    expect(screen.getByText("1 de 4")).toBeTruthy();
  });

  it("o texto combina com as etiquetas", async () => {
    montar();
    await abrir("Itens");
    fireEvent.change(screen.getByLabelText("Filtrar por texto"), { target: { value: "poro" } });
    // O padrão de item exige SR, e o Petisco de Poro é só de ARAM.
    expect(screen.getByText("0 de 4")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Mostrar tudo" }));
    expect(screen.getByText("1 de 4")).toBeTruthy();
  });

  it("o grupo é derivado da fatia, não declarado: runa traz árvore, item não", async () => {
    montar();
    await abrir("Runas");
    expect(screen.getByRole("group", { name: "Árvore de runa" })).toBeTruthy();
    expect(screen.queryByRole("group", { name: "Mapa" })).toBeNull();
    // O rótulo da árvore sai do nome do próprio ícone; `nenhuma` é dos stat mods.
    expect(screen.getByLabelText(/sem árvore/)).toBeTruthy();
  });

  it("categoria sem etiqueta nenhuma não mostra filtro nenhum", async () => {
    montar();
    await abrir("Ícones de perfil");
    expect(screen.queryAllByRole("group")).toHaveLength(0);
    expect(screen.getByText("5042 de 5042")).toBeTruthy();
  });

  it("trocar de categoria limpa o texto digitado", async () => {
    montar();
    await abrir("Itens");
    fireEvent.change(screen.getByLabelText("Filtrar por texto"), { target: { value: "botas" } });
    await abrir("Runas");
    expect((screen.getByLabelText("Filtrar por texto") as HTMLInputElement).value).toBe("");
  });
});

// --- o vazio (critério 4) --------------------------------------------------------------

describe("estado vazio", () => {
  it("diz o que estava filtrado, não só que deu zero", async () => {
    montar();
    await abrir("Itens");
    fireEvent.change(screen.getByLabelText("Filtrar por texto"), {
      target: { value: "não existe" },
    });

    const vazio = screen.getByRole("status");
    expect(vazio.textContent).toContain("Nenhum asset");
    const aplicado = within(vazio).getByRole("list", { name: "Filtro aplicado" });
    expect(aplicado.textContent).toContain("Comprável: sim");
    expect(aplicado.textContent).toContain("Mapa: Summoner's Rift");
    expect(aplicado.textContent).toContain("não existe");
  });
});

// --- a escala (critério 5) --------------------------------------------------------------

describe("5.042 ícones de perfil", () => {
  /**
   * jsdom não faz layout: `offsetHeight` é sempre 0, e um virtualizador que não
   * enxerga viewport nenhuma conclui, com razão, que não há nada visível — e
   * desenha **zero** cartões. Zero passaria numa asserção de "poucos nós" sem
   * provar coisa alguma.
   *
   * Emprestar uma janela de 700 px é o que faz o teste medir o que interessa:
   * **tendo** o que desenhar, quantos nós ele desenha. 700 px sobre cartões de
   * 132 px são ~6 visíveis mais 6 de folga do `overscan`.
   *
   * `offsetHeight` e não `getBoundingClientRect`: é o que o `getRect` do
   * virtual-core lê.
   */
  const original = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "offsetHeight");

  beforeEach(() => {
    Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
      configurable: true,
      get: () => 700,
    });
  });

  afterEach(() => {
    if (original) Object.defineProperty(HTMLElement.prototype, "offsetHeight", original);
  });

  it("a lista da categoria é virtual", async () => {
    const { container } = montar();
    await abrir("Ícones de perfil");
    expect(container.querySelector("[data-virtual='sim']")).not.toBeNull();
  });

  it("o DOM fica na casa das dezenas, não das milhares", async () => {
    const { container } = montar();
    await abrir("Ícones de perfil");
    const scroller = container.querySelector("[data-virtual='sim']");
    const cartoes = scroller?.querySelectorAll("article") ?? [];
    // Desenha o que cabe na janela e nada além dela: dezenas, não 5.042.
    expect(cartoes.length).toBeGreaterThan(5);
    expect(cartoes.length).toBeLessThan(100);
    // Um <li> por cartão: o scroller não deixa 5.042 nós vazios para trás.
    expect(scroller?.querySelectorAll("li")).toHaveLength(cartoes.length);
  });

  it("a contagem diz a verdade mesmo com o DOM pequeno", async () => {
    montar();
    await abrir("Ícones de perfil");
    expect(screen.getByText("5042 assets")).toBeTruthy();
  });

  it("filtrar por texto reduz o total sem sair da lista virtual", async () => {
    const { container } = montar();
    await abrir("Ícones de perfil");
    fireEvent.change(screen.getByLabelText("Filtrar por texto"), { target: { value: "icone-1" } });
    // icone-1, icone-1x, icone-1xx, icone-1xxx: 1 + 10 + 100 + 1000 = 1.111.
    expect(screen.getByText("1111 de 5042")).toBeTruthy();
    expect(container.querySelector("[data-virtual='sim']")).not.toBeNull();
  });
});

describe("o painel do campeão não paga scroller", () => {
  it("lista pequena continua sendo um <ul> simples", () => {
    const { container } = render(
      <PainelDeAsset titulo="Jax" assets={ITENS} onClose={() => {}} />,
    );
    expect(container.querySelector("[data-virtual='sim']")).toBeNull();
    expect(container.querySelectorAll("article")).toHaveLength(4);
  });
});

// --- função, na grade de campeões -------------------------------------------------------

describe("filtro por função (RF-08)", () => {
  /** As seis funções e a distribuição real do patch 16.18.1, em miniatura. */
  const CAMPEOES: CatalogChampion[] = [
    { championKey: 24, championId: "Jax", names: { pt_BR: "Jax" }, tags: ["Fighter"], skinCount: 18, baseSkinId: 24000 },
    { championKey: 99, championId: "Lux", names: { pt_BR: "Lux" }, tags: ["Mage", "Support"], skinCount: 12, baseSkinId: 99000 },
    { championKey: 20, championId: "Nunu", names: { pt_BR: "Nunu e Willump" }, tags: ["Tank", "Fighter"], skinCount: 9, baseSkinId: 20000 },
  ];

  function grade() {
    return render(<GradeDeCampeoes champions={CAMPEOES} onAbrir={() => {}} />);
  }

  it("as funções vêm do catálogo, em português, com a contagem", () => {
    grade();
    expect(screen.getByLabelText("Lutador (2)")).toBeTruthy();
    expect(screen.getByLabelText("Mago (1)")).toBeTruthy();
    expect(screen.queryByLabelText(/Atirador/)).toBeNull();
  });

  it("marcar uma função reduz a grade", () => {
    grade();
    fireEvent.click(screen.getByLabelText("Mago (1)"));
    expect(screen.getByText("1 de 3 campeões")).toBeTruthy();
    const lista = screen.getByRole("list", { name: "Campeões" });
    expect(within(lista).getAllByRole("listitem")).toHaveLength(1);
  });

  it("duas funções são OU, e o campeão das duas aparece uma vez só", () => {
    grade();
    fireEvent.click(screen.getByLabelText("Lutador (2)"));
    fireEvent.click(screen.getByLabelText("Tanque (1)"));
    expect(screen.getByText("2 de 3 campeões")).toBeTruthy();
  });

  it("limpar volta a grade inteira", () => {
    grade();
    fireEvent.click(screen.getByLabelText("Mago (1)"));
    fireEvent.click(screen.getByRole("button", { name: "Todas as funções" }));
    expect(screen.getByText("3 de 3 campeões")).toBeTruthy();
  });

  it("catálogo sem função nenhuma não mostra o filtro", () => {
    render(
      <GradeDeCampeoes
        champions={[{ ...CAMPEOES[0], tags: undefined }]}
        onAbrir={() => {}}
      />,
    );
    expect(screen.queryByRole("group", { name: "Função" })).toBeNull();
  });
});

// --- a barra lateral, que é onde as categorias moram desde o T-41 ---------------------

describe("barra lateral", () => {
  /** A página registra as categorias assim que o manifesto chega. */
  function Registra({ shards }: { shards: readonly { category: string }[] }) {
    const { registrar } = useNavegacao();
    useEffect(() => registrar(categoriasDisponiveis(shards)), [registrar, shards]);
    return null;
  }

  function barra(shards: readonly { category: string }[] = SHARDS) {
    return render(
      <ProvedorDeNavegacao>
        <Registra shards={shards} />
        <Rodape />
      </ProvedorDeNavegacao>,
    );
  }

  it("lista as categorias que o manifesto declara", () => {
    barra();
    const nav = screen.getByRole("navigation", { name: "Categorias" });
    expect(within(nav).getByRole("button", { name: "Itens" })).toBeTruthy();
    expect(within(nav).getByRole("button", { name: "Runas" })).toBeTruthy();
  });

  it("categoria que o manifesto não declara não vira botão", () => {
    barra([{ category: "champion" }, { category: "item" }]);
    const nav = screen.getByRole("navigation", { name: "Categorias" });
    expect(within(nav).getByRole("button", { name: "Itens" })).toBeTruthy();
    expect(within(nav).queryByRole("button", { name: "Runas" })).toBeNull();
    expect(within(nav).queryByRole("button", { name: "Emotes" })).toBeNull();
  });

  it("Campeões é a primeira, e é a que abre marcada (RF-04)", () => {
    barra();
    const botoes = within(screen.getByRole("navigation", { name: "Categorias" })).getAllByRole(
      "button",
    );
    expect(botoes[0].textContent).toBe("Campeões");
    expect(botoes[0].getAttribute("aria-pressed")).toBe("true");
  });

  it("clicar numa categoria marca ela e desmarca Campeões", () => {
    barra();
    const nav = screen.getByRole("navigation", { name: "Categorias" });
    fireEvent.click(within(nav).getByRole("button", { name: "Itens" }));

    expect(within(nav).getByRole("button", { name: "Itens" }).getAttribute("aria-pressed")).toBe(
      "true",
    );
    expect(
      within(nav).getByRole("button", { name: "Campeões" }).getAttribute("aria-pressed"),
    ).toBe("false");
  });

  it("sem provedor, a barra não desenha categoria nenhuma", () => {
    // É como o teste do T-27 monta o `Rodape`. O aviso legal continua lá.
    const { container } = render(<Rodape />);
    expect(screen.queryByRole("navigation", { name: "Categorias" })).toBeNull();
    expect(container.querySelector("[data-aviso='riot']")).not.toBeNull();
  });
});
