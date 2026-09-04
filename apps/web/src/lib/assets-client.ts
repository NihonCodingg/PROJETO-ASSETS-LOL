/**
 * Carga do índice, na ordem do ADR 0010.
 *
 * `manifest.json` → catálogo (sempre) → fatia de assets (**sob demanda**, na
 * primeira vez que um painel abre). A home desenha 173 cartões sem baixar um
 * único registro de asset, que é o que sustenta o RNF-03.
 */
import type { Catalog, IndexManifest, IndexShard } from "@lol-assets/schema";

export type FetchLike = (input: string) => Promise<Response>;

/** O único arquivo de nome fixo no bucket (§9 da Spec). */
export const MANIFEST_FILE = "manifest.json";

export class AssetsFetchError extends Error {
  constructor(
    readonly url: string,
    readonly status: number,
  ) {
    super(`falhou ao buscar ${url}: HTTP ${status}`);
    this.name = "AssetsFetchError";
  }
}

export class AssetsClient {
  #baseUrl: string;
  #fetch: FetchLike;
  /** Memoiza por categoria: a fatia é buscada uma vez por sessão, não por abertura. */
  #shards = new Map<string, Promise<IndexShard>>();

  constructor(baseUrl: string, fetchImpl?: FetchLike) {
    this.#baseUrl = baseUrl.replace(/\/+$/, "");
    this.#fetch = fetchImpl ?? ((input: string) => fetch(input));
  }

  url(path: string): string {
    return `${this.#baseUrl}/${path.replace(/^\/+/, "")}`;
  }

  async loadManifest(): Promise<IndexManifest> {
    return this.#json<IndexManifest>(MANIFEST_FILE);
  }

  /** A projeção de navegação e busca. É o único documento pesado da abertura. */
  async loadCatalog(manifest: IndexManifest): Promise<Catalog> {
    return this.#json<Catalog>(this.#currentVersion(manifest).catalog.url);
  }

  /** Sob demanda. Chamar duas vezes não busca duas vezes. */
  async loadShard(manifest: IndexManifest, category: string): Promise<IndexShard> {
    const existente = this.#shards.get(category);
    if (existente) return existente;

    const shard = this.#currentVersion(manifest).shards.find((s) => s.category === category);
    if (!shard) {
      return Promise.reject(new Error(`a versão atual não tem a fatia ${category}`));
    }
    const promessa = this.#json<IndexShard>(shard.url);
    this.#shards.set(category, promessa);
    return promessa;
  }

  #currentVersion(manifest: IndexManifest): IndexManifest["versions"][number] {
    const versao = manifest.versions.find((v) => v.gameVersion === manifest.currentVersion);
    if (!versao) {
      throw new Error(`o manifesto não traz a versão ${manifest.currentVersion}`);
    }
    return versao;
  }

  async #json<T>(path: string): Promise<T> {
    const url = this.url(path);
    const resposta = await this.#fetch(url);
    if (!resposta.ok) throw new AssetsFetchError(url, resposta.status);
    return (await resposta.json()) as T;
  }
}

/** Idade do índice, para o aviso de índice velho do T-31. */
export function indexAgeHours(manifest: IndexManifest, now: Date = new Date()): number {
  const gerado = Date.parse(manifest.generatedAt);
  return (now.getTime() - gerado) / 3_600_000;
}
