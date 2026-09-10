/**
 * A barra lateral — marca no topo, navegação no meio, aviso legal no pé.
 *
 * O nome do arquivo continua `rodape` porque é o que ele é para o **RF-21**: o
 * lugar por onde o aviso da Riot passa em toda página. O design não desenhou
 * rodapé nenhum — o layout dele é `100vh` em duas colunas — e a decisão de
 * 10/09 foi pôr o aviso aqui, no pé da coluna da esquerda, em vez de comer
 * altura da grade com uma faixa atravessada.
 *
 * O quadrado violeta de 20px no topo é a marca do design. Ele não é logotipo:
 * é o acento, do tamanho que o desenho pede, no lugar que o desenho reservou
 * para `[ nome do produto ]`.
 */

import Link from "next/link";

import { siteConfig } from "@/lib/site-config";

export function Rodape() {
  return (
    <aside className="flex min-h-0 flex-row flex-wrap items-center gap-x-2 border-b border-borda bg-superficie md:flex-col md:flex-nowrap md:items-stretch md:gap-x-0 md:border-b-0 md:border-r">
      <div className="flex h-cabecalho flex-none items-center gap-2 px-3.5">
        <div className="size-5 flex-none rounded-marca bg-acento" aria-hidden="true" />
        <span className="text-13 font-semibold tracking-marca text-texto-forte">
          {siteConfig.displayName}
        </span>
      </div>

      <nav aria-label="Seções" className="flex flex-none flex-row gap-0.5 px-2 md:flex-col">
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

      {/* RF-21: o texto da Riot, **inteiro**, em toda página. Em tela estreita
          ele ocupa a linha toda da faixa em vez de ser cortado — "visível" com
          reticências não é visível. `mt-auto` põe ele no pé da coluna quando há
          coluna. */}
      <footer className="w-full flex-none px-3.5 pb-2 leading-solta md:mt-auto md:w-auto md:py-3">
        <p data-aviso="riot" className="font-mono text-10 text-texto-suave">
          {siteConfig.riotLegalNotice}
        </p>
      </footer>
    </aside>
  );
}
