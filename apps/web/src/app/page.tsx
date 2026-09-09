"use client";

/**
 * A página: grade de campeões, busca e painel.
 *
 * A ordem de carga é a do [ADR 0010] e está verificada em rede: manifesto e
 * catálogo na abertura, fatia de assets **só no primeiro clique** num campeão.
 * A home desenha 173 cartões sem baixar um único registro de asset.
 *
 * Tela crua de propósito: o design (T-30) e os tokens (T-34) chegam depois.
 */

import { useCallback, useEffect, useMemo, useState } from "react";

import type { Asset, Catalog, CatalogChampion, IndexManifest } from "@lol-assets/schema";

import { GradeDeCampeoes } from "@/components/grade-de-campeoes";
import { PainelDoCampeao } from "@/components/painel-do-campeao";
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

interface Aberto {
  readonly champion: CatalogChampion;
  /** Skin que a busca pediu; sem ela o painel abre na base. */
  readonly skinNum?: number;
}

export default function HomePage() {
  const cliente = useMemo(() => new AssetsClient(BASE_INDICE), []);
  const [estado, setEstado] = useState<Estado>({ fase: "carregando" });
  const [aberto, setAberto] = useState<Aberto | null>(null);
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
    async (champion: CatalogChampion, skinNum?: number) => {
      setAberto({ champion, skinNum });
      setErroDoPainel(null);
      if (estado.fase !== "pronto") return;
      try {
        // Sob demanda, e memoizada: trocar de campeão não busca de novo.
        const shard = await cliente.loadShard(estado.manifest, "champion");
        setAssets(shard.assets.filter((a) => a.championKey === champion.championKey));
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
        onChampion={(champion) => void abrir(champion)}
        // O resultado de skin é atalho para dentro do painel, não destino
        // separado: abre o campeão já naquela skin (RF-25).
        onSkin={(skin, champion) => champion && void abrir(champion, skin.skinNum)}
      />

      <GradeDeCampeoes
        champions={catalog.champions}
        assetsBaseUrl={BASE_ASSETS}
        onAbrir={(champion) => void abrir(champion)}
      />

      {aberto && (
        <PainelDoCampeao
          champion={aberto.champion}
          skins={catalog.skins}
          assets={assets}
          skinInicial={aberto.skinNum}
          assetsBaseUrl={BASE_ASSETS}
          erro={erroDoPainel}
          onClose={() => setAberto(null)}
        />
      )}
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
