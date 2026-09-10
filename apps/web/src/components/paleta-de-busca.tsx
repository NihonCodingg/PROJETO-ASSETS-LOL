"use client";

/**
 * A paleta de busca — cmdk pela lista acessível e pela navegação por teclado.
 *
 * **`shouldFilter={false}` não é detalhe.** O filtro embutido do cmdk faz um
 * casamento difuso próprio, e ligado ele descartaria `mf`, `j4` e `kda` antes de
 * o nosso ranqueamento ver a consulta — em silêncio, sem erro nenhum. Quem
 * decide o que aparece é o `search()` ([ADR 0011]).
 *
 * Tela crua de propósito: o design (T-30) e os tokens (T-34) chegam depois. O
 * que este ticket entrega é comportamento.
 */

import { useVirtualizer } from "@tanstack/react-virtual";
import { Command } from "cmdk";
import { useEffect, useMemo, useRef, useState } from "react";

import type { Catalog, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

import { Tecla } from "@/components/ui/campo";
import { buildSearchIndex, hitId, search, type SearchHit } from "@/lib/search";

/** Altura fixa por item — é o que a virtualização exige para medir. */
export const ALTURA_DO_ITEM = 44;
/** Acima disto a lista vira virtual. Abaixo, o custo não se paga (ADR 0011). */
export const LIMIAR_DE_VIRTUALIZACAO = 60;

export interface PaletaDeBuscaProps {
  readonly catalog: Catalog;
  readonly onChampion: (champion: CatalogChampion) => void;
  /** Uma skin escolhida abre o painel do campeão dela, já naquela skin (T-19). */
  readonly onSkin: (skin: CatalogSkin, champion: CatalogChampion | undefined) => void;
}

export function PaletaDeBusca({ catalog, onChampion, onSkin }: PaletaDeBuscaProps) {
  const indice = useMemo(() => buildSearchIndex(catalog), [catalog]);
  const [consulta, setConsulta] = useState("");
  const campo = useRef<HTMLInputElement>(null);

  // Sem teto: quem segura a lista é a virtualização, não um corte arbitrário.
  const resultados = useMemo(
    () => search(indice, consulta, Number.POSITIVE_INFINITY),
    [indice, consulta],
  );
  const scroller = useRef<HTMLDivElement>(null);
  const virtual = resultados.length > LIMIAR_DE_VIRTUALIZACAO;
  const virtualizador = useVirtualizer({
    count: resultados.length,
    getScrollElement: () => scroller.current,
    estimateSize: () => ALTURA_DO_ITEM,
    overscan: 8,
  });
  const janela = virtual
    ? virtualizador.getVirtualItems().map((v) => ({ indice: v.index, inicio: v.start }))
    : resultados.map((_, indice) => ({ indice, inicio: indice * ALTURA_DO_ITEM }));

  useEffect(() => {
    function atalho(evento: KeyboardEvent) {
      if (evento.key !== "/" || evento.defaultPrevented) return;
      const alvo = evento.target as HTMLElement | null;
      if (alvo && (alvo.tagName === "INPUT" || alvo.tagName === "TEXTAREA")) return;
      // `preventDefault` antes do foco: senão a barra entra no campo (RF-02).
      evento.preventDefault();
      campo.current?.focus();
    }
    window.addEventListener("keydown", atalho);
    return () => window.removeEventListener("keydown", atalho);
  }, []);

  function escolher(hit: SearchHit) {
    if (hit.kind === "champion") {
      onChampion(hit.champion);
      return;
    }
    onSkin(hit.skin, indice.byKey.get(hit.skin.championKey));
  }

  return (
    <Command
      shouldFilter={false}
      label="Buscar campeão ou skin"
      className="flex flex-none flex-col border-b border-borda"
    >
      <div className="relative flex h-cabecalho flex-none items-center px-3.5">
        <span
          aria-hidden="true"
          className="pointer-events-none absolute left-6 font-mono text-12 text-texto-suave"
        >
          ⌕
        </span>
        <Command.Input
          ref={campo}
          autoFocus
          value={consulta}
          onValueChange={setConsulta}
          placeholder="Campeão ou skin — tente mf, j4, K/DA"
          className="h-controle-lg w-full max-w-busca-max rounded-padrao border border-borda-forte bg-campo pl-6.5 pr-2.5 font-interface text-13 text-texto caret-acento placeholder:text-texto-suave focus:border-acento"
        />
        <Tecla className="absolute right-6 hidden sm:block">/</Tecla>
      </div>
      <div
        ref={scroller}
        data-virtual={virtual}
        data-resultados={resultados.length}
        className="overflow-y-auto px-2 pb-2 [&_[cmdk-item]]:flex [&_[cmdk-item]]:cursor-pointer [&_[cmdk-item]]:items-center [&_[cmdk-item]]:gap-2.5 [&_[cmdk-item]]:rounded-padrao [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:text-13 [&_[cmdk-item][data-selected=true]]:bg-acento-suave [&_[cmdk-item]>span:last-child]:ml-auto [&_[cmdk-item]>span:last-child]:font-mono [&_[cmdk-item]>span:last-child]:text-10 [&_[cmdk-item]>span:last-child]:text-texto-suave"
        style={{ maxHeight: ALTURA_DO_ITEM * 10 }}
      >
        <Command.List
          style={
            virtual
              ? { height: virtualizador.getTotalSize(), position: "relative" }
              : undefined
          }
        >
          {consulta && resultados.length === 0 && (
            <Command.Empty>Nada para “{consulta}”.</Command.Empty>
          )}
          {janela.map(({ indice: posicao, inicio }) => {
            const hit = resultados[posicao];
            return (
              <Command.Item
                key={hitId(hit)}
                value={hitId(hit)}
                onSelect={() => escolher(hit)}
                style={
                  virtual
                    ? {
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        height: ALTURA_DO_ITEM,
                        transform: `translateY(${inicio}px)`,
                      }
                    : undefined
                }
              >
                {hit.kind === "champion" ? (
                  <>
                    <span>{hit.champion.names.pt_BR}</span>
                    <span>
                      {hit.champion.skinCount} {hit.champion.skinCount === 1 ? "skin" : "skins"}
                    </span>
                  </>
                ) : (
                  <>
                    <span>{hit.skin.names.pt_BR}</span>
                    {/* RF-24: sem o rótulo, "Prestígio" não diz de quem é. */}
                    <span>{hit.championName}</span>
                  </>
                )}
              </Command.Item>
            );
          })}
        </Command.List>
      </div>
    </Command>
  );
}
