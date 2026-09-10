"use client";

/**
 * A grade padrão: 173 cartões, um por campeão ([ADR 0010]).
 *
 * **Não virtualiza, de propósito.** São 173 itens; o [ADR 0011] mediu que a
 * virtualização só se paga nos resultados de busca de skin, que chegam a 2.118.
 * Virtualizar 173 cartões custaria altura fixa por breakpoint e um scroller
 * próprio para não ganhar nada.
 *
 * O filtro por **função** do RF-08 mora aqui e não na navegação por categoria:
 * função é atributo de campeão, e campeão é a home ([ADR 0010]). As etiquetas
 * vêm do catálogo — os 173 campeões do patch 16.18.1 têm todas.
 */

import { useMemo, useState } from "react";

import type { CatalogChampion } from "@lol-assets/schema";

import { thumbnailSrc } from "@/lib/asset-file";
import { filtrarCampeoes, funcoesDe } from "@/lib/categorias";

export interface GradeDeCampeoesProps {
  readonly champions: readonly CatalogChampion[];
  readonly assetsBaseUrl?: string;
  readonly onAbrir: (champion: CatalogChampion) => void;
}

export function GradeDeCampeoes({ champions, assetsBaseUrl, onAbrir }: GradeDeCampeoesProps) {
  const funcoes = useMemo(() => funcoesDe(champions), [champions]);
  const [marcadas, setMarcadas] = useState<ReadonlySet<string>>(new Set());
  const visiveis = useMemo(() => filtrarCampeoes(champions, marcadas), [champions, marcadas]);

  function alternar(tag: string) {
    setMarcadas((antes) => {
      const proximo = new Set(antes);
      if (!proximo.delete(tag)) proximo.add(tag);
      return proximo;
    });
  }

  return (
    <>
      {funcoes.length > 0 && (
        <fieldset>
          <legend>Função</legend>
          {funcoes.map((funcao) => (
            <label key={funcao.tag}>
              <input
                type="checkbox"
                checked={marcadas.has(funcao.tag)}
                onChange={() => alternar(funcao.tag)}
              />
              {funcao.rotulo} ({funcao.total})
            </label>
          ))}
          {marcadas.size > 0 && (
            <button type="button" onClick={() => setMarcadas(new Set())}>
              Todas as funções
            </button>
          )}
        </fieldset>
      )}

      <p>
        {visiveis.length} de {champions.length} campeões
      </p>

      {visiveis.length === 0 ? (
        <p role="status">Nenhum campeão com essa função.</p>
      ) : (
        <GradeCrua champions={visiveis} assetsBaseUrl={assetsBaseUrl} onAbrir={onAbrir} />
      )}
    </>
  );
}

function GradeCrua({ champions, assetsBaseUrl, onAbrir }: GradeDeCampeoesProps) {
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
