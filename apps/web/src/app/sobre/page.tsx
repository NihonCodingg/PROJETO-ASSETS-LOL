/**
 * "Sobre": o que é isto, de onde vem a arte, e sob que licenças (RF-22).
 *
 * Página estática de propósito — não carrega índice, não faz requisição, e por
 * isso continua correta mesmo quando a indexação está quebrada. É também a
 * única página que precisa existir para o lançamento ser legal.
 *
 * O texto legal **definitivo** é o T-33, junto com a decisão do nome
 * ([ADR 0003](../../../../docs/adr/0003-nome-publico-do-produto.md)). O que está
 * aqui é o conteúdo obrigatório, com o aviso da Riot exatamente como ele deve
 * aparecer.
 *
 * Tela crua de propósito; o design chega no T-30.
 */

import type { Metadata } from "next";
import Link from "next/link";

import { creditosVisiveis } from "@/lib/creditos";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = {
  title: `Sobre — ${siteConfig.displayName}`,
  description: "Fontes, créditos, licenças e aviso de não afiliação.",
};

export default function SobrePage() {
  const creditos = creditosVisiveis(siteConfig.wikiConsentGranted);

  return (
    <main className="min-h-0 flex-1 overflow-y-auto px-3.5 py-6">
      <div className="mx-auto flex max-w-busca-max flex-col gap-6">
      <h1 className="text-19 font-semibold tracking-titulo">Sobre</h1>

      <section className="flex flex-col gap-2 text-13 leading-cartao text-texto-medio" aria-label="O que é">
        <h2 className="mb-1.5 text-12 font-medium uppercase tracking-rotulo text-texto-suave">O que é</h2>
        <p>
          {siteConfig.displayName} é um catálogo de assets visuais de League of Legends: um
          índice que diz onde cada arte está, em que resolução e em que formato, para que
          baixar a certa custe três cliques em vez de uma tarde.
        </p>
        <p>
          <strong>Nenhuma imagem é hospedada aqui.</strong> O que este site publica é o
          índice; os arquivos vêm direto das fontes abaixo, e o download acontece entre o seu
          navegador e elas.
        </p>
      </section>

      <section className="flex flex-col gap-2 text-13 leading-cartao text-texto-medio" aria-label="Não afiliação">
        <h2 className="mb-1.5 text-12 font-medium uppercase tracking-rotulo text-texto-suave">Não afiliação</h2>
        {/* RF-21 e RNF-10. O mesmo texto do rodapé, aqui em destaque. */}
        <p data-aviso="riot" className="rounded-padrao border border-borda-forte bg-campo p-2.5 font-mono text-11 leading-cartao text-texto-suave">
          {siteConfig.riotLegalNotice}
        </p>
        <p>
          Este é um projeto pessoal, sem fins lucrativos, sem publicidade e sem qualquer
          vínculo com a Riot Games.
        </p>
      </section>

      <section className="flex flex-col gap-2 text-13 leading-cartao text-texto-medio" aria-label="Fontes e créditos">
        <h2 className="mb-1.5 text-12 font-medium uppercase tracking-rotulo text-texto-suave">Fontes e créditos</h2>
        <ul className="flex flex-col gap-2">
          {creditos.map((credito) => (
            <li key={credito.fonte} data-fonte={credito.fonte} className="rounded-padrao border border-borda-forte p-2.5">
              <a href={credito.url} className="font-medium underline underline-offset-2 text-acento-claro hover:text-acento-mais-claro">
                {credito.nome}
              </a> — {credito.papel}
              {credito.licencaDoTexto && <> Licença do conteúdo: {credito.licencaDoTexto}.</>}
            </li>
          ))}
        </ul>
      </section>

      <section className="flex flex-col gap-2 text-13 leading-cartao text-texto-medio" aria-label="Licenças">
        <h2 className="mb-1.5 text-12 font-medium uppercase tracking-rotulo text-texto-suave">Licenças</h2>
        <p>
          <strong>A arte é da Riot Games.</strong> Toda ela, em todas as fontes. Este projeto
          não reivindica direito nenhum sobre as imagens e não altera a licença delas: ele
          só diz onde elas estão.
        </p>
        <p>
          O <strong>código</strong> deste projeto é aberto e está em{" "}
          <a href={siteConfig.repositoryUrl} className="underline underline-offset-2 text-acento-claro hover:text-acento-mais-claro">
            {siteConfig.repositoryUrl}
          </a>. O índice gerado
          descreve arquivos de terceiros e não contém nenhum deles.
        </p>
      </section>

      <p>
        <Link href="/" className="text-13 underline underline-offset-2 text-acento-claro hover:text-acento-mais-claro">
          Voltar ao catálogo
        </Link>
      </p>
      </div>
    </main>
  );
}
