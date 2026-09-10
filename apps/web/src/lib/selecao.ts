/**
 * Seleção múltipla e o orçamento honesto do lote (RF-17, RF-18).
 *
 * Desde o [ADR 0012] este é o **único** caminho de lote que existe: não há zip
 * por categoria pré-gerado para onde empurrar quem selecionou demais. O aviso,
 * então, tem que informar em vez de redirecionar — dizer quanto tempo vai
 * demorar e deixar a pessoa decidir, porque a alternativa é ela não baixar nada.
 *
 * O número que sustenta a estimativa é medido, não chutado: **~28 arquivos/s**,
 * do teste com bytes de terceiros do ADR 0012 (§6.1 da Spec). É o que põe a
 * categoria `item` (868 arquivos) em ~31 s.
 */
import type { Asset } from "@lol-assets/schema";

import { formatBytes } from "@/lib/asset-file";

/** §6.1 da Spec. Acima disto a UI avisa — e só avisa. */
export const LIMITE_DE_ARQUIVOS = 300;
export const LIMITE_DE_BYTES = 500 * 1024 * 1024;

/** Medido no teste do [ADR 0012]: 5 arquivos de dois hosts em 1,5 s. */
export const ARQUIVOS_POR_SEGUNDO = 28;

export interface ResumoDaSelecao {
  readonly arquivos: number;
  readonly bytes: number;
  /** Estimativa pela taxa medida, arredondada para cima. */
  readonly segundos: number;
  readonly pesada: boolean;
}

export function resumir(assets: readonly Asset[]): ResumoDaSelecao {
  const bytes = assets.reduce((total, asset) => total + asset.bytes, 0);
  return {
    arquivos: assets.length,
    bytes,
    segundos: Math.ceil(assets.length / ARQUIVOS_POR_SEGUNDO),
    pesada: assets.length > LIMITE_DE_ARQUIVOS || bytes > LIMITE_DE_BYTES,
  };
}

/** "31 s", "3 min 35 s". Segundo nenhum é escondido para parecer mais rápido. */
export function duracao(segundos: number): string {
  if (segundos < 60) return `${segundos} s`;
  const minutos = Math.floor(segundos / 60);
  const resto = segundos % 60;
  return resto === 0 ? `${minutos} min` : `${minutos} min ${resto} s`;
}

/** O texto do aviso do critério 3, com o tempo e o tamanho. */
export function aviso(resumo: ResumoDaSelecao): string {
  return (
    `${resumo.arquivos} arquivos, ${formatBytes(resumo.bytes)}. ` +
    `A montagem acontece no seu navegador e deve levar cerca de ${duracao(resumo.segundos)}, ` +
    `com tudo isso em memória. Dá para continuar.`
  );
}

// --- nomes dentro do zip -----------------------------------------------------------------

/**
 * Um nome por asset, sem colisão.
 *
 * `zip.file()` **sobrescreve em silêncio** um nome repetido: 300 selecionados
 * virariam 299 arquivos sem erro nenhum, e ninguém contaria. Os `fileName` do
 * índice são únicos hoje, e este mapa é o que garante que continuem sendo mesmo
 * quando não forem.
 */
export function nomesUnicos(assets: readonly Asset[]): Map<string, string> {
  const usados = new Set<string>();
  const nomes = new Map<string, string>();
  for (const asset of assets) {
    let nome = asset.fileName;
    if (usados.has(nome)) {
      const ponto = asset.fileName.lastIndexOf(".");
      const base = ponto === -1 ? asset.fileName : asset.fileName.slice(0, ponto);
      const extensao = ponto === -1 ? "" : asset.fileName.slice(ponto);
      let n = 2;
      while (usados.has(`${base} (${n})${extensao}`)) n += 1;
      nome = `${base} (${n})${extensao}`;
    }
    usados.add(nome);
    nomes.set(asset.id, nome);
  }
  return nomes;
}

/**
 * Acentos combinantes, escritos por escape.
 *
 * Mesma classe do `normalize` da busca; escrita em `\u` porque o intervalo
 * literal é invisível num diff, e um caractere perdido não daria erro — daria nome
 * de arquivo errado, em silêncio.
 */
const DIACRITICOS = /[\u0300-\u036f]/g;

/** `lol-assets-jax-16.18.1.zip`. Sem rótulo, o número de arquivos serve. */
export function nomeDoZip(rotulo: string | undefined, quantos: number): string {
  const limpo = (rotulo ?? "")
    .normalize("NFD")
    .replace(DIACRITICOS, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `lol-assets-${limpo || `selecao-${quantos}`}.zip`;
}

// --- a seleção ---------------------------------------------------------------------------

/** Alterna um id. Seleção é conjunto: clicar duas vezes desmarca. */
export function alternar(selecao: ReadonlySet<string>, id: string): Set<string> {
  const proxima = new Set(selecao);
  if (!proxima.delete(id)) proxima.add(id);
  return proxima;
}

/** Os assets selecionados, na ordem em que a lista os mostra. */
export function selecionados(
  assets: readonly Asset[],
  selecao: ReadonlySet<string>,
): Asset[] {
  return assets.filter((asset) => selecao.has(asset.id));
}

/**
 * "Tudo deste campeão" (RF-18).
 *
 * Chroma entra **se estiver revelado**, e não entra se não estiver: o RF-06 diz
 * que chroma não aparece sem alguém pedir, e uma seleção que arrasta 43 chromas
 * escondidos junto é a mesma surpresa que o RF-06 evita na tela. Quem abriu o
 * controle de chromas pediu; quem não abriu, não.
 */
export function tudoDo(assets: readonly Asset[], comChromas: boolean): Set<string> {
  return new Set(
    assets.filter((asset) => comChromas || asset.type !== "chroma").map((asset) => asset.id),
  );
}
