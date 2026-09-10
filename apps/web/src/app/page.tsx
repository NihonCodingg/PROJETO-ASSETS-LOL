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

import { AvisoDeIndiceVelho } from "@/components/aviso-de-indice-velho";
import { GradeDeCampeoes } from "@/components/grade-de-campeoes";
import { useNavegacao } from "@/components/navegacao-context";
import { NavegacaoPorCategoria } from "@/components/navegacao-por-categoria";
import { PainelDoCampeao } from "@/components/painel-do-campeao";
import { PaletaDeBusca } from "@/components/paleta-de-busca";
import { Botao } from "@/components/ui/botao";
import { AssetsClient } from "@/lib/assets-client";
import { categoriasDisponiveis } from "@/lib/categorias";
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
  const { aberta, abrir, registrar } = useNavegacao();
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

  // A barra lateral desenha os botões de categoria, e ela só sabe quais existem
  // depois que o manifesto chega. Este é o único ponto em que os dois se
  // encontram (T-41).
  useEffect(() => {
    if (estado.fase !== "pronto") return;
    registrar(categoriasDisponiveis(versaoAtual(estado.manifest).shards));
  }, [estado, registrar]);

  const abrirCampeao = useCallback(
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
        {/* T-43: publicado, quem lê isto é um visitante, não quem roda o
            indexador. A instrução de gerar o índice só faz sentido no `next dev`. */}
        {process.env.NODE_ENV === "development" ? (
          <p>
            Gere o índice com <code>lol-assets-indexer index</code>; ele é servido de{" "}
            <code>{BASE_INDICE}</code>.
          </p>
        ) : (
          <p>Recarregue a página. Se continuar, o site pode estar no meio de uma atualização.</p>
        )}
        <Botao tamanho="md" onClick={() => window.location.reload()}>
          Recarregar
        </Botao>
      </Moldura>
    );
  }

  const { catalog, manifest } = estado;
  return (
    <main className="flex min-h-0 flex-1 flex-col">
      {/* O `h1` é o nome do produto e existe para leitor de tela e para o SEO;
          na tela ele já está na barra lateral, em cima do quadrado do acento. */}
      <h1 className="sr-only">{siteConfig.displayName}</h1>

      {/* T-31: o único alarme que existe. Sem monitoramento, o site é o detector. */}
      <AvisoDeIndiceVelho manifest={manifest} />

      <PaletaDeBusca
        catalog={catalog}
        onChampion={(champion) => void abrirCampeao(champion)}
        // O resultado de skin é atalho para dentro do painel, não destino
        // separado: abre o campeão já naquela skin (RF-25).
        onSkin={(skin, champion) => champion && void abrirCampeao(champion, skin.skinNum)}
      />

      {/* Uma grade por vez, como o design desenha (T-41). "Campeões" é a
          primeira categoria da barra lateral e é onde a home abre (RF-04);
          escolher outra troca o conteúdo em vez de empilhar. */}
      <div className="flex min-h-0 flex-1 flex-col">
        {aberta === null ? (
          // A grade rola por dentro deste `div`. A categoria **não** pode rolar
          // aqui: ela tem scroller virtual próprio, e um pai que rola daria a
          // ele altura zero — a lista viria vazia, sem erro nenhum.
          <div className="min-h-0 flex-1 overflow-y-auto">
            <GradeDeCampeoes
              champions={catalog.champions}
              assetsBaseUrl={BASE_ASSETS}
              onAbrir={(champion) => void abrirCampeao(champion)}
            />
          </div>
        ) : (
          /* RF-08: o outro caminho, para quem não tem nome para digitar.
             Nenhuma fatia é buscada até alguém abrir uma categoria. */
          <NavegacaoPorCategoria
            aberta={aberta}
            carregar={(category) => cliente.loadShard(manifest, category)}
            onFechar={() => abrir(null)}
            assetsBaseUrl={BASE_ASSETS}
          />
        )}
      </div>

      <p className="flex-none border-t border-borda px-3.5 py-1.5 font-mono text-10 text-texto-suave">
        patch {manifest.currentVersion} · {catalog.champions.length} campeões ·{" "}
        {catalog.skins.length} skins
      </p>

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
    </main>
  );
}

/** A única versão que existe desde o [ADR 0013]. */
function versaoAtual(manifest: IndexManifest): IndexManifest["versions"][number] {
  return (
    manifest.versions.find((v) => v.gameVersion === manifest.currentVersion) ?? manifest.versions[0]
  );
}

function Moldura({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-0 flex-1 flex-col items-center justify-center gap-2 px-3.5 text-center">
      <h1 className="text-19 font-semibold tracking-titulo">{siteConfig.displayName}</h1>
      {children}
    </main>
  );
}
