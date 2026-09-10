/**
 * O zip da seleção, montado no navegador (RF-17).
 *
 * Nenhum servidor próprio entra nisto — é a promessa do [ADR 0005] e a única
 * forma de lote que sobrou depois do [ADR 0012]. Os bytes vêm por `fetch` das
 * URLs das fontes, o zip se monta em memória e o arquivo sai pelo `saveBlob`.
 * Isso funciona porque o CORS das fontes permite **ler** os bytes, não só
 * exibi-los — verificado no ADR 0012 com cinco arquivos de dois hosts.
 *
 * ## Três decisões que valem comentário
 *
 * **`STORE`, não `DEFLATE`.** Tudo que se baixa aqui é JPEG ou PNG, já
 * comprimido. Deflatar de novo gasta CPU do usuário para economizar ~0%.
 *
 * **Falha de um arquivo não derruba o lote.** Numa seleção de 300, abortar por
 * causa de um 404 é hostil. O que falhou vai para `FALHAS.txt` dentro do zip:
 * quem abrir vê o que não veio, em vez de contar 299 e não saber qual sumiu.
 *
 * **Concorrência 4.** É a regra 4 do CLAUDE.md, e ela vale para o navegador pela
 * mesma razão que vale para o indexador: são as mesmas fontes de terceiros. O
 * navegador não deixa mandar `User-Agent` próprio, então a cortesia possível é
 * não abrir trinta conexões de uma vez.
 */
import type { Asset } from "@lol-assets/schema";

import { assetUrl } from "@/lib/asset-file";
import { nomesUnicos } from "@/lib/selecao";

/** Regra 4 do CLAUDE.md: ≤ 4 por host. */
export const CONCORRENCIA = 4;

export interface Progresso {
  readonly feitos: number;
  readonly total: number;
  readonly falhas: number;
}

export interface Falha {
  readonly fileName: string;
  readonly url: string;
  readonly motivo: string;
}

export interface ResultadoDoZip {
  readonly blob: Blob;
  readonly arquivos: number;
  readonly falhas: readonly Falha[];
}

/** O mínimo do JSZip que este módulo usa — o resto entra por injeção nos testes. */
export interface ZipLike {
  file(nome: string, dados: Blob | string): unknown;
  generateAsync(opcoes: { type: "blob"; compression: "STORE" }): Promise<Blob>;
}

export interface MontarDeps {
  /** Injetável para o teste provar que **nenhuma** URL de servidor próprio é tocada. */
  readonly buscar?: (url: string) => Promise<Blob>;
  readonly novoZip?: () => ZipLike;
  readonly onProgresso?: (progresso: Progresso) => void;
  /** Cancelamento: uma seleção de 5.042 arquivos precisa poder ser interrompida. */
  readonly sinal?: AbortSignal;
}

async function buscarDeVerdade(url: string): Promise<Blob> {
  const resposta = await fetch(url);
  if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
  return resposta.blob();
}

async function novoZipDeVerdade(): Promise<ZipLike> {
  // Import dinâmico: o JSZip só é baixado quando alguém monta um lote de
  // verdade. Quem só abre o site e baixa um arquivo não paga por ele.
  const { default: JSZip } = await import("jszip");
  return new JSZip() as unknown as ZipLike;
}

export class ZipCanceladoError extends Error {
  constructor() {
    super("montagem cancelada");
    this.name = "ZipCanceladoError";
  }
}

/**
 * Monta o zip, buscando de 4 em 4 e avisando a cada arquivo pronto.
 *
 * A ordem de entrada no zip é a da seleção, não a de chegada da rede: os nomes
 * são resolvidos antes, e cada resultado vai para a sua posição.
 */
export async function montarZip(
  assets: readonly Asset[],
  assetsBaseUrl?: string,
  deps: MontarDeps = {},
): Promise<ResultadoDoZip> {
  const buscar = deps.buscar ?? buscarDeVerdade;
  const zip = deps.novoZip ? deps.novoZip() : await novoZipDeVerdade();
  const nomes = nomesUnicos(assets);

  const blobs = new Array<Blob | null>(assets.length).fill(null);
  const falhas: Falha[] = [];
  let feitos = 0;
  let proximo = 0;

  async function trabalhar(): Promise<void> {
    for (;;) {
      const indice = proximo;
      proximo += 1;
      if (indice >= assets.length) return;
      if (deps.sinal?.aborted) throw new ZipCanceladoError();

      const asset = assets[indice];
      const url = assetUrl(asset, assetsBaseUrl);
      try {
        blobs[indice] = await buscar(url);
      } catch (erro) {
        falhas.push({
          fileName: nomes.get(asset.id) ?? asset.fileName,
          url,
          motivo: erro instanceof Error ? erro.message : String(erro),
        });
      }
      feitos += 1;
      deps.onProgresso?.({ feitos, total: assets.length, falhas: falhas.length });
    }
  }

  await Promise.all(
    Array.from({ length: Math.min(CONCORRENCIA, assets.length) }, () => trabalhar()),
  );

  let dentro = 0;
  for (let i = 0; i < assets.length; i += 1) {
    const blob = blobs[i];
    if (!blob) continue;
    zip.file(nomes.get(assets[i].id) ?? assets[i].fileName, blob);
    dentro += 1;
  }
  if (falhas.length > 0) zip.file("FALHAS.txt", relatorioDeFalhas(falhas));

  return {
    blob: await zip.generateAsync({ type: "blob", compression: "STORE" }),
    arquivos: dentro,
    falhas,
  };
}

/** O que não veio, e por quê. Vai dentro do zip, em texto puro. */
export function relatorioDeFalhas(falhas: readonly Falha[]): string {
  const linhas = [
    `${falhas.length} ${falhas.length === 1 ? "arquivo não veio" : "arquivos não vieram"}:`,
    "",
    ...falhas.map((falha) => `${falha.fileName}\t${falha.motivo}\t${falha.url}`),
  ];
  return linhas.join("\n") + "\n";
}
