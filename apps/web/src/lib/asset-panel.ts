/**
 * A ordem em que os tipos aparecem no painel, e por quê.
 *
 * `splash_centered` vem primeiro por ser o maior corte ([ADR 0002]) — é o que a
 * maioria das jornadas da §2 da Spec quer. Depois dele, a ordem desce do maior
 * para o menor e termina nos ícones, que são o que se procura de propósito, não
 * por acaso.
 *
 * Tipo que não está no índice **não aparece**: o painel mostra o que existe, não
 * o que deveria existir (RF-20 morreu com o histórico, mas o princípio fica).
 */
import type { Asset, AssetType } from "@lol-assets/schema";

/**
 * Acima disto o painel vira scroller virtual ([ADR 0011]).
 *
 * O número é a fronteira entre os dois usos do painel: o de um campeão mostra
 * dezenas de cartões e não deve pagar scroller próprio; o de uma categoria
 * mostra 5.042 ícones de perfil e não pode não pagar. 200 fica com folga dos
 * dois lados — o campeão mais carregado do patch tem 18 skins.
 */
export const LIMITE_DE_VIRTUALIZACAO = 200;

export const TYPE_ORDER: readonly AssetType[] = [
  "splash_centered",
  "splash_wide",
  "loading",
  "loading_vintage",
  "tile",
  "chroma",
  "square",
  "passive_icon",
  "ability_icon",
  "item_icon",
  "rune_icon",
  "rune_tree_icon",
  "stat_mod_icon",
  "summoner_spell_icon",
  "profile_icon",
  "emote_icon",
  "ward_icon",
  "map_image",
  "rank_emblem",
];

/**
 * O nome legível de cada tipo, na tela.
 *
 * As palavras vêm do design; **o mapeamento foi corrigido**. O mock entregue em
 * 10/09 rotulava 1280×720 como "corte do cliente" e 1215×717 como "corte
 * centralizado" — o inverso do [ADR 0002], que é medido e reverificado todo dia
 * pelos testes de contrato das fontes. A divergência foi levantada e a decisão
 * foi manter as palavras no tipo certo:
 *
 * | Tipo | Medido | Rótulo |
 * |---|---|---|
 * | `splash_centered` | 1280×720 | Splash — corte centralizado |
 * | `splash_wide` | 1215×717 | Splash — corte do cliente |
 *
 * Tipo sem rótulo cai no próprio nome, que é feio mas honesto — melhor do que
 * sumir da tela porque ninguém lembrou de traduzir.
 */
export const ROTULO_DO_TIPO: Partial<Record<AssetType, string>> = {
  splash_centered: "Splash — corte centralizado",
  splash_wide: "Splash — corte do cliente",
  loading: "Tela de carregamento",
  loading_vintage: "Tela de carregamento — versão antiga",
  tile: "Tile quadrado",
  chroma: "Chroma",
  square: "Ícone do campeão",
  passive_icon: "Ícone da passiva",
  ability_icon: "Ícone de habilidade",
  item_icon: "Ícone do item",
  rune_icon: "Ícone da runa",
  rune_tree_icon: "Ícone da árvore",
  stat_mod_icon: "Ícone de fragmento",
  summoner_spell_icon: "Ícone do feitiço",
  profile_icon: "Ícone de perfil",
  emote_icon: "Emote",
  ward_icon: "Ward skin",
  map_image: "Imagem do mapa",
  rank_emblem: "Emblema de elo",
};

export function rotuloDoTipo(tipo: AssetType): string {
  return ROTULO_DO_TIPO[tipo] ?? tipo;
}

const POSICAO = new Map(TYPE_ORDER.map((tipo, indice) => [tipo, indice]));

/** Tipo desconhecido vai para o fim, em vez de sumir ou quebrar a ordenação. */
function posicaoDe(tipo: AssetType): number {
  return POSICAO.get(tipo) ?? TYPE_ORDER.length;
}

/**
 * Ordena por tipo e, dentro do tipo, por skin — base primeiro.
 *
 * Enquanto o seletor de skin não existe (T-19), o painel de um campeão mostra os
 * assets de todas as skins dele. Agrupar por tipo é o que mantém a promessa do
 * critério: `splash_centered` no topo, e não o square porque o campeão só tem um.
 */
export function orderAssets(assets: readonly Asset[]): Asset[] {
  return [...assets].sort(
    (a, b) =>
      posicaoDe(a.type) - posicaoDe(b.type) ||
      (a.skinNum ?? -1) - (b.skinNum ?? -1) ||
      a.id.localeCompare(b.id),
  );
}

/** Os tipos presentes, na ordem do painel. Nenhum inventado. */
export function availableTypes(assets: readonly Asset[]): AssetType[] {
  return [...new Set(orderAssets(assets).map((asset) => asset.type))];
}
