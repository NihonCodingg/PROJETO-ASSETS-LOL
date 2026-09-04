"use client";

/**
 * Esqueleto andante do front (T-08).
 *
 * Carrega o manifesto e o catálogo, desenha a grade de **campeões** e, ao abrir
 * um, busca a fatia de assets **sob demanda** — a ordem do ADR 0010. Cada asset
 * mostra formato, resolução, tamanho e fonte antes de qualquer download, e
 * oferece o original e o PNG convertido no clique (ADR 0001).
 *
 * Tela crua de propósito: busca (T-14), seletor de skin (T-19) e o design
 * (T-30) chegam depois. O que este ticket entrega é o comportamento.
 */

import { useCallback, useEffect, useMemo, useState } from "react";

import type { Asset, Catalog, CatalogChampion, IndexManifest } from "@lol-assets/schema";

import {
  assetSummary,
  assetUrl,
  canConvertToPng,
  convertToPng,
  pngFileName,
  saveBlob,
} from "@/lib/asset-file";
import { AssetsClient } from "@/lib/assets-client";
import { siteConfig } from "@/lib/site-config";

const BASE_ASSETS = process.env.NEXT_PUBLIC_ASSETS_BASE_URL ?? "";

type Estado =
  | { fase: "carregando" }
  | { fase: "erro"; motivo: string }
  | { fase: "pronto"; manifest: IndexManifest; catalog: Catalog };

export default function HomePage() {
  const cliente = useMemo(() => new AssetsClient(BASE_ASSETS), []);
  const [estado, setEstado] = useState<Estado>({ fase: "carregando" });
  const [aberto, setAberto] = useState<CatalogChampion | null>(null);
  const [assets, setAssets] = useState<Asset[] | null>(null);
  const [erroDoPainel, setErroDoPainel] = useState<string | null>(null);

  useEffect(() => {
    let vivo = true;
    (async () => {
      try {
        const manifest = await cliente.loadManifest();
        const catalog = await cliente.loadCatalog(manifest);
        if (vivo) setEstado({ fase: "pronto", manifest, catalog });
      } catch (erro) {
        if (vivo) {
          setEstado({ fase: "erro", motivo: erro instanceof Error ? erro.message : String(erro) });
        }
      }
    })();
    return () => {
      vivo = false;
    };
  }, [cliente]);

  const abrir = useCallback(
    async (campeao: CatalogChampion) => {
      setAberto(campeao);
      setAssets(null);
      setErroDoPainel(null);
      if (estado.fase !== "pronto") return;
      try {
        // Sob demanda: a fatia só é buscada aqui, e uma vez por sessão.
        const shard = await cliente.loadShard(estado.manifest, "champion");
        setAssets(shard.assets.filter((a) => a.championKey === campeao.championKey));
      } catch (erro) {
        setErroDoPainel(erro instanceof Error ? erro.message : String(erro));
      }
    },
    [cliente, estado],
  );

  if (estado.fase === "carregando") {
    return <Moldura>carregando o catálogo…</Moldura>;
  }
  if (estado.fase === "erro") {
    return (
      <Moldura>
        <p role="alert">Falhou ao carregar o catálogo: {estado.motivo}</p>
        <p>
          Configure <code>NEXT_PUBLIC_ASSETS_BASE_URL</code> apontando para o bucket.
        </p>
      </Moldura>
    );
  }

  const { catalog, manifest } = estado;
  return (
    <Moldura>
      <p>
        patch {manifest.currentVersion} · {catalog.champions.length} campeões ·{" "}
        {catalog.skins.length} skins
      </p>

      <ul aria-label="Campeões">
        {catalog.champions.map((campeao) => (
          <li key={campeao.championKey}>
            <button type="button" onClick={() => abrir(campeao)}>
              {campeao.thumbnailKey && (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={`${BASE_ASSETS}/${campeao.thumbnailKey}`}
                  alt={campeao.names.pt_BR}
                  width={64}
                  height={64}
                />
              )}
              <span>{campeao.names.pt_BR}</span>
              <span>
                {campeao.skinCount} {campeao.skinCount === 1 ? "skin" : "skins"}
              </span>
            </button>
          </li>
        ))}
      </ul>

      {aberto && (
        <section aria-label={aberto.names.pt_BR}>
          <h2>{aberto.names.pt_BR}</h2>
          <button type="button" onClick={() => setAberto(null)}>
            fechar
          </button>
          {erroDoPainel && <p role="alert">{erroDoPainel}</p>}
          {!assets && !erroDoPainel && <p>carregando os assets…</p>}
          {assets?.map((asset) => (
            <CartaoDeAsset key={asset.id} asset={asset} />
          ))}
        </section>
      )}
    </Moldura>
  );
}

function CartaoDeAsset({ asset }: { asset: Asset }) {
  const [baixando, setBaixando] = useState<"original" | "png" | null>(null);
  const url = assetUrl(asset, BASE_ASSETS);

  const baixar = useCallback(
    async (comoPng: boolean) => {
      setBaixando(comoPng ? "png" : "original");
      try {
        const blob = await (await fetch(url)).blob();
        if (comoPng) saveBlob(await convertToPng(blob), pngFileName(asset.fileName));
        else saveBlob(blob, asset.fileName);
      } finally {
        setBaixando(null);
      }
    },
    [asset.fileName, url],
  );

  return (
    <article>
      <h3>{asset.type}</h3>
      {/* RF-09: a ficha aparece antes de qualquer clique de download. */}
      <p>{assetSummary(asset)}</p>
      <button type="button" disabled={baixando !== null} onClick={() => baixar(false)}>
        Baixar original
      </button>
      <button
        type="button"
        disabled={baixando !== null || !canConvertToPng(asset)}
        onClick={() => baixar(true)}
      >
        {canConvertToPng(asset) ? "Baixar PNG" : "já é PNG"}
      </button>
      <button type="button" onClick={() => navigator.clipboard.writeText(url)}>
        Copiar URL
      </button>
    </article>
  );
}

function Moldura({ children }: { children: React.ReactNode }) {
  return (
    <main>
      <h1>{siteConfig.displayName}</h1>
      {children}
    </main>
  );
}
