"use client";

/**
 * O painel de um item: todos os tipos que existem no índice, cada um com ficha
 * honesta antes de qualquer download (RF-09) e as duas formas de baixar.
 *
 * **Estado por asset, não por painel.** Um download que falha marca o cartão
 * dele e mais nada: são dezenas de cartões, e um erro de rede num deles não pode
 * apagar os outros da tela (critério 4).
 *
 * As duas ações que tocam o mundo — baixar e copiar — entram por injeção, com o
 * comportamento real como padrão. É o mesmo desenho do `PngDeps` do
 * `asset-file.ts`: testável sem mock de módulo.
 *
 * **Lista grande vira lista virtual.** Acima de `LIMITE_DE_VIRTUALIZACAO` cartões
 * o painel troca o `<ul>` por um scroller do TanStack Virtual ([ADR 0011]): a
 * categoria `profile_icon` tem 5.042 ícones, e 5.042 `<article>` no DOM é o
 * tipo de coisa que só se percebe no meio da rolagem. Abaixo do limite nada
 * muda — o painel de um campeão tem dezenas de cartões e não paga scroller
 * próprio por isso.
 *
 * Tela crua de propósito; o design chega no T-30, e as medidas inline do
 * scroller vão junto.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useVirtualizer } from "@tanstack/react-virtual";

import type { Asset } from "@lol-assets/schema";

import { LIMITE_DE_VIRTUALIZACAO, orderAssets } from "@/lib/asset-panel";
import {
  assetSummary,
  assetUrl,
  canConvertToPng,
  convertToPng,
  pngFileName,
  saveBlob,
} from "@/lib/asset-file";

export type EstadoDoCartao = "pronto" | "baixando" | "erro";

export interface PainelDeAssetProps {
  readonly titulo: string;
  readonly assets: readonly Asset[];
  readonly assetsBaseUrl?: string;
  readonly onClose: () => void;
  readonly baixar?: (asset: Asset, comoPng: boolean, url: string) => Promise<void>;
  readonly copiar?: (texto: string) => Promise<void>;
}

async function baixarDeVerdade(asset: Asset, comoPng: boolean, url: string): Promise<void> {
  const resposta = await fetch(url);
  if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
  const blob = await resposta.blob();
  if (comoPng) saveBlob(await convertToPng(blob), pngFileName(asset.fileName));
  else saveBlob(blob, asset.fileName);
}

function copiarDeVerdade(texto: string): Promise<void> {
  return navigator.clipboard.writeText(texto);
}

export function PainelDeAsset({
  titulo,
  assets,
  assetsBaseUrl,
  onClose,
  baixar = baixarDeVerdade,
  copiar = copiarDeVerdade,
}: PainelDeAssetProps) {
  const ordenados = useMemo(() => orderAssets(assets), [assets]);
  const [estados, setEstados] = useState<Record<string, EstadoDoCartao>>({});

  useEffect(() => {
    function aoTeclar(evento: KeyboardEvent) {
      if (evento.key === "Escape") onClose();
    }
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, [onClose]);

  const marcar = useCallback((id: string, estado: EstadoDoCartao) => {
    setEstados((anteriores) => ({ ...anteriores, [id]: estado }));
  }, []);

  return (
    <section aria-label={titulo}>
      <h2>{titulo}</h2>
      <button type="button" onClick={onClose}>
        fechar
      </button>
      <p>
        {ordenados.length} {ordenados.length === 1 ? "asset" : "assets"}
      </p>

      {ordenados.length > LIMITE_DE_VIRTUALIZACAO ? (
        <ListaVirtual
          assets={ordenados}
          assetsBaseUrl={assetsBaseUrl}
          estados={estados}
          marcar={marcar}
          baixar={baixar}
          copiar={copiar}
        />
      ) : (
        <ul>
          {ordenados.map((asset) => (
            <li key={asset.id}>
              <CartaoDeAsset
                asset={asset}
                url={assetUrl(asset, assetsBaseUrl)}
                estado={estados[asset.id] ?? "pronto"}
                marcar={marcar}
                baixar={baixar}
                copiar={copiar}
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

interface ListaVirtualProps {
  readonly assets: readonly Asset[];
  readonly assetsBaseUrl?: string;
  readonly estados: Record<string, EstadoDoCartao>;
  readonly marcar: (id: string, estado: EstadoDoCartao) => void;
  readonly baixar: (asset: Asset, comoPng: boolean, url: string) => Promise<void>;
  readonly copiar: (texto: string) => Promise<void>;
}

/** Altura estimada de um cartão. Chute honesto: o design (T-30) mede de verdade. */
const ALTURA_DO_CARTAO = 132;

function ListaVirtual({
  assets,
  assetsBaseUrl,
  estados,
  marcar,
  baixar,
  copiar,
}: ListaVirtualProps) {
  const scroller = useRef<HTMLDivElement>(null);
  // Sem `measureElement`: o cartão tem altura previsível e medir de volta em
  // jsdom (que não faz layout) devolveria zero e faria a lista se recalcular
  // para sempre. Estimativa fixa é o que mantém isto testável.
  const virtual = useVirtualizer({
    count: assets.length,
    getScrollElement: () => scroller.current,
    estimateSize: () => ALTURA_DO_CARTAO,
    overscan: 6,
  });

  return (
    <div
      ref={scroller}
      data-virtual="sim"
      style={{ height: "70vh", overflowY: "auto", contain: "strict" }}
    >
      <ul style={{ height: virtual.getTotalSize(), position: "relative", margin: 0, padding: 0 }}>
        {virtual.getVirtualItems().map((item) => {
          const asset = assets[item.index];
          return (
            <li
              key={asset.id}
              data-index={item.index}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: ALTURA_DO_CARTAO,
                transform: `translateY(${item.start}px)`,
              }}
            >
              <CartaoDeAsset
                asset={asset}
                url={assetUrl(asset, assetsBaseUrl)}
                estado={estados[asset.id] ?? "pronto"}
                marcar={marcar}
                baixar={baixar}
                copiar={copiar}
              />
            </li>
          );
        })}
      </ul>
    </div>
  );
}

interface CartaoProps {
  readonly asset: Asset;
  readonly url: string;
  readonly estado: EstadoDoCartao;
  readonly marcar: (id: string, estado: EstadoDoCartao) => void;
  readonly baixar: (asset: Asset, comoPng: boolean, url: string) => Promise<void>;
  readonly copiar: (texto: string) => Promise<void>;
}

function CartaoDeAsset({ asset, url, estado, marcar, baixar, copiar }: CartaoProps) {
  const acionar = useCallback(
    async (comoPng: boolean) => {
      marcar(asset.id, "baixando");
      try {
        await baixar(asset, comoPng, url);
        marcar(asset.id, "pronto");
      } catch {
        // O erro fica no cartão. Derrubar o painel por causa de um asset seria
        // esconder os outros trinta que funcionam.
        marcar(asset.id, "erro");
      }
    },
    [asset, baixar, marcar, url],
  );

  const ocupado = estado === "baixando";

  return (
    <article aria-label={asset.fileName} data-tipo={asset.type} data-estado={estado}>
      <h3>{asset.type}</h3>
      {/* RF-09: a ficha aparece antes de qualquer clique de download. */}
      <p>{assetSummary(asset)}</p>

      <button type="button" disabled={ocupado} onClick={() => void acionar(false)}>
        Baixar original
      </button>
      <button
        type="button"
        disabled={ocupado || !canConvertToPng(asset)}
        onClick={() => void acionar(true)}
      >
        {canConvertToPng(asset) ? "Baixar PNG" : "já é PNG"}
      </button>
      <button type="button" onClick={() => void copiar(url)}>
        Copiar URL
      </button>

      {estado === "erro" && <p role="alert">Falhou ao baixar. Tente de novo.</p>}
    </article>
  );
}
