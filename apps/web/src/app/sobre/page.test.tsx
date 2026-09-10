import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { AssetSource } from "@lol-assets/schema";

import { Rodape } from "@/components/rodape";
import { CREDITOS, creditosVisiveis } from "@/lib/creditos";
import { siteConfig } from "@/lib/site-config";

import SobrePage, { metadata } from "./page";

/**
 * A obrigação legal (RF-21, RF-22, RF-23, RNF-10).
 *
 * Estes testes não são sobre texto bonito: são sobre a única parte do produto
 * cujo erro não é bug, é problema com a Riot ou com a Weird Gloop. O caso
 * perigoso é o crédito à wiki aparecer **antes** do consentimento — creditar
 * quem pediu, nos termos, para não ser usado automatizadamente é pior do que
 * não creditar.
 */

afterEach(cleanup);

/** As fontes do contrato. Se o schema ganhar uma, esta lista tem que ganhar junto. */
const FONTES_DO_CONTRATO: AssetSource[] = ["ddragon", "cdragon", "riot_static", "wiki"];

// --- RF-21: o aviso em toda página ------------------------------------------------------

describe("aviso legal da Riot", () => {
  it("está no rodapé, que é por onde toda página passa", () => {
    const { container } = render(<Rodape />);
    expect(container.querySelector("[data-aviso='riot']")?.textContent).toBe(
      siteConfig.riotLegalNotice,
    );
  });

  it("o texto tem as duas frases que a política exige", () => {
    expect(siteConfig.riotLegalNotice).toContain("isn't endorsed by Riot Games");
    expect(siteConfig.riotLegalNotice).toContain("trademarks");
  });

  it("aparece também em destaque na página Sobre", () => {
    const { container } = render(<SobrePage />);
    expect(container.querySelector("[data-aviso='riot']")?.textContent).toBe(
      siteConfig.riotLegalNotice,
    );
  });

  it("o rodapé leva para a página Sobre", () => {
    render(<Rodape />);
    expect(screen.getByRole("link", { name: /Sobre/ }).getAttribute("href")).toBe("/sobre");
  });
});

// --- RF-22: as fontes ---------------------------------------------------------------------

describe("créditos das fontes", () => {
  it("toda fonte do contrato tem crédito — fonte nova não entra sem ele", () => {
    for (const fonte of FONTES_DO_CONTRATO) {
      expect(CREDITOS[fonte], `sem crédito para ${fonte}`).toBeTruthy();
      expect(CREDITOS[fonte].nome.length).toBeGreaterThan(0);
      expect(CREDITOS[fonte].url).toMatch(/^https:\/\//);
    }
    expect(Object.keys(CREDITOS).sort()).toEqual([...FONTES_DO_CONTRATO].sort());
  });

  it("a página cita as fontes efetivamente usadas", () => {
    const { container } = render(<SobrePage />);
    const lista = within(screen.getByLabelText("Fontes e créditos"));
    expect(lista.getByRole("link", { name: "Data Dragon" })).toBeTruthy();
    expect(lista.getByRole("link", { name: "Community Dragon" })).toBeTruthy();
    expect(container.querySelector("[data-fonte='ddragon']")).not.toBeNull();
    expect(container.querySelector("[data-fonte='cdragon']")).not.toBeNull();
  });

  it("cada crédito diz o que aquela fonte traz de diferente", () => {
    expect(CREDITOS.cdragon.papel).toContain("chromas");
  });
});

// --- RF-22, parte perigosa: a wiki --------------------------------------------------------

describe("o crédito à wiki", () => {
  it("não aparece enquanto o consentimento não existir", () => {
    expect(creditosVisiveis(false).map((c) => c.fonte)).not.toContain("wiki");
  });

  it("a página, hoje, não cita a Weird Gloop", () => {
    const { container } = render(<SobrePage />);
    expect(siteConfig.wikiConsentGranted).toBe(false);
    expect(container.querySelector("[data-fonte='wiki']")).toBeNull();
    expect(container.textContent).not.toContain("Weird Gloop");
  });

  it("com o consentimento, aparece — com a licença do texto separada da arte", () => {
    const comWiki = creditosVisiveis(true).find((c) => c.fonte === "wiki");
    expect(comWiki).toBeTruthy();
    expect(comWiki?.licencaDoTexto).toContain("CC BY-SA");
    expect(comWiki?.licencaDoTexto).toContain("imagens continuam sendo da Riot");
  });

  it("nenhuma outra fonte reivindica licença de texto", () => {
    for (const fonte of ["ddragon", "cdragon", "riot_static"] as const) {
      expect(CREDITOS[fonte].licencaDoTexto).toBeUndefined();
    }
  });
});

// --- RF-23: o nome ------------------------------------------------------------------------

describe("o nome exibido", () => {
  it("continua fora das três palavras proibidas (ADR 0003)", () => {
    const proibidas = ["riot", "league of legends", "lol"];
    const nome = siteConfig.displayName.toLowerCase();
    for (const palavra of proibidas) {
      expect(nome.includes(palavra), `"${palavra}" no nome exibido`).toBe(false);
    }
  });

  it("o título da página Sobre é derivado dele, não escrito à mão", () => {
    // Quando o [ADR 0003] fechar o nome, o título da aba muda junto — sem
    // ninguém precisar lembrar de mudar aqui.
    expect(metadata.title).toBe(`Sobre — ${siteConfig.displayName}`);
  });
});

// --- o que a página promete -----------------------------------------------------------------

describe("o que a página diz", () => {
  it("deixa claro que nenhuma imagem é hospedada aqui (ADR 0012)", () => {
    const { container } = render(<SobrePage />);
    expect(container.textContent).toContain("Nenhuma imagem é hospedada aqui");
  });

  it("diz que a arte é da Riot, sem reivindicar direito nenhum", () => {
    const { container } = render(<SobrePage />);
    expect(within(screen.getByLabelText("Licenças")).getByText(/A arte é da Riot Games/)).toBeTruthy();
    expect(container.textContent).toContain("não reivindica direito nenhum");
  });

  it("não faz requisição nenhuma: continua correta com a indexação quebrada", () => {
    const { container } = render(<SobrePage />);
    expect(container.querySelector("img")).toBeNull();
  });
});
