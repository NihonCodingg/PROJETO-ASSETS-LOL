import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

/**
 * O critério 1 do T-34: o tema do Tailwind bate com `docs/design/TOKENS.md`
 * **valor a valor**.
 *
 * Sem este teste, o tema vira uma coleção de cinzas *parecidos* com o desenho, e
 * a diferença só aparece quando alguém põe as duas telas lado a lado. Com ele,
 * mexer num arquivo sem mexer no outro é vermelho na hora.
 *
 * A comparação é nos dois sentidos de propósito: token no CSS que não está no
 * documento é token não documentado; token no documento que não está no CSS é
 * decisão de design que ninguém implementou. Os dois são defeito.
 */

// `process.cwd()` é `apps/web` quando o vitest roda; `import.meta.url` não é
// URL de arquivo dentro do jsdom.
const raiz = resolve(process.cwd(), "../..");
const TOKENS = readFileSync(resolve(raiz, "docs/design/TOKENS.md"), "utf-8");
const CSS = readFileSync(resolve(process.cwd(), "src/app/globals.css"), "utf-8");

/** `| \`nome\` | \`#valor\` |` → { nome: valor }. Só linhas de tabela. */
function coresDoDocumento(): Map<string, string> {
  const cores = new Map<string, string>();
  for (const linha of TOKENS.split("\n")) {
    const achado = /^\|\s*`([a-z-]+)`\s*\|\s*`(#[0-9a-f]{6})`\s*\|/i.exec(linha);
    if (achado) cores.set(achado[1], achado[2].toLowerCase());
  }
  return cores;
}

/** `--color-nome: #valor;` → { nome: valor }. */
function coresDoTema(): Map<string, string> {
  const cores = new Map<string, string>();
  for (const achado of CSS.matchAll(/--color-([a-z-]+):\s*(#[0-9a-f]{6});/gi)) {
    cores.set(achado[1], achado[2].toLowerCase());
  }
  return cores;
}

const DOC = coresDoDocumento();
const TEMA = coresDoTema();

// --- critério 1: paridade -----------------------------------------------------------

describe("tokens de cor", () => {
  it("o documento e o tema declaram os mesmos nomes", () => {
    expect([...TEMA.keys()].sort()).toEqual([...DOC.keys()].sort());
  });

  it("cada nome tem o mesmo valor nos dois", () => {
    for (const [nome, valor] of TEMA) {
      expect(DOC.get(nome), `--color-${nome} divergiu do TOKENS.md`).toBe(valor);
    }
  });

  it("são 22 cores, e o número é do design, não desta suíte", () => {
    // 9 superfícies + 4 bordas + 6 textos + 3 acentos.
    expect(TEMA.size).toBe(22);
  });
});

describe("raios e tamanhos", () => {
  /** Todo `Npx` que o documento cita numa tabela de token. */
  function pixelsDoDocumento(): Set<string> {
    const valores = new Set<string>();
    for (const linha of TOKENS.split("\n")) {
      const achado = /^\|\s*`([a-z0-9-]+)`\s*\|\s*(\d+px)\s*\|/i.exec(linha);
      if (achado) valores.add(achado[2]);
    }
    return valores;
  }

  it("todo px do documento existe no tema", () => {
    const noTema = new Set([...CSS.matchAll(/:\s*(\d+px);/g)].map((m) => m[1]));
    for (const valor of pixelsDoDocumento()) {
      expect(noTema.has(valor), `${valor} está no TOKENS.md e não no tema`).toBe(true);
    }
  });

  it("o raio padrão do design é 6px", () => {
    expect(CSS).toContain("--radius-padrao: 6px;");
  });
});

// --- critério 3: uma cor de destaque ------------------------------------------------

describe("acento", () => {
  /** Matiz HSL de um hex, em graus. */
  function matiz(hex: string): number {
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    if (max === min) return 0;
    const d = max - min;
    const h =
      max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return Math.round(((h * 60) % 360) + 360) % 360;
  }

  const acentos = [...TEMA].filter(([nome]) => nome.startsWith("acento") && nome !== "acento-suave");

  it("existem três tons de acento", () => {
    expect(acentos.map(([nome]) => nome).sort()).toEqual([
      "acento",
      "acento-claro",
      "acento-mais-claro",
    ]);
  });

  it("os três são o mesmo matiz — um segundo acento faz este teste falhar", () => {
    // 10° de tolerância: a rampa de violeta do Tailwind deriva ~5° do 500 ao
    // 300, e isso é o mesmo matiz. Um acento de verdade diferente estaria a
    // dezenas de graus — um teal está a 85°, um âmbar a 220°.
    const matizes = acentos.map(([, valor]) => matiz(valor));
    for (const h of matizes) {
      expect(Math.abs(h - matizes[0]), `matiz ${h}° destoa de ${matizes[0]}°`).toBeLessThan(10);
    }
  });

  it("nenhuma outra cor do tema é saturada o bastante para virar acento", () => {
    // Cinza tem saturação ~0. Qualquer cor com saturação alta que não seja o
    // acento é um segundo acento entrando pela porta dos fundos.
    function saturacao(hex: string): number {
      const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
      const max = Math.max(r, g, b);
      const min = Math.min(r, g, b);
      const l = (max + min) / 2;
      if (max === min) return 0;
      return l > 0.5 ? (max - min) / (2 - max - min) : (max - min) / (max + min);
    }
    for (const [nome, valor] of TEMA) {
      if (nome.startsWith("acento")) continue;
      expect(saturacao(valor), `${nome} (${valor}) está saturada demais`).toBeLessThan(0.2);
    }
  });
});

// --- critério 4: contraste ------------------------------------------------------------

describe("contraste", () => {
  function canal(v: number): number {
    const x = v / 255;
    return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
  }

  function luminancia(hex: string): number {
    const [r, g, b] = [1, 3, 5].map((i) => canal(parseInt(hex.slice(i, i + 2), 16)));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  function contraste(a: string, b: string): number {
    const [la, lb] = [luminancia(a), luminancia(b)];
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
  }

  /** Os fundos sobre os quais o produto escreve texto. */
  const FUNDOS = ["fundo", "fundo-barra", "superficie", "superficie-alta", "superficie-lote", "campo"];

  /**
   * Os tokens que o T-30 pode aplicar a `color`.
   *
   * `texto-fraco` e `texto-tenue` ficam de fora por decisão de 10/09: são fiéis
   * ao design e reprovam em AA nos tamanhos em que ele os usa. Continuam no
   * tema — e o teste abaixo garante que não virem texto.
   */
  const TEXTO = ["texto", "texto-forte", "texto-medio", "texto-suave"];

  it("todo par texto × fundo passa em AA", () => {
    for (const nomeTexto of TEXTO) {
      for (const nomeFundo of FUNDOS) {
        const razao = contraste(TEMA.get(nomeTexto)!, TEMA.get(nomeFundo)!);
        expect(razao, `${nomeTexto} sobre ${nomeFundo} = ${razao.toFixed(2)}:1`).toBeGreaterThanOrEqual(4.5);
      }
    }
  });

  it("o botão primário passa: texto escuro sobre o acento", () => {
    expect(contraste(TEMA.get("superficie")!, TEMA.get("acento")!)).toBeGreaterThanOrEqual(4.5);
  });

  it("o acento passa como texto sobre o fundo", () => {
    for (const nome of ["acento", "acento-claro", "acento-mais-claro"]) {
      expect(contraste(TEMA.get(nome)!, TEMA.get("fundo")!)).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("os dois cinzas do design que reprovam continuam reprovando", () => {
    // Este teste não é redundante: ele documenta **por que** `texto-fraco` e
    // `texto-tenue` não estão na lista de cima. Se um dia alguém clarear os
    // valores no design, ele falha e obriga a revisar a decisão de 10/09.
    expect(contraste(TEMA.get("texto-fraco")!, TEMA.get("fundo")!)).toBeLessThan(4.5);
    expect(contraste(TEMA.get("texto-tenue")!, TEMA.get("fundo")!)).toBeLessThan(4.5);
  });
});
