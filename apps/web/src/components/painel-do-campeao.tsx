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
 *
 * **A seleção do lote mora aqui, não nos painéis.** "Tudo do Jax" (RF-18)
 * atravessa duas listas — a da skin e a dos chromas — e um estado por painel
 * faria o botão selecionar metade. Chroma só entra se estiver revelado, pela
 * mesma razão do RF-06: seleção que arrasta 43 chromas escondidos é a surpresa
 * que o RF-06 existe para evitar.
 */

import { useEffect, useMemo, useState } from "react";

import type { Asset, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

import { BarraDeLote } from "@/components/barra-de-lote";
import { PainelDeAsset } from "@/components/painel-de-asset";
import { baseSkin, chromasOf, panelAssets, skinsOf } from "@/lib/champion-panel";
import { alternar, selecionados, tudoDo } from "@/lib/selecao";

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
  const [selecao, setSelecao] = useState<ReadonlySet<string>>(new Set());

  /**
   * `Escape` mora aqui, e não nos painéis de dentro, por dois motivos.
   *
   * O primeiro é ordem: com os chromas abertos, `Escape` fecha os chromas — o
   * de dentro primeiro, como todo mundo espera. Dois ouvintes na mesma tecla
   * fechariam os dois de uma vez.
   *
   * O segundo é tempo: o painel aparece antes de a fatia chegar, e um ouvinte
   * que só existe depois dos assets deixa `Escape` sem efeito exatamente
   * durante a espera, que é quando alguém mais desiste.
   */
  useEffect(() => {
    function aoTeclar(evento: KeyboardEvent) {
      if (evento.key !== "Escape") return;
      if (chromasAbertos) setChromasAbertos(false);
      else onClose();
    }
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, [chromasAbertos, onClose]);

  // A busca pode trocar de campeão com o painel aberto: sem isto, a skin
  // selecionada ficaria a do campeão anterior — e a seleção levaria assets de
  // um campeão que já não está na tela.
  useEffect(() => {
    setSkinNum(padrao);
    setChromasAbertos(false);
    setSelecao(new Set());
  }, [padrao, champion.championKey]);

  const lista = useMemo(() => assets ?? [], [assets]);
  const visiveis = useMemo(() => panelAssets(lista, skinNum), [lista, skinNum]);
  const chromas = useMemo(() => chromasOf(lista, skinNum), [lista, skinNum]);
  const skinAtual = doCampeao.find((skin) => skin.skinNum === skinNum);

  // O que o lote pode alcançar: o que está na tela agora. Chroma escondido não
  // está na tela e por isso não entra nem no "tudo", nem na conta.
  const alcancaveis = useMemo(
    () => (chromasAbertos ? [...visiveis, ...chromas] : visiveis),
    [visiveis, chromas, chromasAbertos],
  );
  const noLote = useMemo(() => selecionados(alcancaveis, selecao), [alcancaveis, selecao]);
  const alternarNoLote = (id: string) => setSelecao((antes) => alternar(antes, id));

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

      {/* RF-18: um clique pré-monta a seleção do campeão inteiro. */}
      {assets && alcancaveis.length > 0 && (
        <button type="button" onClick={() => setSelecao(tudoDo(alcancaveis, chromasAbertos))}>
          Tudo de {champion.names.pt_BR} ({alcancaveis.length})
        </button>
      )}

      <BarraDeLote
        assets={noLote}
        rotulo={champion.names.pt_BR}
        assetsBaseUrl={assetsBaseUrl}
        onLimpar={() => setSelecao(new Set())}
      />

      {assets && (
        <PainelDeAsset
          titulo={skinAtual?.names.pt_BR ?? champion.names.pt_BR}
          assets={visiveis}
          assetsBaseUrl={assetsBaseUrl}
          onClose={onClose}
          selecao={selecao}
          onAlternar={alternarNoLote}
          fecharComEsc={false}
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
              selecao={selecao}
              onAlternar={alternarNoLote}
              fecharComEsc={false}
            />
          )}
        </section>
      )}
    </section>
  );
}
