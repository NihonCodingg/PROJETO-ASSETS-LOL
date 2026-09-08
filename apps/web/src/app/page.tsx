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

import { thumbnailSrc } from "@/lib/asset-file";
import { PainelDeAsset } from "@/components/painel-de-asset";
import { PaletaDeBusca } from "@/components/paleta-de-busca";
import { AssetsClient } from "@/lib/assets-client";
import { siteConfig } from "@/lib/site-config";

/** O índice é servido pelo próprio app, de `public/indice` (ADR 0012). */
const BASE_INDICE = process.env.NEXT_PUBLIC_INDEX_BASE_URL ?? "/indice";

/**
 * Onde os assets COPIADOS moram. Vazio na opção B do ADR 0012 — nada é
 * copiado, então cada asset vale pela `sourceUrl`. A variável continua lida
 * para o dia em que houver bucket de novo.
 */
const BASE_ASSETS = process.env.NEXT_PUBLIC_ASSETS_BASE_URL ?? "";

type Estado =
  | { fase: "carregando" }
  | { fase: "erro"; motivo: string }
  | { fase: "pronto"; manifest: IndexManifest; catalog: Catalog };

export default function HomePage() {
  const cliente = useMemo(() => new AssetsClient(BASE_INDICE), []);
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
          Gere o índice com <code>lol-assets-indexer index</code>; ele é servido de{" "}
          <code>{BASE_INDICE}</code>.
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

      <PaletaDeBusca
        catalog={catalog}
        onChampion={abrir}
        onSkin={(_skin, campeao) => campeao && abrir(campeao)}
      />

      <ul aria-label="Campeões">
        {catalog.champions.map((campeao) => {
          const miniatura = thumbnailSrc(campeao, BASE_ASSETS);
          return (
          <li key={campeao.championKey}>
            <button type="button" onClick={() => abrir(campeao)}>
              {miniatura && (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={miniatura} alt={campeao.names.pt_BR} width={64} height={64} />
              )}
              <span>{campeao.names.pt_BR}</span>
              <span>
                {campeao.skinCount} {campeao.skinCount === 1 ? "skin" : "skins"}
              </span>
            </button>
          </li>
          );
        })}
      </ul>

      {aberto && (
        <PainelDeAsset
          titulo={aberto.names.pt_BR}
          assets={assets ?? []}
          assetsBaseUrl={BASE_ASSETS}
          onClose={() => setAberto(null)}
        />
      )}
      {aberto && erroDoPainel && <p role="alert">{erroDoPainel}</p>}
      {aberto && !assets && !erroDoPainel && <p>carregando os assets…</p>}
    </Moldura>
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
