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
 *
 * ## O cartão, como o design o desenha
 *
 * Placa quadrada com a arte, nome embaixo e contagem de skins em mono. A placa
 * tem fundo próprio porque a miniatura demora: sem ele, 173 buracos pretos
 * piscam até a rede responder.
 */

import { useMemo, useState } from "react";

import type { CatalogChampion } from "@lol-assets/schema";

import { thumbnailSrc } from "@/lib/asset-file";
import { filtrarCampeoes, funcoesDe } from "@/lib/categorias";
import { cn } from "@/lib/utils";

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
        <fieldset className="flex flex-none flex-wrap items-center gap-1.5 border-b border-borda px-3.5 py-2">
          <legend className="float-left font-mono text-10 uppercase tracking-rotulo text-texto-suave">
            Função
          </legend>
          {funcoes.map((funcao) => (
            <label
              key={funcao.tag}
              className={cn(
                "cursor-pointer rounded-padrao border px-2 py-0.75 text-11",
                marcadas.has(funcao.tag)
                  ? "border-acento bg-acento-suave text-texto"
                  : "border-borda-forte text-texto-suave hover:bg-campo hover:text-texto",
              )}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={marcadas.has(funcao.tag)}
                onChange={() => alternar(funcao.tag)}
              />
              {funcao.rotulo} ({funcao.total})
            </label>
          ))}
          {marcadas.size > 0 && (
            <button
              type="button"
              onClick={() => setMarcadas(new Set())}
              className="cursor-pointer rounded-padrao px-2 py-0.75 text-11 text-texto-suave hover:bg-campo hover:text-texto"
            >
              Todas as funções
            </button>
          )}
        </fieldset>
      )}

      <div className="flex h-barra flex-none items-center gap-2.5 border-b border-borda bg-fundo-barra px-3.5">
        <span className="text-12 font-medium text-texto-forte">Campeões</span>
        <span className="font-mono text-11 text-texto-suave">
          {visiveis.length} de {champions.length} campeões
        </span>
        <div className="ml-auto hidden items-center gap-2 font-mono text-10 text-texto-suave sm:flex">
          <span>/ buscar</span>
          <span>↵ abrir</span>
        </div>
      </div>

      {visiveis.length === 0 ? (
        <p role="status" className="px-3.5 py-20 text-center text-14 text-texto-suave">
          Nenhum campeão com essa função.
        </p>
      ) : (
        <GradeCrua champions={visiveis} assetsBaseUrl={assetsBaseUrl} onAbrir={onAbrir} />
      )}
    </>
  );
}

function GradeCrua({ champions, assetsBaseUrl, onAbrir }: GradeDeCampeoesProps) {
  return (
    <ul
      aria-label="Campeões"
      className="grid grid-cols-[repeat(auto-fill,minmax(var(--spacing-alvo-cartao-denso),1fr))] gap-1.5 px-3.5 py-2"
    >
      {champions.map((champion) => {
        const miniatura = thumbnailSrc(champion, assetsBaseUrl);
        return (
          <li key={champion.championKey}>
            <button
              type="button"
              onClick={() => onAbrir(champion)}
              className="group w-full cursor-pointer rounded-padrao text-left"
            >
              {/* 1:1 e não o 16:9 do design: o mock usava splash, e a miniatura
                  real do campeão é o `square` de 128×128 do ddragon. Cortá-la em
                  16:9 tiraria 44% da altura — o rosto. A proporção segue o dado. */}
              <div className="relative aspect-square overflow-hidden rounded-padrao bg-campo">
                {miniatura && (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    src={miniatura}
                    alt={champion.names.pt_BR}
                    loading="lazy"
                    decoding="async"
                    className="size-full object-cover transition-opacity group-hover:opacity-80"
                  />
                )}
              </div>
              <div className="truncate pt-1.25 text-11 leading-cartao text-texto-medio">
                {champion.names.pt_BR}
              </div>
              {/* RF-04: o cartão conta skins, nunca chromas. */}
              <div className="truncate font-mono text-10 text-texto-suave">
                {champion.skinCount} {champion.skinCount === 1 ? "skin" : "skins"}
              </div>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
