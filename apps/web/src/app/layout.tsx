import type { Metadata } from "next";

import { Rodape } from "@/components/rodape";
import { fonteInterface, fonteMono } from "@/lib/fontes";
import { siteConfig } from "@/lib/site-config";

import "./globals.css";

export const metadata: Metadata = {
  title: siteConfig.displayName,
  description: siteConfig.description,
};

/**
 * A casca de duas colunas do design: barra lateral de 208px e o resto.
 *
 * Ela mora no layout, e não na página, por causa do RF-21: o aviso da Riot é
 * obrigatório em **toda** página, e o layout é o único caminho por onde toda
 * página passa. O design não tinha rodapé — decidido em 10/09 que ele vai no pé
 * da barra lateral, que é onde sobrava espaço sem comer altura da grade.
 *
 * `h-screen` com `overflow-hidden`: as duas colunas rolam por dentro, não a
 * janela. É o que faz a barra lateral ficar parada enquanto 5.042 ícones passam
 * ao lado.
 */
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" className={`${fonteInterface.variable} ${fonteMono.variable}`}>
      {/* Abaixo de `md` a barra lateral vira faixa no topo: 208px fixos num
          telefone de 375px deixariam 167px para a grade, que não é largura de
          nada. Acima, as duas colunas do design. */}
      <body className="grid h-screen grid-rows-[auto_1fr] overflow-hidden bg-fundo text-texto md:grid-cols-[var(--spacing-barra-lateral)_1fr] md:grid-rows-1">
        <Rodape />
        <div className="flex min-h-0 min-w-0 flex-col">{children}</div>
      </body>
    </html>
  );
}
