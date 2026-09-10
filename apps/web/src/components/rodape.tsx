/**
 * O rodapé — e o aviso legal que o RF-21 exige em **toda** página.
 *
 * Mora no `layout.tsx`, que é o único lugar por onde toda página passa. Repetir
 * o aviso página a página seria uma dessas coisas que funcionam até alguém
 * criar a página seguinte.
 */

import Link from "next/link";

import { siteConfig } from "@/lib/site-config";

export function Rodape() {
  return (
    <footer className="border-t border-neutral-800 px-6 py-8 text-xs text-neutral-500">
      <nav>
        <Link href="/">Início</Link> · <Link href="/sobre">Sobre, créditos e licenças</Link> ·{" "}
        <a href={siteConfig.repositoryUrl}>Código</a>
      </nav>
      {/* RF-21: o texto da Riot, visível, em toda página. */}
      <p data-aviso="riot">{siteConfig.riotLegalNotice}</p>
    </footer>
  );
}
