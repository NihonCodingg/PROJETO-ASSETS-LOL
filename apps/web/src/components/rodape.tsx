"use client";

/**
 * A barra lateral — marca, categorias, seções e o aviso legal no pé.
 *
 * O nome do arquivo continua `rodape` porque é o que ele é para o **RF-21**: o
 * lugar por onde o aviso da Riot passa em toda página. O design não desenhou
 * rodapé nenhum — o layout dele é `100vh` em duas colunas — e a decisão de
 * 10/09 foi pôr o aviso aqui, no pé da coluna da esquerda, em vez de comer
 * altura da grade com uma faixa atravessada.
 *
 * As **categorias** entraram no T-41. Antes elas ficavam abaixo dos 173 cartões
 * de campeão, o que obrigava a rolar a grade inteira para chegar em "Itens".
 * Aqui elas estão sempre à vista, que é onde o design as desenhou.
 *
 * O quadrado violeta de 20px no topo é a marca do design. Ele não é logotipo: é
 * o acento, do tamanho que o desenho pede, no lugar que o desenho reservou para
 * `[ nome do produto ]`.
 */

import Link from "next/link";

import { useNavegacao } from "@/components/navegacao-context";
import { siteConfig } from "@/lib/site-config";
import { cn } from "@/lib/utils";

export function Rodape() {
  const { categorias, aberta, abrir } = useNavegacao();

  return (
    <aside className="flex min-h-0 flex-row flex-wrap items-center gap-x-2 border-b border-borda bg-superficie md:flex-col md:flex-nowrap md:items-stretch md:gap-x-0 md:overflow-y-auto md:border-b-0 md:border-r">
      <div className="flex h-cabecalho flex-none items-center gap-2 px-3.5">
        <div className="size-5 flex-none rounded-marca bg-acento" aria-hidden="true" />
        <span className="text-13 font-semibold tracking-marca text-texto-forte">
          {siteConfig.displayName}
        </span>
      </div>

      {/* Sem provedor — como no teste do T-27, que monta este componente sozinho
          — a lista vem vazia e a barra desenha só o resto. */}
      {categorias.length > 0 && (
        <nav
          aria-label="Categorias"
          className="flex w-full flex-row flex-wrap gap-0.5 px-2 md:w-auto md:flex-none md:flex-col md:flex-nowrap"
        >
          <span className="hidden px-2 pt-1.5 pb-1 font-mono text-10 uppercase tracking-rotulo text-texto-suave md:block">
            Categorias
          </span>
          {/* RF-04: campeão é a navegação padrão, e no design ele é a primeira
              categoria da lista. `null` é a grade de campeões. */}
          <ItemDeCategoria rotulo="Campeões" ativo={aberta === null} onClick={() => abrir(null)} />
          {categorias.map((categoria) => (
            <ItemDeCategoria
              key={categoria.category}
              rotulo={categoria.rotulo}
              ativo={aberta === categoria.category}
              onClick={() => abrir(categoria.category)}
            />
          ))}
        </nav>
      )}

      <nav
        aria-label="Seções"
        className="flex w-full flex-row flex-wrap gap-0.5 px-2 md:mt-3 md:w-auto md:flex-none md:flex-col md:flex-nowrap"
      >
        <span className="hidden px-2 pt-1.5 pb-1 font-mono text-10 uppercase tracking-rotulo text-texto-suave md:block">
          Projeto
        </span>
        <Link
          href="/"
          className="rounded-padrao px-2 py-1.5 text-13 text-texto-suave hover:bg-campo hover:text-texto"
        >
          Início
        </Link>
        <Link
          href="/sobre"
          className="rounded-padrao px-2 py-1.5 text-13 text-texto-suave hover:bg-campo hover:text-texto"
        >
          Sobre e créditos
        </Link>
        <a
          href={siteConfig.repositoryUrl}
          className="rounded-padrao px-2 py-1.5 text-13 text-texto-suave hover:bg-campo hover:text-texto"
        >
          Código
        </a>
      </nav>

      {/* RF-21: os dois textos da Riot, **inteiros**, em toda página — o do
          Developer Portal e o do Legal Jibber Jabber (ver `site-config.ts`). Em
          tela estreita eles ocupam a linha toda da faixa em vez de serem
          cortados: "visível" com reticências não é visível. `mt-auto` põe o
          rodapé no pé da coluna quando há coluna. `lang="en"` porque o texto é
          copiado, não traduzido. */}
      <footer className="flex w-full flex-none flex-col gap-1.5 px-3.5 pb-2 leading-solta md:mt-auto md:w-auto md:py-3">
        <p data-aviso="riot" lang="en" className="font-mono text-10 text-texto-suave">
          {siteConfig.riotLegalNotice}
        </p>
        <p data-aviso="jibber-jabber" lang="en" className="font-mono text-10 text-texto-suave">
          {siteConfig.riotJibberJabberNotice}
        </p>
      </footer>
    </aside>
  );
}

function ItemDeCategoria({
  rotulo,
  ativo,
  onClick,
}: {
  rotulo: string;
  ativo: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={ativo}
      onClick={onClick}
      className={cn(
        "cursor-pointer rounded-padrao px-2 py-1.5 text-left text-13",
        ativo ? "bg-selecionado text-texto" : "text-texto-suave hover:bg-campo hover:text-texto",
      )}
    >
      {rotulo}
    </button>
  );
}
