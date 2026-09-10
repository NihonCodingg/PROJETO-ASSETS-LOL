import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { siteConfig } from "./site-config";

/**
 * T-33 — a parte do lançamento que dá para automatizar.
 *
 * O resto do checklist depende de conta e de dinheiro do dono do projeto e está
 * em [`docs/LANCAMENTO.md`](../../../../docs/LANCAMENTO.md), marcado com 🔑.
 * Estes testes cobrem o que uma máquina consegue afirmar sozinha: que o nome
 * saiu do provisório, que ele respeita a política, e que ninguém deixou um
 * marcador de decisão pendente no código sem que a lista cresça na cara de
 * quem revisa.
 */

const raiz = resolve(process.cwd(), "../..");
const codigo = resolve(process.cwd(), "src");

// --- D1: o nome -----------------------------------------------------------------------

describe("nome público (D1)", () => {
  it("não é mais o rótulo provisório", () => {
    expect(siteConfig.displayName).not.toBe("Catálogo de Assets");
    expect(siteConfig.displayName).toBe("Biblioteca de Assets");
  });

  it("não contém nenhuma das três palavras proibidas (ADR 0003)", () => {
    const nome = siteConfig.displayName.toLowerCase();
    for (const proibida of ["riot", "league of legends", "lol"]) {
      expect(nome.includes(proibida), `"${proibida}" no nome público`).toBe(false);
    }
  });

  it("o aviso legal é derivado do nome, não escrito à mão", () => {
    // Se alguém trocar o nome e esquecer o aviso, o aviso deixa de citar o
    // produto — e é o produto que a política manda nomear.
    expect(siteConfig.riotLegalNotice.startsWith(siteConfig.displayName)).toBe(true);
  });
});

// --- marcadores de decisão pendente ----------------------------------------------------

/**
 * Os marcadores que **ainda** existem no código, e por quê.
 *
 * A lista tem que chegar a zero antes de publicar — é o critério 5 do T-33. Ela
 * está aqui em vez de o teste simplesmente falhar porque o item que falta
 * (`[A CONFIRMAR]` do texto legal) depende de alguém abrir a Developer API
 * Policy e comparar palavra a palavra. Fingir que não existe seria pior; deixar
 * a suíte vermelha até lá tornaria a suíte inútil.
 *
 * O que o teste garante é que **nenhum marcador novo** apareça sem que alguém
 * tenha que vir aqui e escrever o motivo.
 */
const PENDENTES: ReadonlyArray<{ arquivo: string; marcador: string; porque: string }> = [
  {
    arquivo: "lib/site-config.ts",
    marcador: "[A CONFIRMAR]",
    porque: "D6: o texto do aviso precisa ser comparado com a Developer API Policy à mão.",
  },
];

function arquivosDeCodigo(pasta: string): string[] {
  return readdirSync(pasta).flatMap((nome) => {
    const caminho = join(pasta, nome);
    if (statSync(caminho).isDirectory()) return arquivosDeCodigo(caminho);
    return /\.tsx?$/.test(nome) && !/\.test\.tsx?$/.test(nome) ? [caminho] : [];
  });
}

describe("marcadores de decisão", () => {
  const achados = arquivosDeCodigo(codigo).flatMap((caminho) => {
    const texto = readFileSync(caminho, "utf-8");
    return ["[A DECIDIR]", "[A CONFIRMAR]"]
      .filter((marcador) => texto.includes(marcador))
      .map((marcador) => ({
        arquivo: relative(codigo, caminho).replace(/\\/g, "/"),
        marcador,
      }));
  });

  it("nenhum marcador novo entrou sem justificativa", () => {
    const conhecidos = new Set(PENDENTES.map((p) => `${p.arquivo}:${p.marcador}`));
    const novos = achados.filter((a) => !conhecidos.has(`${a.arquivo}:${a.marcador}`));
    expect(
      novos,
      "marcador novo no código: some com ele, ou acrescente à lista PENDENTES com o motivo",
    ).toEqual([]);
  });

  it("os marcadores da lista ainda existem — lista desatualizada também é defeito", () => {
    const presentes = new Set(achados.map((a) => `${a.arquivo}:${a.marcador}`));
    for (const pendente of PENDENTES) {
      expect(
        presentes.has(`${pendente.arquivo}:${pendente.marcador}`),
        `${pendente.marcador} sumiu de ${pendente.arquivo}: tire-o da lista PENDENTES`,
      ).toBe(true);
    }
  });

  it("o `[A DECIDIR]` do nome acabou — o D1 fechou", () => {
    expect(achados.some((a) => a.marcador === "[A DECIDIR]")).toBe(false);
  });
});

// --- o checklist existe e cobre os quatro itens ------------------------------------------

describe("docs/LANCAMENTO.md", () => {
  const checklist = readFileSync(resolve(raiz, "docs/LANCAMENTO.md"), "utf-8");

  it("cobre D1, D2, D6 e D7", () => {
    for (const item of ["D1", "D2", "D6", "D7"]) {
      expect(checklist).toContain(item);
    }
  });

  it("marca o que depende de conta do dono", () => {
    // 🔑 é o que separa "falta fazer" de "falta você fazer".
    expect(checklist).toContain("🔑");
  });

  it("o texto do aviso no checklist é o que o site publica", () => {
    // Um checklist que cita um aviso diferente do publicado é pior que nenhum.
    const trecho = siteConfig.riotLegalNotice.slice(0, 60);
    expect(checklist.replace(/\s+/g, " ")).toContain(trecho.replace(/\s+/g, " "));
  });
});
