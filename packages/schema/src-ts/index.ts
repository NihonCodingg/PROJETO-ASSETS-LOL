/**
 * Contrato do índice de assets, lado TypeScript.
 *
 * O JSON Schema em `schemas/` é a fonte de verdade; os tipos abaixo são
 * escritos à mão por enquanto e passam a ser gerados no ticket da etapa 6.
 */
export const SCHEMA_VERSION = "1.1.0";

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

export interface LocalizedName {
  pt_BR: string;
  en_US?: string;
}

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
  names: LocalizedName;
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

/**
 * Catálogo — as duas projeções que o front carrega antes de qualquer asset.
 * Navegação opera em `champions` (173); busca opera em `skins` (2.149). Ver ADR 0010.
 */
export interface CatalogChampion {
  championKey: number;
  championId: string;
  names: LocalizedName;
  title?: LocalizedName;
  tags?: string[];
  aliases?: string[];
  /** Exibido no cartão da grade. Conta skins, não chromas. */
  skinCount: number;
  chromaCount?: number;
  baseSkinId: number;
  thumbnailKey?: string;
  thumbnailUrl?: string;
}

export interface CatalogSkin {
  skinId: number;
  skinNum: number;
  /** Junção com CatalogChampion — o rótulo do campeão no resultado vem daqui. */
  championKey: number;
  names: LocalizedName;
  isBase: boolean;
  chromaCount?: number;
  thumbnailKey?: string;
  thumbnailUrl?: string;
}

export interface Catalog {
  schemaVersion: string;
  gameVersion: string;
  generatedAt: string;
  assetsBaseUrl?: string;
  champions: CatalogChampion[];
  skins: CatalogSkin[];
}

/** Carregada sob demanda, não na abertura do site (ADR 0010). */
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
    catalog: {
      url: string;
      champions: number;
      skins: number;
      bytes: number;
      sha256?: string;
    };
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
