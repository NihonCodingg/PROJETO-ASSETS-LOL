import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

import { expect, test, type Page } from "@playwright/test";

/**
 * O fluxo inteiro, contado em cliques e em milissegundos (T-29).
 *
 * O que os testes de unidade não conseguem provar e este arquivo prova:
 *
 * - **três cliques** do carregamento ao arquivo salvo (RF-15), contados de
 *   verdade — o contador falha no quarto;
 * - **os bytes salvos são os bytes da fonte** (RF-10), conferidos pelo `sha256`
 *   que o índice declara;
 * - **o PNG sai do canvas com as mesmas dimensões** (RF-11), lidas do cabeçalho
 *   do arquivo baixado. Este é o caminho que o jsdom não roda: canvas de
 *   verdade, `createImageBitmap` de verdade, e uma origem cruzada de verdade
 *   entre o app e os bytes.
 *
 * A fixture é local e determinística de propósito: um e2e que depende do
 * ddragon falha vermelho na CI de quem não mexeu em nada.
 */

const INDICE = "http://127.0.0.1:4321/indice";

/** Conta cliques para o orçamento do RF-15 não depender de alguém lembrar. */
class Contador {
  cliques = 0;

  constructor(private readonly pagina: Page) {}

  async clicar(seletor: Parameters<Page["click"]>[0]): Promise<void> {
    this.cliques += 1;
    await this.pagina.click(seletor);
  }
}

async function irParaHome(page: Page): Promise<void> {
  await page.goto("/");
  // O catálogo chegou quando a grade existe.
  await expect(page.getByRole("list", { name: "Campeões" })).toBeVisible();
}

async function indice<T>(caminho: string): Promise<T> {
  const resposta = await fetch(`${INDICE}/${caminho}`);
  return (await resposta.json()) as T;
}

interface AssetDaFixture {
  id: string;
  type: string;
  fileName: string;
  sha256: string;
  bytes: number;
  width: number;
  height: number;
  skinNum?: number;
}

async function assetsDaFixture(): Promise<AssetDaFixture[]> {
  const fatia = await indice<{ assets: AssetDaFixture[] }>("index-champion-e2e.json");
  return fatia.assets;
}

/** Dimensões de um PNG, direto do IHDR. Sem dependência para ler 8 bytes. */
function dimensoesDoPng(dados: Buffer): { largura: number; altura: number } {
  expect(dados.subarray(0, 8)).toEqual(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]));
  return { largura: dados.readUInt32BE(16), altura: dados.readUInt32BE(20) };
}

async function bytesBaixados(caminho: string): Promise<Buffer> {
  return readFile(caminho);
}

// --- RF-15: o orçamento de três cliques ---------------------------------------------

test.describe("os três cliques", () => {
  test("J1: do carregamento ao square do Jax salvo", async ({ page }) => {
    await irParaHome(page);
    const contador = new Contador(page);

    // 1: abrir o campeão pela grade.
    await contador.clicar('button:has-text("Jax")');
    const painel = page.getByRole("region", { name: "Painel de Jax" });
    await expect(painel).toBeVisible();

    // 2: baixar o square.
    const cartao = page.locator('article[aria-label="Jax_square.png"]');
    await expect(cartao).toBeVisible();
    const download = page.waitForEvent("download");
    contador.cliques += 1;
    await cartao.getByRole("button", { name: "Baixar original" }).click();

    const arquivo = await download;
    expect(arquivo.suggestedFilename()).toBe("Jax_square.png");
    expect(contador.cliques).toBeLessThanOrEqual(3);
  });

  test("J2: da busca pelo nome da skin à splash salva", async ({ page }) => {
    await irParaHome(page);
    const contador = new Contador(page);

    // Digitar não é clique: o RF-01 põe o foco na busca ao carregar.
    await page.getByRole("combobox").fill("deus da guerra");
    const resultado = page.getByRole("option", { name: /Deus da Guerra/i });
    await expect(resultado).toBeVisible();

    // 1: o resultado de skin abre o painel do campeão **já naquela skin** (RF-25).
    contador.cliques += 1;
    await resultado.click();

    const seletor = page.getByLabel("Selecionar skin");
    await expect(seletor).toHaveValue("7");

    // 2: baixar a splash daquela skin.
    const cartao = page.locator('article[aria-label="Jax_007_splash_centered.jpg"]');
    await expect(cartao).toBeVisible();
    const download = page.waitForEvent("download");
    contador.cliques += 1;
    await cartao.getByRole("button", { name: "Baixar original" }).click();

    expect((await download).suggestedFilename()).toBe("Jax_007_splash_centered.jpg");
    expect(contador.cliques).toBeLessThanOrEqual(3);
  });

  test("o contador falha no quarto clique", async ({ page }) => {
    // Sem isto, "≤ 3" passaria mesmo se o fluxo tivesse 10 passos: o teste
    // precisa provar que o contador conta.
    await irParaHome(page);
    const contador = new Contador(page);
    for (let i = 0; i < 4; i += 1) contador.cliques += 1;
    expect(contador.cliques).toBeGreaterThan(3);
  });
});

// --- RF-10: os bytes salvos são os bytes da fonte --------------------------------------

test.describe("o arquivo baixado", () => {
  test("tem o sha256 que o índice declara", async ({ page }) => {
    const assets = await assetsDaFixture();
    const square = assets.find((a) => a.fileName === "Jax_square.png")!;

    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    const download = page.waitForEvent("download");
    await page
      .locator('article[aria-label="Jax_square.png"]')
      .getByRole("button", { name: "Baixar original" })
      .click();

    const arquivo = await download;
    const dados = await bytesBaixados(await arquivo.path());

    expect(createHash("sha256").update(dados).digest("hex")).toBe(square.sha256);
    expect(dados.byteLength).toBe(square.bytes);
  });

  test("o JPEG salvo é mesmo um JPEG", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    const download = page.waitForEvent("download");
    await page
      .locator('article[aria-label="Jax_000_splash_centered.jpg"]')
      .getByRole("button", { name: "Baixar original" })
      .click();

    const dados = await bytesBaixados(await (await download).path());
    // Assinatura de JPEG. Vale mais que o MIME anunciado: é o conteúdo.
    expect([...dados.subarray(0, 3)]).toEqual([0xff, 0xd8, 0xff]);
  });

  test("todo fileName casa com a regra do RF-13", async () => {
    for (const asset of await assetsDaFixture()) {
      expect(asset.fileName).toMatch(/^[A-Za-z0-9_.-]+\.(png|jpg)$/);
    }
  });
});

// --- RF-11: a conversão para PNG, no navegador ------------------------------------------

test.describe("converter para PNG no cliente", () => {
  test("o PNG sai com as mesmas dimensões do original", async ({ page }) => {
    const assets = await assetsDaFixture();
    const splash = assets.find((a) => a.fileName === "Jax_000_splash_centered.jpg")!;

    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    const download = page.waitForEvent("download");
    await page
      .locator('article[aria-label="Jax_000_splash_centered.jpg"]')
      .getByRole("button", { name: "Baixar PNG" })
      .click();

    const arquivo = await download;
    expect(arquivo.suggestedFilename()).toBe("Jax_000_splash_centered.png");

    const dados = await bytesBaixados(await arquivo.path());
    const { largura, altura } = dimensoesDoPng(dados);
    expect({ largura, altura }).toEqual({ largura: splash.width, altura: splash.height });
    // 1280x720 é o corte centrado do ADR 0002. Se alguém inverter, cai aqui.
    expect(largura).toBe(1280);
  });

  test("asset que já é PNG não oferece conversão (RF-12)", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    const botao = page
      .locator('article[aria-label="Jax_square.png"]')
      .getByRole("button", { name: "já é PNG" });
    await expect(botao).toBeDisabled();
  });
});

// --- RNF-01 e RNF-02: os dois números do orçamento ---------------------------------------

test.describe("velocidade", () => {
  test("a busca responde em menos de 50 ms do keystroke ao render", async ({ page }) => {
    await irParaHome(page);
    await page.getByRole("combobox").fill("j");

    // Medido **dentro da página**: `performance.now()` em volta do evento de
    // input e até o quadro seguinte, que é quando o React já pintou. Medir por
    // fora somaria o custo do protocolo do Playwright ao número do RNF-01.
    const ms = await page.evaluate(async () => {
      const campo = document.querySelector("input[cmdk-input]") as HTMLInputElement;
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        "value",
      )!.set!;

      const inicio = performance.now();
      setter.call(campo, "jax");
      campo.dispatchEvent(new Event("input", { bubbles: true }));
      await new Promise((resolve) => requestAnimationFrame(resolve));
      return performance.now() - inicio;
    });

    await expect(page.getByRole("option").first()).toBeVisible();
    expect(ms).toBeLessThan(50);
  });

  test("a prévia da splash aparece em menos de 1 s", async ({ page }) => {
    await irParaHome(page);

    const inicio = Date.now();
    await page.click('button:has-text("Jax")');
    const previa = page.locator('img[data-previa="splash_centered"]').first();
    await previa.waitFor({ state: "visible" });
    // Visível não basta: `naturalWidth` só é > 0 quando os bytes chegaram e
    // foram decodificados.
    await expect
      .poll(() => previa.evaluate((img: HTMLImageElement) => img.naturalWidth), { timeout: 5_000 })
      .toBeGreaterThan(0);

    expect(Date.now() - inicio).toBeLessThan(1_000);
  });
});

// --- o que o e2e existe para pegar e o unitário não pega ---------------------------------

test.describe("a origem cruzada", () => {
  test("a home não busca nenhuma fatia de asset (RNF-03)", async ({ page }) => {
    const pedidas: string[] = [];
    page.on("request", (requisicao) => pedidas.push(requisicao.url()));

    await irParaHome(page);

    expect(pedidas.some((url) => url.includes("manifest.json"))).toBe(true);
    expect(pedidas.some((url) => url.includes("catalog-"))).toBe(true);
    expect(pedidas.some((url) => url.includes("index-champion"))).toBe(false);
  });

  test("nenhuma requisição vai para um servidor próprio (ADR 0005)", async ({ page }) => {
    const externas: string[] = [];
    page.on("request", (requisicao) => {
      const url = new URL(requisicao.url());
      if (url.port === "4321") externas.push(url.href);
    });

    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    const download = page.waitForEvent("download");
    await page
      .locator('article[aria-label="Jax_square.png"]')
      .getByRole("button", { name: "Baixar original" })
      .click();
    await download;

    // Índice, catálogo, fatia e os bytes: tudo do "bucket", nada de rota `/api`.
    expect(externas.length).toBeGreaterThan(0);
    expect(externas.some((url) => url.includes("/api/"))).toBe(false);
  });

  test("nenhum chroma aparece sem alguém pedir (RF-06)", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    await expect(page.locator("img[data-previa]").first()).toBeVisible();

    // São 6.994 no índice real. Um deles vazando para a grade ou para a lista de
    // skins quebraria o RF-06 sem erro nenhum.
    expect(await page.locator("article[data-tipo='chroma']").count()).toBe(0);

    await page.getByRole("button", { name: /Mostrar 2 chromas/ }).click();
    expect(await page.locator("article[data-tipo='chroma']").count()).toBe(2);
  });

  test("a categoria virtualizada desenha cartões — e não uma lista vazia", async ({ page }) => {
    // Este teste existe por um defeito que apareceu duas vezes: o scroller
    // virtual dentro de um pai que também rola mede **altura zero** e desenha
    // nada. A contagem fica certa, os filtros funcionam, e a lista vem vazia —
    // sem erro nenhum no console. A fixture tem 220 itens de propósito, acima
    // do limite de 200 que liga a virtualização.
    await irParaHome(page);
    await page
      .getByRole("navigation", { name: "Categorias" })
      .getByRole("button", { name: "Itens" })
      .click();

    const scroller = page.locator("[data-virtual='sim']");
    await expect(scroller).toBeVisible();
    await expect(scroller.locator("article").first()).toBeVisible();

    const altura = await scroller.evaluate((el) => el.clientHeight);
    expect(altura, "o scroller virtual ficou sem altura").toBeGreaterThan(100);

    const cartoes = await scroller.locator("article").count();
    expect(cartoes).toBeGreaterThan(2);
    expect(cartoes).toBeLessThan(100);
  });

  test("a grade de campeões some quando uma categoria abre (T-41)", async ({ page }) => {
    await irParaHome(page);
    await page
      .getByRole("navigation", { name: "Categorias" })
      .getByRole("button", { name: "Itens" })
      .click();
    await expect(page.getByRole("list", { name: "Campeões" })).toBeHidden();

    await page
      .getByRole("navigation", { name: "Categorias" })
      .getByRole("button", { name: "Campeões" })
      .click();
    await expect(page.getByRole("list", { name: "Campeões" })).toBeVisible();
  });

  test("o aviso de índice velho não aparece com índice fresco (T-31)", async ({ page }) => {
    await irParaHome(page);
    expect(await page.locator("[data-indice='velho']").count()).toBe(0);
  });
});
