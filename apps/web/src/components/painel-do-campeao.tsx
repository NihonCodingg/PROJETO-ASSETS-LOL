"use client";

/**
 * O painel do campeão: o seletor de skin mora aqui, e só aqui ([ADR 0010]).
 *
 * Trocar de skin **não recarrega a fatia**. Ela já está em memória desde a
 * primeira abertura; o que muda é o filtro. É isso que mantém a promessa de ≤ 3
 * cliques do carregamento ao arquivo salvo.
 *
 * Chromas ficam atrás de um controle (RF-06): eles são 7.037 e não podem poluir
 * nem a grade nem a lista de skins. O controle só existe quando a skin tem
 * chroma.
 */

import { useEffect, useMemo, useState } from "react";

import type { Asset, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

import { PainelDeAsset } from "@/components/painel-de-asset";
import { baseSkin, chromasOf, panelAssets, skinsOf } from "@/lib/champion-panel";

export interface PainelDoCampeaoProps {
  readonly champion: CatalogChampion;
  readonly skins: readonly CatalogSkin[];
  readonly assets: readonly Asset[] | null;
  /** Skin que a busca pediu. Sem ela, o painel abre na base. */
  readonly skinInicial?: number;
  readonly assetsBaseUrl?: string;
  readonly erro?: string | null;
  readonly onClose: () => void;
}

export function PainelDoCampeao({
  champion,
  skins,
  assets,
  skinInicial,
  assetsBaseUrl,
  erro,
  onClose,
}: PainelDoCampeaoProps) {
  const doCampeao = useMemo(() => skinsOf(skins, champion), [skins, champion]);
  const padrao = useMemo(
    () => skinInicial ?? baseSkin(skins, champion)?.skinNum ?? 0,
    [skinInicial, skins, champion],
  );
  const [skinNum, setSkinNum] = useState(padrao);
  const [chromasAbertos, setChromasAbertos] = useState(false);

  // A busca pode trocar de campeão com o painel aberto: sem isto, a skin
  // selecionada ficaria a do campeão anterior.
  useEffect(() => {
    setSkinNum(padrao);
    setChromasAbertos(false);
  }, [padrao, champion.championKey]);

  const lista = useMemo(() => assets ?? [], [assets]);
  const visiveis = useMemo(() => panelAssets(lista, skinNum), [lista, skinNum]);
  const chromas = useMemo(() => chromasOf(lista, skinNum), [lista, skinNum]);
  const skinAtual = doCampeao.find((skin) => skin.skinNum === skinNum);

  return (
    <section aria-label={`Painel de ${champion.names.pt_BR}`}>
      <h2>{champion.names.pt_BR}</h2>

      <label>
        Skin
        <select
          value={skinNum}
          onChange={(evento) => setSkinNum(Number(evento.target.value))}
          aria-label="Selecionar skin"
        >
          {doCampeao.map((skin) => (
            <option key={skin.skinId} value={skin.skinNum}>
              {skin.names.pt_BR}
            </option>
          ))}
        </select>
      </label>

      {erro && <p role="alert">{erro}</p>}
      {!assets && !erro && <p>carregando os assets…</p>}

      {assets && (
        <PainelDeAsset
          titulo={skinAtual?.names.pt_BR ?? champion.names.pt_BR}
          assets={visiveis}
          assetsBaseUrl={assetsBaseUrl}
          onClose={onClose}
        />
      )}

      {/* RF-06: chroma não aparece sozinho; só quando alguém pede o desta skin. */}
      {assets && chromas.length > 0 && (
        <section aria-label="Chromas">
          <button
            type="button"
            aria-expanded={chromasAbertos}
            onClick={() => setChromasAbertos((aberto) => !aberto)}
          >
            {chromasAbertos ? "Esconder" : "Mostrar"} {chromas.length}{" "}
            {chromas.length === 1 ? "chroma" : "chromas"}
          </button>
          {chromasAbertos && (
            <PainelDeAsset
              titulo={`Chromas de ${skinAtual?.names.pt_BR ?? champion.names.pt_BR}`}
              assets={chromas}
              assetsBaseUrl={assetsBaseUrl}
              onClose={() => setChromasAbertos(false)}
            />
          )}
        </section>
      )}
    </section>
  );
}
