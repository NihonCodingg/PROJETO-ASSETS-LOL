import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { IndexManifest } from "@lol-assets/schema";
import { examples } from "@lol-assets/schema/examples";

import { idadeEmPalavras, LIMITE_DE_IDADE_HORAS, medirFrescor } from "@/lib/frescor";

import { AvisoDeIndiceVelho } from "./aviso-de-indice-velho";

/**
 * O único alarme que existe (§11 da Spec).
 *
 * Não há monitoramento: o [ADR 0005] escolheu operação de custo zero, e o preço
 * é que o site tem que ser o próprio detector de "o workflow parou". Os dois
 * lados do limite são testados porque o erro perigoso aqui é o **falso
 * negativo** — o índice parado que ninguém percebe.
 */

afterEach(cleanup);

const AGORA = new Date("2026-09-09T12:00:00Z");

function manifestoCom(horas: number): IndexManifest {
  const gerado = new Date(AGORA.getTime() - horas * 3_600_000);
  return { ...examples.manifest, generatedAt: gerado.toISOString() } as IndexManifest;
}

describe("o limite", () => {
  it("uma hora antes do limite, sem aviso", () => {
    const { container } = render(
      <AvisoDeIndiceVelho manifest={manifestoCom(LIMITE_DE_IDADE_HORAS - 1)} agora={AGORA} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("exatamente no limite, ainda sem aviso", () => {
    const { container } = render(
      <AvisoDeIndiceVelho manifest={manifestoCom(LIMITE_DE_IDADE_HORAS)} agora={AGORA} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("uma hora depois do limite, avisa", () => {
    render(<AvisoDeIndiceVelho manifest={manifestoCom(LIMITE_DE_IDADE_HORAS + 1)} agora={AGORA} />);
    expect(screen.getByRole("status")).toBeTruthy();
  });

  it("índice recém-gerado não avisa", () => {
    const { container } = render(<AvisoDeIndiceVelho manifest={manifestoCom(0)} agora={AGORA} />);
    expect(container.firstChild).toBeNull();
  });

  it("o limite são as 12 execuções do workflow de 6 h", () => {
    expect(LIMITE_DE_IDADE_HORAS).toBe(72);
  });
});

describe("o que o aviso diz", () => {
  it("mostra a data da última indexação, legível e em `datetime`", () => {
    const manifesto = manifestoCom(96);
    render(<AvisoDeIndiceVelho manifest={manifesto} agora={AGORA} />);

    const aviso = screen.getByRole("status");
    expect(aviso.textContent).toContain("5 de setembro de 2026");
    expect(aviso.querySelector("time")?.getAttribute("dateTime")).toBe(manifesto.generatedAt);
  });

  it("diz a idade em palavras", () => {
    render(<AvisoDeIndiceVelho manifest={manifestoCom(96)} agora={AGORA} />);
    expect(screen.getByRole("status").textContent).toContain("4 dias");
  });

  it("diz que o site continua funcionando — não é bloqueio", () => {
    render(<AvisoDeIndiceVelho manifest={manifestoCom(200)} agora={AGORA} />);
    expect(screen.getByRole("status").textContent).toContain("continua funcionando");
  });

  it("é status, não alert: não interrompe quem está baixando", () => {
    render(<AvisoDeIndiceVelho manifest={manifestoCom(200)} agora={AGORA} />);
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("medir o frescor", () => {
  it("devolve horas, veredito e a data de geração", () => {
    const frescor = medirFrescor(manifestoCom(80), AGORA);
    expect(frescor.horas).toBeCloseTo(80, 1);
    expect(frescor.velho).toBe(true);
    expect(frescor.geradoEm.toISOString()).toBe("2026-09-06T04:00:00.000Z");
  });

  it("manifesto do futuro não vira aviso", () => {
    expect(medirFrescor(manifestoCom(-10), AGORA).velho).toBe(false);
  });
});

describe("idade em palavras", () => {
  it("abaixo de dois dias, conta horas", () => {
    expect(idadeEmPalavras(47.9)).toBe("47 horas");
  });

  it("de dois dias em diante, conta dias", () => {
    expect(idadeEmPalavras(48)).toBe("2 dias");
    expect(idadeEmPalavras(96)).toBe("4 dias");
  });

  it("arredonda para baixo — nunca diz que é mais velho do que é", () => {
    expect(idadeEmPalavras(95.9)).toBe("3 dias");
  });
});
