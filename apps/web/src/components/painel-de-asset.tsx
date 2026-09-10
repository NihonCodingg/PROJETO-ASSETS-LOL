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

import { LIMITE_DE_VIRTUALIZACAO, orderAssets, rotuloDoTipo } from "@/lib/asset-panel";
import { Botao } from "@/components/ui/botao";
import { cn } from "@/lib/utils";
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
  /**
   * Seleção do lote (RF-17), **de fora**.
   *
   * O estado mora no pai porque um lote pode atravessar dois painéis: "tudo do
   * Jax" leva os assets da skin e os chromas, que são listas diferentes. Sem
   * `onAlternar` não há caixa nenhuma — é o que mantém o painel usável em
   * contexto onde lote não faz sentido.
   */
  readonly selecao?: ReadonlySet<string>;
  readonly onAlternar?: (id: string) => void;
  /**
   * Se `Escape` fecha **este** painel.
   *
   * `false` quando ele está dentro de outro que já trata a tecla: dois
   * ouvintes na mesma tecla fechariam os dois de uma vez, e quem tem chroma
   * aberto perderia o painel do campeão junto.
   */
  readonly fecharComEsc?: boolean;
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
  selecao,
  onAlternar,
  fecharComEsc = true,
}: PainelDeAssetProps) {
  const ordenados = useMemo(() => orderAssets(assets), [assets]);
  const [estados, setEstados] = useState<Record<string, EstadoDoCartao>>({});

  useEffect(() => {
    if (!fecharComEsc) return;
    function aoTeclar(evento: KeyboardEvent) {
      if (evento.key === "Escape") onClose();
    }
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, [onClose, fecharComEsc]);

  const marcar = useCallback((id: string, estado: EstadoDoCartao) => {
    setEstados((anteriores) => ({ ...anteriores, [id]: estado }));
  }, []);

  return (
    <section aria-label={titulo} className="flex min-h-0 flex-col">
      <div className="flex flex-none items-center gap-2 px-3.5 py-2">
        <h2 className="truncate text-12 font-medium text-texto-forte">{titulo}</h2>
        <span className="font-mono text-11 text-texto-suave">
          {ordenados.length} {ordenados.length === 1 ? "asset" : "assets"}
        </span>
        <Botao variante="fantasma" tamanho="md" onClick={onClose} className="ml-auto">
          fechar
        </Botao>
      </div>

      {ordenados.length > LIMITE_DE_VIRTUALIZACAO ? (
        <ListaVirtual
          assets={ordenados}
          assetsBaseUrl={assetsBaseUrl}
          estados={estados}
          marcar={marcar}
          baixar={baixar}
          copiar={copiar}
          selecao={selecao}
          onAlternar={onAlternar}
        />
      ) : (
        <ul className="flex flex-col px-3.5 pb-4">
          {ordenados.map((asset) => (
            <li key={asset.id}>
              <CartaoDeAsset
                asset={asset}
                url={assetUrl(asset, assetsBaseUrl)}
                estado={estados[asset.id] ?? "pronto"}
                marcar={marcar}
                baixar={baixar}
                copiar={copiar}
                selecionado={selecao?.has(asset.id)}
                onAlternar={onAlternar}
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
  readonly selecao?: ReadonlySet<string>;
  readonly onAlternar?: (id: string) => void;
  /**
   * Se `Escape` fecha **este** painel.
   *
   * `false` quando ele está dentro de outro que já trata a tecla: dois
   * ouvintes na mesma tecla fechariam os dois de uma vez, e quem tem chroma
   * aberto perderia o painel do campeão junto.
   */
  readonly fecharComEsc?: boolean;
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
  selecao,
  onAlternar,
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
      // `flex-1 min-h-0` em vez de uma altura fixa: a altura vem do pai, que é
      // a coluna do painel. Uma `70vh` cravada aqui ignoraria a bandeja do lote
      // e a barra de filtros que dividem a mesma tela.
      className="min-h-0 flex-1 overflow-y-auto contain-strict"
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
                selecionado={selecao?.has(asset.id)}
                onAlternar={onAlternar}
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
  readonly selecionado?: boolean;
  readonly onAlternar?: (id: string) => void;
}

function CartaoDeAsset({
  asset,
  url,
  estado,
  marcar,
  baixar,
  copiar,
  selecionado,
  onAlternar,
}: CartaoProps) {
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
    <article
      aria-label={asset.fileName}
      data-tipo={asset.type}
      data-estado={estado}
      className="grid grid-cols-[auto_1fr_auto] items-center gap-x-3 gap-y-1 border-b border-borda py-2.5"
    >
      {onAlternar && (
        <label
          className={cn(
            "grid size-controle-min cursor-pointer place-items-center self-start rounded-tecla border",
            "font-mono text-10",
            selecionado
              ? "border-acento bg-acento text-superficie"
              : "border-borda-fraca text-texto-suave hover:border-acento",
          )}
        >
          {/* O nome acessível vem do `aria-label`, não do texto do rótulo: o
              que está escrito é "✓" ou "+", que não diz nada a quem não vê. */}
          <input
            type="checkbox"
            className="sr-only"
            aria-label={`Selecionar ${asset.fileName}`}
            checked={selecionado ?? false}
            onChange={() => onAlternar(asset.id)}
          />
          <span aria-hidden="true">{selecionado ? "✓" : "+"}</span>
        </label>
      )}
      {!onAlternar && <span />}
      <h3 className="col-start-2 text-13 font-medium text-texto-forte">
        {rotuloDoTipo(asset.type)}
      </h3>
      {/* RNF-02: a prévia é o que responde "é esta arte?" antes de baixar 121 KB.
          `loading="lazy"` porque uma categoria tem centenas de cartões e nem
          todos passam pela tela.

          `<img>` e não `next/image`: a URL é de terceiro e o [ADR 0012] não tem
          storage nem proxy — otimizar exigiria servir os bytes por conta
          própria, que é exatamente o que o projeto decidiu não fazer. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={url}
        alt={`Prévia de ${asset.names.pt_BR}`}
        width={asset.width}
        height={asset.height}
        loading="lazy"
        decoding="async"
        data-previa={asset.type}
        className="col-start-2 row-start-2 max-w-60 rounded-padrao bg-campo"
      />
      {/* RF-09: a ficha aparece antes de qualquer clique de download. */}
      <p className="col-start-2 row-start-3 font-mono text-11 text-texto-suave">
        {assetSummary(asset)}
      </p>

      <div className="col-start-3 row-start-1 row-span-3 flex flex-none flex-col gap-1.5 self-center">
        <Botao
          variante="primario"
          tamanho="md"
          disabled={ocupado}
          onClick={() => void acionar(false)}
        >
          Baixar original
        </Botao>
        <Botao
          tamanho="md"
          disabled={ocupado || !canConvertToPng(asset)}
          onClick={() => void acionar(true)}
        >
          {canConvertToPng(asset) ? "Baixar PNG" : "já é PNG"}
        </Botao>
        <Botao variante="fantasma" tamanho="md" onClick={() => void copiar(url)}>
          Copiar URL
        </Botao>
      </div>

      {estado === "erro" && (
        <p role="alert" className="col-start-2 text-11 text-acento-mais-claro">
          Falhou ao baixar. Tente de novo.
        </p>
      )}
    </article>
  );
}
