import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { Command } from "cmdk";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Botao } from "./botao";
import { Campo, Tecla } from "./campo";
import { FecharPainel, PainelLateral } from "./painel-lateral";
import { Etiqueta, Meta, RotuloDeSecao } from "./rotulo";

/**
 * Os primitivos do T-34 — e a parte do ADR 0011 que dá errado em silêncio.
 *
 * O teste do `cmdk` é o mais importante do arquivo: o filtro embutido dele é
 * ligado por padrão, e ligado ele **substitui** a busca do [ADR 0009] por uma
 * comparação de substring que não sabe de apelido nem de acento. O sintoma não
 * é erro; é `mf` deixar de achar Miss Fortune.
 */

afterEach(cleanup);

// --- botão ------------------------------------------------------------------------

describe("Botão", () => {
  it("é `type=button` por padrão — dentro de form, `submit` seria surpresa", () => {
    render(<Botao>ok</Botao>);
    expect(screen.getByRole("button").getAttribute("type")).toBe("button");
  });

  it("as três variantes existem e são distintas", () => {
    const { container } = render(
      <>
        <Botao variante="primario">a</Botao>
        <Botao variante="contorno">b</Botao>
        <Botao variante="fantasma">c</Botao>
      </>,
    );
    const classes = [...container.querySelectorAll("button")].map((b) => b.className);
    expect(new Set(classes).size).toBe(3);
    expect(classes[0]).toContain("bg-acento");
    expect(classes[1]).toContain("border-borda-forte");
  });

  it("desabilitado parece desabilitado, não só ignora o clique", () => {
    render(<Botao disabled>x</Botao>);
    const botao = screen.getByRole("button") as HTMLButtonElement;
    expect(botao.disabled).toBe(true);
    expect(botao.className).toContain("disabled:opacity-45");
  });

  it("aceita classe de fora sem perder a própria", () => {
    render(<Botao className="w-full">x</Botao>);
    const classe = screen.getByRole("button").className;
    expect(classe).toContain("w-full");
    expect(classe).toContain("rounded-padrao");
  });
});

// --- campo e tecla ------------------------------------------------------------------

describe("Campo", () => {
  it("tem o cursor no acento — é o único sinal de foco para quem usa mouse", () => {
    render(<Campo aria-label="busca" />);
    expect(screen.getByLabelText("busca").className).toContain("caret-acento");
  });

  it("o placeholder usa um cinza que passa em AA", () => {
    render(<Campo aria-label="busca" placeholder="Buscar…" />);
    // `texto-suave` (6,91:1 sobre `campo`), não o `#52525b` do design.
    expect(screen.getByLabelText("busca").className).toContain("placeholder:text-texto-suave");
  });
});

describe("Tecla", () => {
  it("é um `kbd`, não um `span` com borda", () => {
    const { container } = render(<Tecla>/</Tecla>);
    expect(container.querySelector("kbd")).not.toBeNull();
  });
});

// --- rótulos ------------------------------------------------------------------------

describe("rótulos", () => {
  it("o rótulo de seção é mono, caixa alta e com o espacejamento do design", () => {
    const { container } = render(<RotuloDeSecao>Categorias</RotuloDeSecao>);
    const classe = container.firstElementChild!.className;
    expect(classe).toContain("font-mono");
    expect(classe).toContain("uppercase");
    expect(classe).toContain("tracking-rotulo");
  });

  it("metadado técnico é sempre mono — é assim que o design separa número de texto", () => {
    const { container } = render(<Meta>1280×720 · jpeg · 121 KB</Meta>);
    expect(container.firstElementChild!.className).toContain("font-mono");
  });

  it("a etiqueta usa o acento mais claro sobre o véu violeta", () => {
    const { container } = render(<Etiqueta>skin</Etiqueta>);
    expect(container.firstElementChild!.className).toContain("text-acento-mais-claro");
  });
});

// --- painel lateral -----------------------------------------------------------------

describe("PainelLateral", () => {
  it("fechado não desenha nada", () => {
    const { container } = render(
      <PainelLateral aberto={false} onFechar={() => {}} titulo="Painel">
        <p>conteúdo</p>
      </PainelLateral>,
    );
    expect(container.textContent).toBe("");
  });

  it("aberto é um diálogo com nome — sem nome, ninguém o anuncia", () => {
    render(
      <PainelLateral aberto onFechar={() => {}} titulo="Painel de Jax">
        <p>conteúdo</p>
      </PainelLateral>,
    );
    expect(screen.getByRole("dialog", { name: "Painel de Jax" })).toBeTruthy();
  });

  it("Escape fecha, porque o Radix trata a tecla por construção", () => {
    const fechar = vi.fn();
    render(
      <PainelLateral aberto onFechar={fechar} titulo="Painel">
        <p>conteúdo</p>
      </PainelLateral>,
    );
    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(fechar).toHaveBeenCalled();
  });

  it("o botão de fechar tem nome acessível, não só um `×`", () => {
    render(
      <PainelLateral aberto onFechar={() => {}} titulo="Painel">
        <FecharPainel />
      </PainelLateral>,
    );
    expect(screen.getByRole("button", { name: "Fechar" })).toBeTruthy();
  });
});

// --- critério 5: o cmdk não filtra ----------------------------------------------------

describe("cmdk com o filtro desligado", () => {
  function paleta(consulta: string) {
    return render(
      <Command shouldFilter={false}>
        <Command.Input value={consulta} onValueChange={() => {}} aria-label="buscar" />
        <Command.List>
          <Command.Item value="miss-fortune">Miss Fortune</Command.Item>
          <Command.Item value="twisted-fate">Twisted Fate</Command.Item>
          <Command.Item value="jarvan-iv">Jarvan IV</Command.Item>
        </Command.List>
      </Command>,
    );
  }

  it("consulta que não casa com nada devolve a lista inteira", () => {
    // Com o filtro ligado, `mf` esconderia os três: nenhum contém "mf". É esse
    // o modo de falha — o apelido do ADR 0009 casa, e o cmdk esconde depois.
    paleta("mf");
    expect(screen.getAllByRole("option")).toHaveLength(3);
  });

  it("consulta vazia também devolve tudo", () => {
    paleta("");
    expect(screen.getAllByRole("option")).toHaveLength(3);
  });

  it("a paleta que o produto usa passa `shouldFilter={false}`", () => {
    // Asserção de código-fonte de propósito: o comportamento do apelido já é
    // coberto pelo T-14 e pelo e2e. O que este teste protege é a linha que, se
    // alguém apagar numa refatoração, não quebra teste nenhum — só faz `mf`
    // parar de achar Miss Fortune, em silêncio.
    const fonte = readFileSync(resolve(process.cwd(), "src/components/paleta-de-busca.tsx"), "utf-8");
    expect(fonte).toContain("shouldFilter={false}");
  });
});
