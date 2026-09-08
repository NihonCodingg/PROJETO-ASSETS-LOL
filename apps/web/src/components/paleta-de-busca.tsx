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

import { Command } from "cmdk";
import { useEffect, useMemo, useRef, useState } from "react";

import type { Catalog, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

import { buildSearchIndex, hitId, search, type SearchHit } from "@/lib/search";

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

  const resultados = useMemo(() => search(indice, consulta), [indice, consulta]);

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
    <Command shouldFilter={false} label="Buscar campeão ou skin">
      <Command.Input
        ref={campo}
        autoFocus
        value={consulta}
        onValueChange={setConsulta}
        placeholder="Campeão ou skin — tente mf, j4, K/DA"
      />
      <Command.List>
        {consulta && resultados.length === 0 && (
          <Command.Empty>Nada para “{consulta}”.</Command.Empty>
        )}
        {resultados.map((hit) => (
          <Command.Item key={hitId(hit)} value={hitId(hit)} onSelect={() => escolher(hit)}>
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
        ))}
      </Command.List>
    </Command>
  );
}
