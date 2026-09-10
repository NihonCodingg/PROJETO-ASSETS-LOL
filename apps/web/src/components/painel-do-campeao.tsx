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
import { Botao } from "@/components/ui/botao";
import { PainelLateral } from "@/components/ui/painel-lateral";
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
    <PainelLateral
      aberto
      onFechar={onClose}
      titulo={`Painel de ${champion.names.pt_BR}`}
      // O `Escape` daqui tem ordem própria (chroma antes do painel) e o clique
      // fora nunca fechou. Ver o comentário em `PainelLateral`.
      fecharPorEsc={false}
      fecharPorFora={false}
    >
      <section
        aria-label={`Painel de ${champion.names.pt_BR}`}
        className="flex min-h-0 flex-1 flex-col"
      >
        <div className="flex flex-none flex-col gap-2 border-b border-borda px-3.5 py-3.5">
          <div className="flex items-start gap-2.5">
            <div className="min-w-0 flex-1">
              <div className="mb-0.75 font-mono text-10 uppercase tracking-rotulo text-acento">
                Campeão · {doCampeao.length} {doCampeao.length === 1 ? "skin" : "skins"}
              </div>
              <h2 className="text-19 font-semibold leading-apertada tracking-titulo">
                {champion.names.pt_BR}
              </h2>
            </div>
            <Botao tamanho="sm" onClick={onClose} aria-label="Fechar" title="Fechar (Esc)">
              ×
            </Botao>
          </div>

          <label className="flex items-center gap-2 font-mono text-10 uppercase tracking-rotulo text-texto-suave">
            Skin
            <select
              value={skinNum}
              onChange={(evento) => setSkinNum(Number(evento.target.value))}
              aria-label="Selecionar skin"
              className="h-controle-lg min-w-0 flex-1 rounded-padrao border border-borda-forte bg-campo px-2 font-interface text-13 normal-case tracking-normal text-texto"
            >
              {doCampeao.map((skin) => (
                <option key={skin.skinId} value={skin.skinNum}>
                  {skin.names.pt_BR}
                </option>
              ))}
            </select>
          </label>

          {/* RF-18: um clique pré-monta a seleção do campeão inteiro. */}
          {assets && alcancaveis.length > 0 && (
            <Botao
              tamanho="md"
              className="self-start"
              onClick={() => setSelecao(tudoDo(alcancaveis, chromasAbertos))}
            >
              Tudo de {champion.names.pt_BR} ({alcancaveis.length})
            </Botao>
          )}
        </div>

        {erro && (
          <p role="alert" className="px-3.5 py-3 text-13 text-acento-mais-claro">
            {erro}
          </p>
        )}
        {!assets && !erro && (
          <p className="px-3.5 py-3 text-13 text-texto-suave">carregando os assets…</p>
        )}

        <div className="min-h-0 flex-1 overflow-y-auto">
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
        <section aria-label="Chromas" className="border-t border-borda">
          <Botao
            variante="fantasma"
            tamanho="md"
            className="m-3.5"
            aria-expanded={chromasAbertos}
            onClick={() => setChromasAbertos((aberto) => !aberto)}
          >
            {chromasAbertos ? "Esconder" : "Mostrar"} {chromas.length}{" "}
            {chromas.length === 1 ? "chroma" : "chromas"}
          </Botao>
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
        </div>

        {/* A bandeja fica no pé do painel, fixa: com 40 assets selecionados, o
            botão de baixar não pode estar a uma rolagem de distância. */}
        <BarraDeLote
          assets={noLote}
          rotulo={champion.names.pt_BR}
          assetsBaseUrl={assetsBaseUrl}
          onLimpar={() => setSelecao(new Set())}
        />
      </section>
    </PainelLateral>
  );
}
