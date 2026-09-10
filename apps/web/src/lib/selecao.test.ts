import { describe, expect, it } from "vitest";

import type { Asset } from "@lol-assets/schema";

import {
  alternar,
  ARQUIVOS_POR_SEGUNDO,
  aviso,
  duracao,
  LIMITE_DE_ARQUIVOS,
  LIMITE_DE_BYTES,
  nomeDoZip,
  nomesUnicos,
  resumir,
  selecionados,
  tudoDo,
} from "./selecao";

/**
 * O orçamento do lote, com os números da §6.1 da Spec.
 *
 * A estimativa existe porque não há mais para onde mandar quem selecionou
 * demais: o zip por categoria morreu com o [ADR 0012]. Se ela mentir, a pessoa
 * fecha a aba no meio de três minutos de montagem achando que travou.
 */

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

const muitos = (quantos: number, bytes = 1000) =>
  Array.from({ length: quantos }, (_, i) => asset(`a${i}`, { bytes }));

// --- o resumo ----------------------------------------------------------------------------

describe("resumo da seleção", () => {
  it("soma arquivos e bytes", () => {
    const resumo = resumir([asset("a", { bytes: 1500 }), asset("b", { bytes: 2500 })]);
    expect(resumo.arquivos).toBe(2);
    expect(resumo.bytes).toBe(4000);
  });

  it("estima pelo que foi medido, não por chute", () => {
    // 868 ícones de item / 28 por segundo = 31 s, o número da §6.1 da Spec.
    expect(resumir(muitos(868)).segundos).toBe(31);
    expect(ARQUIVOS_POR_SEGUNDO).toBe(28);
  });

  it("os 5.042 ícones de perfil dão pouco mais de 3 min", () => {
    // 5.042 / 28 = 181 s. A §6.1 da Spec dizia "3 minutos e meio", que não sai
    // da taxa que ela mesma declara; a linha foi corrigida junto com este teste.
    expect(duracao(resumir(muitos(5042)).segundos)).toBe("3 min 1 s");
  });

  it("seleção vazia não é pesada e não estima nada", () => {
    expect(resumir([])).toMatchObject({ arquivos: 0, bytes: 0, segundos: 0, pesada: false });
  });
});

describe("quando avisar", () => {
  it("no limite de arquivos ainda não avisa", () => {
    expect(resumir(muitos(LIMITE_DE_ARQUIVOS)).pesada).toBe(false);
  });

  it("um arquivo acima do limite avisa", () => {
    expect(resumir(muitos(LIMITE_DE_ARQUIVOS + 1)).pesada).toBe(true);
  });

  it("poucos arquivos e muitos bytes também avisam", () => {
    const gordo = [asset("a", { bytes: LIMITE_DE_BYTES + 1 })];
    expect(resumir(gordo).pesada).toBe(true);
    expect(resumir(gordo).arquivos).toBe(1);
  });

  it("o aviso diz o tempo, o tamanho e que dá para continuar", () => {
    const texto = aviso(resumir(muitos(868, 600_000)));
    expect(texto).toContain("868 arquivos");
    expect(texto).toContain("31 s");
    expect(texto).toContain("MB");
    expect(texto).toContain("Dá para continuar");
  });
});

describe("duração em palavras", () => {
  it("abaixo de um minuto, segundos", () => {
    expect(duracao(31)).toBe("31 s");
  });

  it("minuto redondo não inventa segundos", () => {
    expect(duracao(120)).toBe("2 min");
  });

  it("o resto aparece, em vez de ser arredondado para baixo", () => {
    expect(duracao(215)).toBe("3 min 35 s");
  });
});

// --- nomes ------------------------------------------------------------------------------

describe("nomes dentro do zip", () => {
  it("sem colisão, cada um mantém o seu", () => {
    const nomes = nomesUnicos([asset("a"), asset("b")]);
    expect([...nomes.values()]).toEqual(["a.png", "b.png"]);
  });

  it("colisão vira (2), (3) — e nenhum arquivo some", () => {
    const nomes = nomesUnicos([
      asset("x", { fileName: "Jax.jpg" }),
      asset("y", { fileName: "Jax.jpg" }),
      asset("z", { fileName: "Jax.jpg" }),
    ]);
    expect([...nomes.values()]).toEqual(["Jax.jpg", "Jax (2).jpg", "Jax (3).jpg"]);
    expect(new Set(nomes.values()).size).toBe(3);
  });

  it("nome sem extensão também é desambiguado", () => {
    const nomes = nomesUnicos([asset("x", { fileName: "LEIA" }), asset("y", { fileName: "LEIA" })]);
    expect([...nomes.values()]).toEqual(["LEIA", "LEIA (2)"]);
  });
});

describe("nome do arquivo zip", () => {
  it("usa o rótulo, sem acento e sem espaço", () => {
    expect(nomeDoZip("Nunu e Willump", 9)).toBe("lol-assets-nunu-e-willump.zip");
    expect(nomeDoZip("Prestígio K/DA", 3)).toBe("lol-assets-prestigio-k-da.zip");
  });

  it("sem rótulo, o número de arquivos serve", () => {
    expect(nomeDoZip(undefined, 12)).toBe("lol-assets-selecao-12.zip");
  });

  it("rótulo que vira nada não deixa o nome quebrado", () => {
    expect(nomeDoZip("!!!", 4)).toBe("lol-assets-selecao-4.zip");
  });
});

// --- a seleção --------------------------------------------------------------------------

describe("alternar", () => {
  it("marca o que não estava", () => {
    expect([...alternar(new Set(), "a")]).toEqual(["a"]);
  });

  it("desmarca o que estava", () => {
    expect([...alternar(new Set(["a", "b"]), "a")]).toEqual(["b"]);
  });

  it("não muda o conjunto original", () => {
    const antes = new Set(["a"]);
    alternar(antes, "b");
    expect([...antes]).toEqual(["a"]);
  });
});

describe("selecionados", () => {
  const lista = [asset("a"), asset("b"), asset("c")];

  it("saem na ordem da lista, não na de clique", () => {
    expect(selecionados(lista, new Set(["c", "a"])).map((x) => x.id)).toEqual(["a", "c"]);
  });

  it("id que não está na lista é ignorado", () => {
    expect(selecionados(lista, new Set(["z"]))).toEqual([]);
  });
});

// --- RF-18 ------------------------------------------------------------------------------

describe("tudo deste campeão", () => {
  const doJax = [
    asset("square", { type: "square" }),
    asset("splash", { type: "splash_centered" }),
    asset("chroma1", { type: "chroma" }),
    asset("chroma2", { type: "chroma" }),
  ];

  it("com os chromas revelados, leva os chromas", () => {
    expect(tudoDo(doJax, true).size).toBe(4);
  });

  it("com os chromas escondidos, não leva o que a tela não mostrou (RF-06)", () => {
    const selecao = tudoDo(doJax, false);
    expect(selecao.size).toBe(2);
    expect(selecao.has("chroma1")).toBe(false);
  });

  it("campeão sem asset nenhum devolve seleção vazia", () => {
    expect(tudoDo([], true).size).toBe(0);
  });
});
