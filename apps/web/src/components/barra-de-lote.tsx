"use client";

/**
 * A barra do lote: o que está selecionado, quanto vai custar, e o botão (RF-17).
 *
 * Desde o [ADR 0012] este é o **único** caminho de download em lote. Não há zip
 * por categoria para onde mandar quem selecionou 5.042 ícones, e por isso o
 * aviso aqui **informa em vez de redirecionar**: diz o tamanho e o tempo
 * estimado pela taxa medida, e deixa o botão habilitado. Bloquear seria decidir
 * pela pessoa que ela não quer esperar três minutos.
 *
 * O progresso não é enfeite: a categoria `item` leva ~31 s. Sem barra, meio
 * minuto de nada acontecendo é indistinguível de travado, e a aba fecha.
 *
 * Tela crua de propósito; o design chega no T-30.
 */

import { useCallback, useRef, useState } from "react";

import type { Asset } from "@lol-assets/schema";

import { formatBytes, saveBlob } from "@/lib/asset-file";
import { aviso, duracao, nomeDoZip, resumir } from "@/lib/selecao";
import { montarZip, ZipCanceladoError, type Falha, type Progresso } from "@/lib/zip";

export interface BarraDeLoteProps {
  /** Os assets **selecionados**, já resolvidos. */
  readonly assets: readonly Asset[];
  /** Vira o nome do arquivo: "Jax" → `lol-assets-jax.zip`. */
  readonly rotulo?: string;
  readonly assetsBaseUrl?: string;
  readonly onLimpar: () => void;
  /** Injetáveis, como no `PainelDeAsset`: teste sem mock de módulo. */
  readonly montar?: typeof montarZip;
  readonly salvar?: (blob: Blob, nome: string) => void;
}

type Estado =
  | { fase: "parado" }
  | { fase: "montando"; progresso: Progresso }
  | { fase: "pronto"; arquivos: number; falhas: readonly Falha[] }
  | { fase: "erro"; motivo: string };

export function BarraDeLote({
  assets,
  rotulo,
  assetsBaseUrl,
  onLimpar,
  montar = montarZip,
  salvar = saveBlob,
}: BarraDeLoteProps) {
  const [estado, setEstado] = useState<Estado>({ fase: "parado" });
  const cancelamento = useRef<AbortController | null>(null);

  const baixar = useCallback(async () => {
    const controle = new AbortController();
    cancelamento.current = controle;
    setEstado({ fase: "montando", progresso: { feitos: 0, total: assets.length, falhas: 0 } });
    try {
      const resultado = await montar(assets, assetsBaseUrl, {
        sinal: controle.signal,
        onProgresso: (progresso) => setEstado({ fase: "montando", progresso }),
      });
      salvar(resultado.blob, nomeDoZip(rotulo, resultado.arquivos));
      setEstado({ fase: "pronto", arquivos: resultado.arquivos, falhas: resultado.falhas });
    } catch (erro) {
      if (erro instanceof ZipCanceladoError) setEstado({ fase: "parado" });
      else setEstado({ fase: "erro", motivo: erro instanceof Error ? erro.message : String(erro) });
    } finally {
      cancelamento.current = null;
    }
  }, [assets, assetsBaseUrl, montar, rotulo, salvar]);

  if (assets.length === 0) return null;

  const resumo = resumir(assets);
  const montando = estado.fase === "montando";

  return (
    <section aria-label="Seleção">
      <p>
        {resumo.arquivos} {resumo.arquivos === 1 ? "selecionado" : "selecionados"} ·{" "}
        {formatBytes(resumo.bytes)} · ~{duracao(resumo.segundos)}
      </p>

      {/* Critério 3: acima do limite avisa, e o botão continua habilitado. */}
      {resumo.pesada && <p role="alert">{aviso(resumo)}</p>}

      <button type="button" onClick={() => void baixar()} disabled={montando}>
        Baixar {resumo.arquivos} como zip
      </button>
      <button type="button" onClick={onLimpar} disabled={montando}>
        Limpar seleção
      </button>

      {montando && (
        <div role="status">
          <progress value={estado.progresso.feitos} max={estado.progresso.total} />
          <p>
            {estado.progresso.feitos} de {estado.progresso.total}
          </p>
          <button type="button" onClick={() => cancelamento.current?.abort()}>
            Cancelar
          </button>
        </div>
      )}

      {estado.fase === "pronto" && (
        <p role="status">
          Zip com {estado.arquivos} {estado.arquivos === 1 ? "arquivo" : "arquivos"}.
          {estado.falhas.length > 0 &&
            ` ${estado.falhas.length} não ${estado.falhas.length === 1 ? "veio" : "vieram"} — a lista está no FALHAS.txt dentro do zip.`}
        </p>
      )}

      {estado.fase === "erro" && <p role="alert">Falhou ao montar o zip: {estado.motivo}</p>}
    </section>
  );
}
