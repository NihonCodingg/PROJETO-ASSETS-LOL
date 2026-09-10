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
    <main>
      <h1>Sobre</h1>

      <section aria-label="O que é">
        <h2>O que é</h2>
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

      <section aria-label="Não afiliação">
        <h2>Não afiliação</h2>
        {/* RF-21 e RNF-10. O mesmo texto do rodapé, aqui em destaque. */}
        <p data-aviso="riot">{siteConfig.riotLegalNotice}</p>
        <p>
          Este é um projeto pessoal, sem fins lucrativos, sem publicidade e sem qualquer
          vínculo com a Riot Games.
        </p>
      </section>

      <section aria-label="Fontes e créditos">
        <h2>Fontes e créditos</h2>
        <ul>
          {creditos.map((credito) => (
            <li key={credito.fonte} data-fonte={credito.fonte}>
              <a href={credito.url}>{credito.nome}</a> — {credito.papel}
              {credito.licencaDoTexto && <> Licença do conteúdo: {credito.licencaDoTexto}.</>}
            </li>
          ))}
        </ul>
      </section>

      <section aria-label="Licenças">
        <h2>Licenças</h2>
        <p>
          <strong>A arte é da Riot Games.</strong> Toda ela, em todas as fontes. Este projeto
          não reivindica direito nenhum sobre as imagens e não altera a licença delas: ele
          só diz onde elas estão.
        </p>
        <p>
          O <strong>código</strong> deste projeto é aberto e está em{" "}
          <a href={siteConfig.repositoryUrl}>{siteConfig.repositoryUrl}</a>. O índice gerado
          descreve arquivos de terceiros e não contém nenhum deles.
        </p>
      </section>

      <p>
        <Link href="/">Voltar ao catálogo</Link>
      </p>
    </main>
  );
}
