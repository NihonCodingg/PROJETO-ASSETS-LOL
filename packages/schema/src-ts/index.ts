/**
 * Contrato do índice de assets, lado TypeScript.
 *
 * O JSON Schema em `schemas/` é a fonte de verdade; os tipos abaixo são
 * escritos à mão por enquanto e passam a ser gerados no ticket da etapa 6.
 */
export const SCHEMA_VERSION = "1.0.0";

export type AssetCategory =
  | "champion"
  | "item"
  | "profile_icon"
  | "rune"
  | "summoner_spell"
  | "emote"
  | "ward"
  | "map"
  | "rank"
  | "misc";

/** Nomes canônicos do ADR 0002 — nunca os nomes das fontes. */
export type AssetType =
  | "square"
  | "splash_centered"
  | "splash_wide"
  | "loading"
  | "loading_vintage"
  | "tile"
  | "chroma"
  | "ability_icon"
  | "passive_icon"
  | "item_icon"
  | "profile_icon"
  | "rune_icon"
  | "rune_tree_icon"
  | "stat_mod_icon"
  | "summoner_spell_icon"
  | "emote_icon"
  | "ward_icon"
  | "map_image"
  | "rank_emblem";

export type AssetSource = "ddragon" | "cdragon" | "riot_static" | "wiki";

export interface Asset {
  id: string;
  type: AssetType;
  category: AssetCategory;
  championKey?: number;
  championId?: string;
  skinId?: number;
  skinNum?: number;
  isBaseSkin?: boolean;
  parentSkinNum?: number;
  itemId?: number;
  refId?: string;
  names: { pt_BR: string; en_US?: string };
  aliases?: string[];
  tags?: string[];
  source: AssetSource;
  sourceUrl: string;
  /** Ausente em versões sem assets copiados: use `sourceUrl`. */
  storageKey?: string;
  fileName: string;
  width: number;
  height: number;
  format: "png" | "jpeg";
  /** Quando true, o asset nunca pode ser convertido para JPEG (ADR 0001). */
  hasAlpha: boolean;
  bytes: number;
  sha256: string;
}

export interface IndexShard {
  schemaVersion: string;
  gameVersion: string;
  category: AssetCategory;
  generatedAt: string;
  assetsBaseUrl?: string;
  assets: Asset[];
}

export interface IndexManifest {
  schemaVersion: string;
  generatedAt: string;
  assetsBaseUrl?: string;
  currentVersion: string;
  versions: Array<{
    gameVersion: string;
    indexedAt: string;
    assetsCopied: boolean;
    totalAssets?: number;
    totalBytes?: number;
    shards: Array<{
      category: string;
      url: string;
      assets: number;
      bytes: number;
      sha256?: string;
    }>;
    zips?: Array<{
      category: string;
      url: string;
      bytes: number;
      assets?: number;
      sha256?: string;
    }>;
  }>;
}
