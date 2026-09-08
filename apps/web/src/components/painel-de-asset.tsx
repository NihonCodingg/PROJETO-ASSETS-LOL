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
 * Tela crua de propósito; o design chega no T-30.
 */

import { useCallback, useEffect, useMemo, useState } from "react";

import type { Asset } from "@lol-assets/schema";

import { orderAssets } from "@/lib/asset-panel";
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

      <ul>
        {ordenados.map((asset) => (
          <CartaoDeAsset
            key={asset.id}
            asset={asset}
            url={assetUrl(asset, assetsBaseUrl)}
            estado={estados[asset.id] ?? "pronto"}
            marcar={marcar}
            baixar={baixar}
            copiar={copiar}
          />
        ))}
      </ul>
    </section>
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
    <li>
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
    </li>
  );
}
