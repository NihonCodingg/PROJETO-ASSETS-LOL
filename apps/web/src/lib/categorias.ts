/**
 * Navegação por categoria e filtros (RF-08) — o caminho de quem não sabe o nome.
 *
 * A busca do [ADR 0010] resolve "quero a splash do Jax". Não resolve "quero um
 * ícone de item de bota", porque quem procura assim não tem termo para digitar.
 * É para isso que a categoria existe, e é por isso que ela **não** carrega tudo:
 * cada fatia entra sob demanda, e a home continua com catálogo e mais nada
 * (RNF-03).
 *
 * ## Os grupos de filtro saem dos dados, não de uma lista aqui
 *
 * Um grupo de filtro é a parte antes do `:` de uma `tag` que o T-21 escreveu no
 * índice; a parte depois é a opção. Etiqueta sem `:` — `compravel` — é um grupo
 * de uma opção só. Nada é declarado de antemão: se a fonte parar de trazer
 * `classe:*`, o grupo some da tela sozinho, sem código morto e sem filtro que
 * não filtra nada.
 *
 * ## Rótulo: dado primeiro, tabela só para o vocabulário que é nosso
 *
 * `arvore:8000` vira "Precisão" lendo o nome do próprio `rune_tree_icon` que
 * está na fatia — o dado se explica. A tabela fixa cobre **só** as etiquetas
 * cujo vocabulário o indexador inventou (`mapa:sr`, `arvore:nenhuma`), porque aí
 * traduzir é desfazer um mapeamento nosso, não adivinhar o da Riot. O que sobra
 * aparece cru: `classe:damage` é `damage`, em inglês, como a Riot escreve — e
 * traduzir 30 tags à mão seria inventar rótulo, que é justamente o que este
 * projeto não faz.
 */
import type { Asset, AssetCategory, CatalogChampion } from "@lol-assets/schema";

import { normalize } from "@/lib/search";

export interface Categoria {
  readonly category: AssetCategory;
  readonly rotulo: string;
}

/**
 * As categorias navegáveis, na ordem em que aparecem.
 *
 * `champion` **não** está aqui: a home inteira já é a navegação por campeão
 * ([ADR 0010]), e repeti-la como categoria daria dois caminhos para o mesmo
 * lugar. `rank` também não — saiu da v1 com o [ADR 0012].
 *
 * A lista é de rótulos, não de existência: o que aparece na tela é a interseção
 * disto com as fatias que o manifesto declara. Índice sem emote, botão sem
 * emote.
 */
export const CATEGORIAS: readonly Categoria[] = [
  { category: "item", rotulo: "Itens" },
  { category: "rune", rotulo: "Runas" },
  { category: "summoner_spell", rotulo: "Feitiços" },
  { category: "profile_icon", rotulo: "Ícones de perfil" },
  { category: "emote", rotulo: "Emotes" },
  { category: "ward", rotulo: "Wards" },
  { category: "map", rotulo: "Mapas" },
  { category: "misc", rotulo: "Diversos" },
];

/** Rótulo da categoria, ou a própria chave se ela for nova por aqui. */
export function rotuloDaCategoria(category: string): string {
  return CATEGORIAS.find((c) => c.category === category)?.rotulo ?? category;
}

/** Categorias que o manifesto tem, na ordem de `CATEGORIAS`. */
export function categoriasDisponiveis(shards: readonly { category: string }[]): Categoria[] {
  const tem = new Set(shards.map((s) => s.category));
  return CATEGORIAS.filter((c) => tem.has(c.category));
}

// --- grupos de filtro ------------------------------------------------------------------

export interface Opcao {
  readonly tag: string;
  readonly rotulo: string;
  /** Quantos assets da fatia têm esta etiqueta. Some quando o filtro combina. */
  readonly total: number;
}

export interface GrupoDeFiltro {
  readonly chave: string;
  readonly rotulo: string;
  readonly opcoes: readonly Opcao[];
}

/** Só o vocabulário que o indexador inventou. O resto sai cru, de propósito. */
const ROTULO_FIXO: Record<string, string> = {
  "mapa:sr": "Summoner's Rift",
  "mapa:aram": "ARAM",
  "mapa:arena": "Arena",
  "arvore:nenhuma": "sem árvore",
};

const ROTULO_DO_GRUPO: Record<string, string> = {
  compravel: "Comprável",
  classe: "Classe",
  mapa: "Mapa",
  arvore: "Árvore de runa",
  slot: "Slot da runa",
};

export function grupoDaTag(tag: string): string {
  const corte = tag.indexOf(":");
  return corte === -1 ? tag : tag.slice(0, corte);
}

function valorDaTag(tag: string): string {
  const corte = tag.indexOf(":");
  return corte === -1 ? "sim" : tag.slice(corte + 1);
}

/**
 * Nomes que a própria fatia declara, indexados por `refId`.
 *
 * É o que transforma `arvore:8000` em "Precisão" sem tabela: o ícone da árvore
 * está na mesma fatia das runas, e o nome dele é o nome dela.
 */
function nomesPorRef(assets: readonly Asset[]): Map<string, string> {
  const nomes = new Map<string, string>();
  for (const asset of assets) {
    if (asset.refId && !nomes.has(asset.refId)) nomes.set(asset.refId, asset.names.pt_BR);
  }
  return nomes;
}

export function gruposDeFiltro(assets: readonly Asset[]): GrupoDeFiltro[] {
  const nomes = nomesPorRef(assets);
  const contagem = new Map<string, number>();
  for (const asset of assets) {
    for (const tag of asset.tags ?? []) contagem.set(tag, (contagem.get(tag) ?? 0) + 1);
  }

  const porGrupo = new Map<string, Opcao[]>();
  for (const [tag, total] of contagem) {
    const chave = grupoDaTag(tag);
    const opcoes = porGrupo.get(chave) ?? [];
    opcoes.push({ tag, rotulo: rotuloDaTag(tag, nomes), total });
    porGrupo.set(chave, opcoes);
  }

  return [...porGrupo]
    .map(([chave, opcoes]) => ({
      chave,
      rotulo: ROTULO_DO_GRUPO[chave] ?? chave,
      // Mais frequente primeiro: é a ordem em que o filtro é útil. Empate pela
      // etiqueta, para a tela não dançar entre patches.
      opcoes: [...opcoes].sort((a, b) => b.total - a.total || a.tag.localeCompare(b.tag)),
    }))
    .sort((a, b) => a.rotulo.localeCompare(b.rotulo, "pt-BR"));
}

/** O rótulo de uma etiqueta: tabela, depois dado, depois o valor cru. */
export function rotuloDaTag(tag: string, nomes: ReadonlyMap<string, string> = new Map()): string {
  const fixo = ROTULO_FIXO[tag];
  if (fixo) return fixo;
  const valor = valorDaTag(tag);
  return nomes.get(valor) ?? valor;
}

/**
 * O filtro que a categoria abre marcado.
 *
 * Só `item` tem um, e ele vem da §B.1.6 do KICKOFF: dos 868 ícones de item, a
 * maioria é de modo antigo, missão ou upgrade do Ornn — `purchasable: false` no
 * JSON da Riot. Abrir mostrando tudo entrega uma lista que não se parece com o
 * jogo. O botão "mostrar tudo" desmarca, e aí a lista é literalmente tudo.
 */
export function filtrosPadrao(
  category: AssetCategory,
  grupos: readonly GrupoDeFiltro[],
): Set<string> {
  if (category !== "item") return new Set();
  const existentes = new Set(grupos.flatMap((g) => g.opcoes.map((o) => o.tag)));
  return new Set(["compravel", "mapa:sr"].filter((tag) => existentes.has(tag)));
}

// --- aplicar ---------------------------------------------------------------------------

/**
 * A fatia preparada para filtrar: o texto de cada asset já normalizado.
 *
 * São 5.042 ícones de perfil. Normalizar na hora da consulta refaria 5.042 `NFD`
 * mais regex **a cada tecla**; aqui é uma vez por fatia. Mesmo desenho do
 * `buildSearchIndex` do `search.ts`, pelo mesmo motivo.
 */
export interface ListaDeCategoria {
  readonly assets: readonly Asset[];
  readonly texto: readonly string[];
}

export function prepararLista(assets: readonly Asset[]): ListaDeCategoria {
  return {
    assets,
    texto: assets.map((asset) =>
      normalize(`${asset.names.pt_BR} ${asset.names.en_US ?? ""} ${asset.fileName}`),
    ),
  };
}

/**
 * OU dentro do grupo, E entre grupos.
 *
 * "ARAM ou Arena, **e** comprável" é o que alguém quer dizer ao marcar três
 * caixas. E entre opções do mesmo grupo devolveria vazio quase sempre — um item
 * comprável no SR e no ARAM existe, mas um item que é `classe:boots` e
 * `classe:consumable` não.
 */
export function filtrar(
  lista: ListaDeCategoria,
  tags: ReadonlySet<string>,
  consulta = "",
): Asset[] {
  const exigidas = new Map<string, string[]>();
  for (const tag of tags) {
    const chave = grupoDaTag(tag);
    exigidas.set(chave, [...(exigidas.get(chave) ?? []), tag]);
  }
  const alvo = normalize(consulta.trim());

  const achados: Asset[] = [];
  for (let i = 0; i < lista.assets.length; i += 1) {
    const asset = lista.assets[i];
    if (alvo && !lista.texto[i].includes(alvo)) continue;
    let passa = true;
    for (const grupo of exigidas.values()) {
      if (!grupo.some((tag) => asset.tags?.includes(tag))) {
        passa = false;
        break;
      }
    }
    if (passa) achados.push(asset);
  }
  return achados;
}

/**
 * O que estava filtrado, em palavras — o estado vazio do critério 4.
 *
 * Sem isto, "nenhum resultado" deixa a pessoa sem saber qual das quatro caixas
 * marcadas é a culpada.
 */
export function descreverFiltro(
  tags: ReadonlySet<string>,
  consulta: string,
  grupos: readonly GrupoDeFiltro[] = [],
): string[] {
  const rotulos = new Map(
    grupos.flatMap((g) => g.opcoes.map((o) => [o.tag, `${g.rotulo}: ${o.rotulo}`] as const)),
  );
  const partes = [...tags].sort().map((tag) => rotulos.get(tag) ?? tag);
  if (consulta.trim()) partes.push(`texto: “${consulta.trim()}”`);
  return partes;
}

// --- função do campeão -------------------------------------------------------------------

/**
 * As seis classes que a Riot dá a campeão, em português.
 *
 * Esta é a exceção à regra de não traduzir do topo do arquivo, e a linha é
 * proposital: são **seis** valores, o conjunto é fechado, não muda há mais de
 * dez anos, e o próprio cliente do jogo em pt-BR usa exatamente estas palavras.
 * As ~30 `classe:*` de item não têm nenhuma dessas três propriedades. Valor fora
 * da tabela sai cru, como em todo o resto.
 */
const FUNCOES: Record<string, string> = {
  Assassin: "Assassino",
  Fighter: "Lutador",
  Mage: "Mago",
  Marksman: "Atirador",
  Support: "Suporte",
  Tank: "Tanque",
};

/**
 * As funções presentes no catálogo, com quantos campeões cada uma tem.
 *
 * É o filtro de "função" do RF-08, e é o único dos seis nomeados lá que sobrevive
 * fora das categorias: `lane` nenhuma fonte declara, e `elo` saiu da v1 com o
 * [ADR 0012]. Ver a nota do T-24 nos tickets.
 */
export function funcoesDe(champions: readonly CatalogChampion[]): Opcao[] {
  const contagem = new Map<string, number>();
  for (const champion of champions) {
    for (const tag of champion.tags ?? []) contagem.set(tag, (contagem.get(tag) ?? 0) + 1);
  }
  return [...contagem]
    .map(([tag, total]) => ({ tag, rotulo: FUNCOES[tag] ?? tag, total }))
    .sort((a, b) => a.rotulo.localeCompare(b.rotulo, "pt-BR"));
}

/** OU entre funções: um campeão Lutador/Tanque aparece nas duas. */
export function filtrarCampeoes(
  champions: readonly CatalogChampion[],
  funcoes: ReadonlySet<string>,
): CatalogChampion[] {
  if (funcoes.size === 0) return [...champions];
  return champions.filter((champion) => champion.tags?.some((tag) => funcoes.has(tag)));
}
