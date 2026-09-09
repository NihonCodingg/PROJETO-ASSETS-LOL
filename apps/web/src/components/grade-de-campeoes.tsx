"use client";

/**
 * A grade padrão: 173 cartões, um por campeão ([ADR 0010]).
 *
 * **Não virtualiza, de propósito.** São 173 itens; o [ADR 0011] mediu que a
 * virtualização só se paga nos resultados de busca de skin, que chegam a 2.118.
 * Virtualizar 173 cartões custaria altura fixa por breakpoint e um scroller
 * próprio para não ganhar nada.
 */

import type { CatalogChampion } from "@lol-assets/schema";

import { thumbnailSrc } from "@/lib/asset-file";

export interface GradeDeCampeoesProps {
  readonly champions: readonly CatalogChampion[];
  readonly assetsBaseUrl?: string;
  readonly onAbrir: (champion: CatalogChampion) => void;
}

export function GradeDeCampeoes({ champions, assetsBaseUrl, onAbrir }: GradeDeCampeoesProps) {
  return (
    <ul aria-label="Campeões">
      {champions.map((champion) => {
        const miniatura = thumbnailSrc(champion, assetsBaseUrl);
        return (
          <li key={champion.championKey}>
            <button type="button" onClick={() => onAbrir(champion)}>
              {miniatura && (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={miniatura} alt={champion.names.pt_BR} width={64} height={64} />
              )}
              <span>{champion.names.pt_BR}</span>
              {/* RF-04: o cartão conta skins, nunca chromas. */}
              <span>
                {champion.skinCount} {champion.skinCount === 1 ? "skin" : "skins"}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
