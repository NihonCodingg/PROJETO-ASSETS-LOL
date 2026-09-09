/**
 * O que o painel de um campeão mostra, e para qual skin.
 *
 * Os dois níveis do [ADR 0010] encontram-se aqui: a navegação é por campeão, mas
 * os assets são por skin. Trocar de skin no seletor não recarrega nada — a fatia
 * já está em memória, e o que muda é o filtro.
 *
 * **Chroma não é skin.** Ele não aparece na lista de skins nem na grade; sai
 * daqui só quando alguém pede os chromas de uma skin específica (RF-06).
 */
import type { Asset, CatalogChampion, CatalogSkin } from "@lol-assets/schema";

/** Tipos que pertencem ao campeão, não a uma skin. */
export const CHAMPION_SCOPED = new Set(["square", "passive_icon", "ability_icon"]);

export function isChroma(asset: Asset): boolean {
  return asset.type === "chroma";
}

/** Os assets do campeão, que aparecem qualquer que seja a skin escolhida. */
export function championAssets(assets: readonly Asset[]): Asset[] {
  return assets.filter((asset) => CHAMPION_SCOPED.has(asset.type) && !isChroma(asset));
}

/**
 * Os assets de uma skin. Chroma fica de fora — ele tem controle próprio (T-20).
 */
export function skinAssets(assets: readonly Asset[], skinNum: number): Asset[] {
  return assets.filter((asset) => !isChroma(asset) && asset.skinNum === skinNum);
}

/**
 * Os chromas de uma skin, ligados por `parentSkinNum`.
 *
 * A amostra "cor original" da própria skin também vem por aqui: o cdragon a
 * declara com `parentSkinNum` igual ao `skinNum` dela mesma.
 */
export function chromasOf(assets: readonly Asset[], skinNum: number): Asset[] {
  return assets.filter((asset) => isChroma(asset) && asset.parentSkinNum === skinNum);
}

/** O que o painel mostra com uma skin escolhida: o do campeão mais o dela. */
export function panelAssets(assets: readonly Asset[], skinNum: number): Asset[] {
  return [...skinAssets(assets, skinNum), ...championAssets(assets)];
}

/** As skins de um campeão, na ordem do catálogo: a base primeiro. */
export function skinsOf(catalogSkins: readonly CatalogSkin[], champion: CatalogChampion): CatalogSkin[] {
  return catalogSkins
    .filter((skin) => skin.championKey === champion.championKey)
    .sort((a, b) => a.skinNum - b.skinNum);
}

/** A skin base, que é como o painel abre quando ninguém pediu outra. */
export function baseSkin(
  catalogSkins: readonly CatalogSkin[],
  champion: CatalogChampion,
): CatalogSkin | undefined {
  const dele = skinsOf(catalogSkins, champion);
  return dele.find((skin) => skin.isBase) ?? dele[0];
}
