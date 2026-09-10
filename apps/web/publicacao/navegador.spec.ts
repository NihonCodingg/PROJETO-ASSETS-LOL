import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

import { expect, test, type Locator, type Page } from "@playwright/test";

/**
 * O site servido de um domínio público, num navegador de verdade (T-43).
 *
 * O e2e do T-29 prova o comportamento com uma fixture local, e é ele que roda na
 * CI. Este arquivo prova outra coisa: que **nada quebra fora do `localhost`** —
 * CORS das fontes, caminhos, o fetch do índice, o canvas, o zip — com o índice
 * publicado e as fontes de verdade. Por isso não roda na CI; os dois modos estão
 * em `playwright.publicacao.config.ts`.
 */

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const ZIP = Buffer.from([0x50, 0x4b, 0x03, 0x04]);

/** Erro de console, exceção e requisição que falhou: CORS quebrado aparece num deles. */
function vigiarErros(page: Page): string[] {
  const erros: string[] = [];
  page.on("console", (mensagem) => {
    if (mensagem.type() === "error") erros.push(mensagem.text());
  });
  page.on("pageerror", (erro) => erros.push(erro.message));
  page.on("requestfailed", (requisicao) => {
    const motivo = requisicao.failure()?.errorText ?? "";
    // Prévia preguiçosa cancelada ao trocar de tela não é defeito.
    if (!motivo.includes("ERR_ABORTED")) erros.push(`${motivo} ${requisicao.url()}`);
  });
  return erros;
}

async function irParaHome(page: Page): Promise<void> {
  await page.goto("/");
  await expect(page.getByRole("list", { name: "Campeões" })).toBeVisible();
}

async function abrirJax(page: Page): Promise<void> {
  await irParaHome(page);
  await page
    .getByRole("list", { name: "Campeões" })
    .getByRole("button", { name: /^Jax\b/ })
    .click();
  await expect(page.getByRole("region", { name: "Painel de Jax" })).toBeVisible();
}

async function abrirEmotes(page: Page): Promise<Locator> {
  await irParaHome(page);
  await page
    .getByRole("navigation", { name: "Categorias" })
    .getByRole("button", { name: "Emotes" })
    .click();
  const cartoes = page.locator("[data-virtual='sim'] article");
  await expect(cartoes.first()).toBeVisible();
  return cartoes;
}

async function baixar(page: Page, botao: Locator): Promise<{ nome: string; dados: Buffer }> {
  const download = page.waitForEvent("download");
  await botao.click();
  const arquivo = await download;
  return { nome: arquivo.suggestedFilename(), dados: await readFile(await arquivo.path()) };
}

interface Registro {
  readonly sha256?: string;
  readonly bytes: number;
  readonly width: number;
  readonly height: number;
  readonly source: string;
}

/**
 * O registro de um arquivo no índice, lido **pela página**.
 *
 * Pela página porque é ela que resolve o domínio: no modo local, o nome
 * `biblioteca-de-assets.test` só existe dentro do Chromium.
 */
async function registro(page: Page, categoria: string, arquivo: string): Promise<Registro> {
  const achado = await page.evaluate(
    async ([categoria, arquivo]) => {
      const manifesto = await (await fetch("/indice/manifest.json")).json();
      const versao = manifesto.versions.find(
        (v: { gameVersion: string }) => v.gameVersion === manifesto.currentVersion,
      );
      const fatia = versao.shards.find((s: { category: string }) => s.category === categoria);
      const { assets } = await (await fetch(`/indice/${fatia.url}`)).json();
      const asset = assets.find((a: { fileName: string }) => a.fileName === arquivo);
      return asset
        ? {
            sha256: asset.sha256,
            bytes: asset.bytes,
            width: asset.width,
            height: asset.height,
            source: asset.source,
          }
        : null;
    },
    [categoria, arquivo] as const,
  );
  expect(achado, `${arquivo} não está na fatia ${categoria}`).not.toBeNull();
  return achado as Registro;
}

/** Os bytes salvos são os da fonte: pelo sha256 do índice, ou pelo tamanho se ele não mediu. */
function conferirBytes(dados: Buffer, esperado: Registro): void {
  if (esperado.sha256) {
    expect(createHash("sha256").update(dados).digest("hex")).toBe(esperado.sha256);
  } else {
    expect(dados.length).toBe(esperado.bytes);
  }
}

test("é servido de um domínio que não é localhost", async ({ page }) => {
  await irParaHome(page);
  expect(["localhost", "127.0.0.1", "[::1]"]).not.toContain(new URL(page.url()).hostname);
});

test("no ar, é HTTPS e contexto seguro", async ({ page }) => {
  // O modo local é HTTP num domínio falso: **não** é contexto seguro, e o
  // Chromium sem janela ignora a flag que o fingiria. Que os cenários de
  // download, PNG e zip passem assim prova que eles não dependem disso. Quem
  // depende é o "Copiar URL", e ele só precisa do HTTPS que a Vercel já dá.
  test.skip(!process.env.URL_PUBLICADA, "só contra o site no ar");
  await irParaHome(page);
  expect(new URL(page.url()).protocol).toBe("https:");
  expect(await page.evaluate(() => window.isSecureContext)).toBe(true);
});

test("o índice vem do próprio domínio — nenhum CORS no caminho", async ({ page }) => {
  const erros = vigiarErros(page);
  const doIndice: string[] = [];
  page.on("request", (requisicao) => {
    if (requisicao.url().includes("/indice/")) doIndice.push(requisicao.url());
  });
  await irParaHome(page);

  const origem = new URL(page.url()).origin;
  expect(doIndice.some((url) => url.endsWith("/indice/manifest.json"))).toBe(true);
  for (const url of doIndice) expect(new URL(url).origin).toBe(origem);
  expect(erros).toEqual([]);
});

test("as miniaturas carregam das fontes", async ({ page }) => {
  const erros = vigiarErros(page);
  await irParaHome(page);
  await expect
    .poll(() =>
      page.evaluate(() => {
        const imagens = [
          ...document.querySelectorAll<HTMLImageElement>('ul[aria-label="Campeões"] img'),
        ].slice(0, 8);
        return imagens.length === 8 && imagens.every((i) => i.complete && i.naturalWidth > 0);
      }),
    )
    .toBe(true);
  expect(erros).toEqual([]);
});

test("baixar do ddragon traz os bytes que o índice descreve", async ({ page }) => {
  const erros = vigiarErros(page);
  await abrirJax(page);
  const esperado = await registro(page, "champion", "Jax_square.png");
  expect(esperado.source).toBe("ddragon");

  const cartao = page.locator('article[aria-label="Jax_square.png"]');
  const { nome, dados } = await baixar(page, cartao.getByRole("button", { name: "Baixar original" }));

  expect(nome).toBe("Jax_square.png");
  expect(dados.subarray(0, 8)).toEqual(PNG);
  conferirBytes(dados, esperado);
  expect(erros).toEqual([]);
});

test("converter a splash para PNG: o canvas não fica contaminado", async ({ page }) => {
  const erros = vigiarErros(page);
  await abrirJax(page);
  const esperado = await registro(page, "champion", "Jax_000_splash_centered.jpg");

  const cartao = page.locator('article[aria-label="Jax_000_splash_centered.jpg"]');
  const { nome, dados } = await baixar(page, cartao.getByRole("button", { name: "Baixar PNG" }));

  expect(nome).toBe("Jax_000_splash_centered.png");
  expect(dados.subarray(0, 8)).toEqual(PNG);
  // IHDR: o PNG gerado no navegador tem as dimensões do JPEG da fonte.
  expect({ largura: dados.readUInt32BE(16), altura: dados.readUInt32BE(20) }).toEqual({
    largura: esperado.width,
    altura: esperado.height,
  });
  expect(erros).toEqual([]);
});

test("baixar do cdragon traz os bytes que o índice descreve", async ({ page }) => {
  const erros = vigiarErros(page);
  const cartoes = await abrirEmotes(page);
  const cartao = cartoes.filter({ hasText: "cdragon" }).first();
  const arquivo = (await cartao.getAttribute("aria-label")) ?? "";
  const esperado = await registro(page, "emote", arquivo);
  expect(esperado.source).toBe("cdragon");

  const { nome, dados } = await baixar(page, cartao.getByRole("button", { name: "Baixar original" }));
  expect(nome).toBe(arquivo);
  conferirBytes(dados, esperado);
  expect(erros).toEqual([]);
});

test("o zip em lote junta arquivos das fontes no navegador", async ({ page }) => {
  const erros = vigiarErros(page);
  const cartoes = await abrirEmotes(page);
  // O rótulo envolve a caixa de seleção; o `input` é `sr-only`.
  await cartoes.nth(0).locator("label").click();
  await cartoes.nth(1).locator("label").click();

  const lote = page.locator('[aria-label="Seleção"]');
  const { nome, dados } = await baixar(page, lote.getByRole("button", { name: /como zip/ }));
  expect(nome).toMatch(/\.zip$/);
  expect(dados.subarray(0, 4)).toEqual(ZIP);
  expect(erros).toEqual([]);
});

test("os dois avisos da Riot, no rodapé e na página Sobre", async ({ page }) => {
  await irParaHome(page);
  for (const qual of ["riot", "jibber-jabber"]) {
    await expect(page.locator(`aside [data-aviso='${qual}']`)).toBeVisible();
  }
  await page.goto("/sobre");
  for (const qual of ["riot", "jibber-jabber"]) {
    await expect(page.locator(`main [data-aviso='${qual}']`)).toBeVisible();
  }
});
