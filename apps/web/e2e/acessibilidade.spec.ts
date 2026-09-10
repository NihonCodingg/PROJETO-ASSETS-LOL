import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/**
 * Acessibilidade (T-28, RNF-11): teclado, `alt` e o que o axe pega sozinho.
 *
 * O axe cobre o que dá para automatizar — contraste, rótulo, papel, ordem de
 * cabeçalho — e **não** cobre o que importa mais aqui: se dá para completar o
 * J1 inteiro sem tocar no mouse. Por isso os dois tipos de teste convivem neste
 * arquivo, e o percurso por teclado vem primeiro.
 *
 * O contraste é o único critério que este ticket **não** fecha: a paleta chega
 * com o design (T-30). O que fica pronto aqui é a verificação, para que o design
 * chegue já sob ela.
 */

/** Sério e crítico falham; moderado e leve viram aviso no relatório. */
const GRAVES = ["critical", "serious"];

async function violacoesGraves(page: Page) {
  const resultado = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();

  // Sem isto, um axe que não rodou (seletor errado, página em branco, script que
  // não injetou) devolveria zero violações e o teste passaria feliz provando
  // nada. Uma página com conteúdo sempre tem dezenas de regras aprovadas.
  expect(resultado.passes.length, "o axe não analisou nada").toBeGreaterThan(5);

  return resultado.violations.filter((v) => GRAVES.includes(v.impact ?? ""));
}

function resumir(violacoes: Awaited<ReturnType<typeof violacoesGraves>>): string {
  return violacoes
    .map((v) => `${v.impact}/${v.id}: ${v.help} (${v.nodes.length}x)\n  ${v.nodes[0]?.html ?? ""}`)
    .join("\n");
}

async function irParaHome(page: Page): Promise<void> {
  await page.goto("/");
  await expect(page.getByRole("list", { name: "Campeões" })).toBeVisible();
}

// --- critério 1: o J1 inteiro só com teclado -------------------------------------------

test.describe("só com teclado", () => {
  test("J1 completo: do carregamento ao arquivo salvo, sem mouse", async ({ page }) => {
    await irParaHome(page);

    // O RF-01 põe o foco na busca ao carregar; digitar já é o primeiro passo.
    await page.keyboard.type("jax");
    await expect(page.getByRole("option").first()).toBeVisible();

    // Enter no resultado abre o painel do campeão.
    await page.keyboard.press("Enter");
    await expect(page.getByRole("region", { name: "Painel de Jax" })).toBeVisible();

    // Tab até o botão de baixar do square, e Enter.
    const baixar = page
      .locator('article[aria-label="Jax_square.png"]')
      .getByRole("button", { name: "Baixar original" });
    await expect(baixar).toBeVisible();

    const download = page.waitForEvent("download");
    await baixar.focus();
    await page.keyboard.press("Enter");

    expect((await download).suggestedFilename()).toBe("Jax_square.png");
  });

  test("todo controle do painel é alcançável por Tab", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    await expect(page.getByRole("region", { name: "Painel de Jax" })).toBeVisible();

    // Percorre a ordem de foco e coleta o que ela alcança. 120 tabulações é
    // muito mais que o painel tem: o teste falharia por armadilha de foco antes.
    const alcancados = new Set<string>();
    await page.locator("body").click({ position: { x: 1, y: 1 } });
    for (let i = 0; i < 120; i += 1) {
      await page.keyboard.press("Tab");
      const marca = await page.evaluate(() => {
        const foco = document.activeElement as HTMLElement | null;
        if (!foco || foco === document.body) return "";
        return `${foco.tagName}:${foco.getAttribute("aria-label") ?? foco.textContent?.trim().slice(0, 40) ?? ""}`;
      });
      if (marca) alcancados.add(marca);
    }

    expect([...alcancados].some((m) => m.includes("Baixar original"))).toBe(true);
    expect([...alcancados].some((m) => m.includes("Selecionar skin"))).toBe(true);
    expect([...alcancados].some((m) => m.includes("fechar"))).toBe(true);
  });

  test("Escape fecha o painel, como manda o padrão", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    await expect(page.getByRole("region", { name: "Painel de Jax" })).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(page.getByRole("region", { name: "Painel de Jax" })).toBeHidden();
  });

  test("Escape funciona antes de a fatia chegar", async ({ page }) => {
    // O painel aparece antes dos assets. Um ouvinte que só existe depois deles
    // deixaria `Escape` sem efeito exatamente durante a espera — que é quando
    // alguém mais desiste.
    await irParaHome(page);
    await page.route("**/index-champion-e2e.json", async (rota) => {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await rota.continue();
    });

    await page.click('button:has-text("Jax")');
    await expect(page.getByText("carregando os assets…")).toBeVisible();
    await page.keyboard.press("Escape");

    await expect(page.getByRole("region", { name: "Painel de Jax" })).toBeHidden();
  });

  test("com chromas abertos, Escape fecha os chromas primeiro", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    const mostrar = page.getByRole("button", { name: /Mostrar 2 chromas/ });
    await expect(mostrar).toBeVisible();
    await mostrar.click();
    await expect(page.getByRole("region", { name: /^Chromas de/ })).toBeVisible();

    // O de dentro primeiro, como todo mundo espera de Escape.
    await page.keyboard.press("Escape");
    await expect(page.getByRole("region", { name: /^Chromas de/ })).toBeHidden();
    await expect(page.getByRole("region", { name: "Painel de Jax" })).toBeVisible();

    // E o segundo fecha o painel.
    await page.keyboard.press("Escape");
    await expect(page.getByRole("region", { name: "Painel de Jax" })).toBeHidden();
  });

  test("a barra `/` foca a busca sem escrever o caractere (RF-07)", async ({ page }) => {
    await irParaHome(page);
    const campo = page.getByRole("combobox");
    await page.locator("body").click({ position: { x: 1, y: 1 } });
    await page.keyboard.press("/");

    await expect(campo).toBeFocused();
    await expect(campo).toHaveValue("");
  });
});

// --- critério 3: `alt` em toda imagem ---------------------------------------------------

test.describe("texto alternativo", () => {
  test("toda imagem da grade tem alt com o nome do campeão", async ({ page }) => {
    await irParaHome(page);
    const alts = await page.locator('ul[aria-label="Campeões"] img').evaluateAll((imgs) =>
      imgs.map((img) => (img as HTMLImageElement).alt),
    );

    expect(alts.length).toBeGreaterThan(0);
    for (const alt of alts) expect(alt.trim().length).toBeGreaterThan(0);
    expect(alts).toContain("Jax");
  });

  test("toda prévia do painel tem alt com o nome do asset", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    // `evaluateAll` não espera: sem isto o teste lê a lista antes de a fatia
    // chegar e passa com zero imagens, provando nada.
    await expect(page.locator("img[data-previa]").first()).toBeVisible();

    const alts = await page
      .locator("img[data-previa]")
      .evaluateAll((imgs) => imgs.map((img) => (img as HTMLImageElement).alt));

    expect(alts.length).toBeGreaterThan(0);
    for (const alt of alts) expect(alt).toMatch(/^Prévia de .+/);
  });

  test("nenhuma imagem da página fica sem alt", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    await expect(page.locator("img[data-previa]").first()).toBeVisible();

    const semAlt = await page
      .locator("img")
      .evaluateAll((imgs) =>
        imgs.filter((img) => !(img as HTMLImageElement).alt.trim()).map((img) => img.outerHTML),
      );

    expect(semAlt).toEqual([]);
  });
});

// --- critério 4: o foco aparece -----------------------------------------------------------

test.describe("foco visível", () => {
  test("o navegador desenha o anel de foco em todo controle", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    await expect(page.locator("img[data-previa]").first()).toBeVisible();

    // `outline: none` sem substituto é o jeito clássico de tornar um site
    // inutilizável por teclado sem que ninguém perceba. Nenhum controle da tela
    // pode fazer isso.
    const semAnel = await page.evaluate(() => {
      const controles = [...document.querySelectorAll("button, a[href], input, select")];
      return controles
        .filter((elemento) => {
          const estilo = getComputedStyle(elemento, ":focus-visible");
          const semOutline = estilo.outlineStyle === "none" || estilo.outlineWidth === "0px";
          const semSombra = estilo.boxShadow === "none";
          return semOutline && semSombra;
        })
        .map((elemento) => elemento.outerHTML.slice(0, 80));
    });

    expect(semAnel).toEqual([]);
  });
});

// --- critério 2: o axe -------------------------------------------------------------------

test.describe("axe", () => {
  test("a home não tem violação séria nem crítica", async ({ page }) => {
    await irParaHome(page);
    const violacoes = await violacoesGraves(page);
    expect(resumir(violacoes)).toBe("");
  });

  test("o painel do campeão não tem violação séria nem crítica", async ({ page }) => {
    await irParaHome(page);
    await page.click('button:has-text("Jax")');
    await expect(page.getByRole("region", { name: "Painel de Jax" })).toBeVisible();

    const violacoes = await violacoesGraves(page);
    expect(resumir(violacoes)).toBe("");
  });

  test("a navegação por categoria não tem violação séria nem crítica", async ({ page }) => {
    await irParaHome(page);
    await page
      .getByRole("navigation", { name: "Categorias" })
      .getByRole("button", { name: "Itens" })
      .click();
    // Grupos de filtro, caixas de seleção e a lista: é a tela com mais controles
    // do produto, e por isso a mais fácil de quebrar sem perceber.
    await expect(page.getByRole("group", { name: "Mapa" })).toBeVisible();

    const violacoes = await violacoesGraves(page);
    expect(resumir(violacoes)).toBe("");
  });

  test("a página Sobre não tem violação séria nem crítica", async ({ page }) => {
    await page.goto("/sobre");
    await expect(page.getByRole("heading", { name: "Sobre", level: 1 })).toBeVisible();

    const violacoes = await violacoesGraves(page);
    expect(resumir(violacoes)).toBe("");
  });
});

// --- critério 3 do T-30: telas estreitas ------------------------------------------------

test.describe("tela estreita", () => {
  test.use({ viewport: { width: 375, height: 720 } });

  test("nada transborda na horizontal", async ({ page }) => {
    await irParaHome(page);
    // Rolagem horizontal numa grade de cartões é o sintoma clássico de largura
    // fixa que não coube. 375px é um telefone comum.
    const transborda = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    );
    expect(transborda).toBe(false);
  });

  test("os dois avisos da Riot continuam inteiros (RF-21)", async ({ page }) => {
    await irParaHome(page);
    for (const qual of ["riot", "jibber-jabber"]) {
      const aviso = page.locator(`[data-aviso='${qual}']`);
      await expect(aviso).toBeVisible();
      // Sem corte: o texto renderizado tem que ser o texto todo.
      const cortado = await aviso.evaluate((el) => el.scrollHeight > el.clientHeight + 1);
      expect(cortado, `o aviso ${qual} foi cortado`).toBe(false);
    }
  });

  test("a grade e a busca continuam utilizáveis", async ({ page }) => {
    await irParaHome(page);
    await expect(page.getByRole("combobox")).toBeVisible();
    await expect(page.getByRole("list", { name: "Campeões" })).toBeVisible();
    const largura = await page
      .getByRole("list", { name: "Campeões" })
      .evaluate((el) => el.getBoundingClientRect().width);
    expect(largura).toBeGreaterThan(300);
  });

  test("a categoria aberta também cabe na tela", async ({ page }) => {
    // Os outros cenários estreitos olham a home. Este olha a categoria, que é
    // onde a barra lateral vira faixa **e** a lista virtual entra: as duas
    // coisas que já transbordaram.
    await irParaHome(page);
    await page
      .getByRole("navigation", { name: "Categorias" })
      .getByRole("button", { name: "Itens" })
      .click();
    await expect(page.locator("[data-virtual='sim'] article").first()).toBeVisible();

    const medidas = await page.evaluate(() => {
      const doc = document.documentElement;
      const caixas = [...document.querySelectorAll("[data-virtual='sim'] article")].map((a) =>
        a.getBoundingClientRect(),
      );
      return {
        transborda: doc.scrollWidth > doc.clientWidth + 1,
        sobrepoe: caixas.slice(1).some((caixa, i) => caixa.top < caixas[i].bottom - 1),
      };
    });
    expect(medidas.transborda, "a categoria transbordou na horizontal").toBe(false);
    expect(medidas.sobrepoe, "um cartão está por cima do outro").toBe(false);
  });

  test("o axe não reclama em tela estreita", async ({ page }) => {
    await irParaHome(page);
    expect(resumir(await violacoesGraves(page))).toBe("");
  });
});
