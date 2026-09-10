import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import {
  CACHE_IMUTAVEL,
  CACHE_REVALIDAR,
  NOME_COM_HASH,
  NOME_FIXO,
  SEM_INDEXACAO,
  cabecalhosDoSite,
} from "./cabecalhos";

/**
 * T-42 — o que a Vercel lê e o que o site responde ([ADR 0016]).
 *
 * O deploy em si não roda em teste: é conta do dono. O que dá para afirmar
 * daqui é que a configuração que ele vai usar está certa — e que ela continua
 * certa quando alguém mexe no pnpm, no indexador ou nos cabeçalhos.
 */

const web = process.cwd();
const raiz = resolve(web, "../..");
const indice = resolve(web, "public/indice");

function json(caminho: string) {
  return JSON.parse(readFileSync(caminho, "utf-8"));
}

// --- vercel.json ----------------------------------------------------------------------

describe("vercel.json", () => {
  const vercel = json(resolve(web, "vercel.json"));
  const pnpm: string = json(resolve(raiz, "package.json")).packageManager;

  it("declara o framework, para a Vercel não ter que adivinhar", () => {
    expect(vercel.framework).toBe("nextjs");
  });

  it("instala e builda com o pnpm do packageManager — a Vercel só conhece até o 10", () => {
    // O `allowBuilds` do pnpm-workspace.yaml é sintaxe do pnpm 11. Com o pnpm
    // que a Vercel escolheria sozinha, ele seria ignorado em silêncio.
    expect(pnpm).toMatch(/^pnpm@11\./);
    expect(vercel.installCommand).toBe(`npx --yes ${pnpm} install --frozen-lockfile`);
    expect(vercel.buildCommand).toBe(`npx --yes ${pnpm} run build`);
  });

  it("não carrega variável de ambiente nem segredo", () => {
    // Nenhuma variável é obrigatória; as opcionais moram no painel.
    expect(vercel.env).toBeUndefined();
    expect(vercel.build).toBeUndefined();
  });
});

// --- cabeçalhos -----------------------------------------------------------------------

describe("cache do índice", () => {
  const arquivos = readdirSync(indice);
  const comHash = new RegExp(`^${NOME_COM_HASH}$`);
  const fixo = new RegExp(`^${NOME_FIXO}$`);

  it("todo arquivo publicado cai em exatamente uma regra", () => {
    expect(arquivos.length).toBeGreaterThan(2);
    for (const arquivo of arquivos) {
      expect([comHash.test(arquivo), fixo.test(arquivo)].filter(Boolean), arquivo).toHaveLength(1);
    }
  });

  it("o hash do nome é o do conteúdo — senão, imutável seria mentira", () => {
    for (const arquivo of arquivos.filter((a) => comHash.test(a))) {
      const noNome = arquivo.match(/-([0-9a-f]+)\.json$/)?.[1] ?? "";
      const doConteudo = createHash("sha256")
        .update(readFileSync(resolve(indice, arquivo)))
        .digest("hex");
      expect(doConteudo.startsWith(noNome), arquivo).toBe(true);
    }
  });

  it("com hash é imutável; nome fixo revalida", () => {
    const [imutaveis, revalidados] = cabecalhosDoSite({ indexavel: true });
    expect(imutaveis.source).toContain(NOME_COM_HASH);
    expect(imutaveis.headers).toEqual([{ key: "Cache-Control", value: CACHE_IMUTAVEL }]);
    expect(revalidados.source).toContain(NOME_FIXO);
    expect(revalidados.headers).toEqual([{ key: "Cache-Control", value: CACHE_REVALIDAR }]);
  });

  it("o manifesto não tem stale-while-revalidate — na Vercel ele apontaria para 404", () => {
    expect(CACHE_REVALIDAR).not.toContain("stale-while-revalidate");
    expect(CACHE_REVALIDAR).toContain("max-age=0");
  });
});

describe("divulgação", () => {
  it("sem divulgação, toda resposta leva noindex", () => {
    const regra = cabecalhosDoSite({ indexavel: false }).find((r) =>
      r.headers.some((h) => h.key === "X-Robots-Tag"),
    );
    expect(regra?.source).toBe("/:caminho*");
    expect(regra?.headers).toEqual([{ key: "X-Robots-Tag", value: SEM_INDEXACAO }]);
  });

  it("indexável, nenhuma resposta leva noindex", () => {
    const regras = cabecalhosDoSite({ indexavel: true });
    expect(regras.flatMap((r) => r.headers).some((h) => h.key === "X-Robots-Tag")).toBe(false);
  });
});
