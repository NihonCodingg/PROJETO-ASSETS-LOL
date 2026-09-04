/**
 * Fixture do contrato, exportada para o front usar nos testes.
 *
 * É um retrato medido do patch 16.17.1: dimensão, formato, canal alfa, bytes e
 * sha256 saíram dos arquivos reais, não de invenção. É ela que permite o T-08
 * andar em paralelo com o indexador — o front tem contra o que programar antes
 * de existir um bucket.
 */
import catalogJson from "../examples/catalog.json";
import indexChampionJson from "../examples/index-champion.json";
import indexItemJson from "../examples/index-item.json";
import indexRuneJson from "../examples/index-rune.json";
import manifestJson from "../examples/manifest.json";

import type { Catalog, IndexManifest, IndexShard } from "./index";

// O TypeScript infere `string` para os campos de enum ao importar JSON; o
// documento já foi validado contra o JSON Schema do lado Python, no
// `test_fixture_de_catalogo_valida` e companhia.
export const exampleManifest = manifestJson as unknown as IndexManifest;
export const exampleCatalog = catalogJson as unknown as Catalog;
export const exampleChampionShard = indexChampionJson as unknown as IndexShard;
export const exampleItemShard = indexItemJson as unknown as IndexShard;
export const exampleRuneShard = indexRuneJson as unknown as IndexShard;

export const examples = {
  manifest: exampleManifest,
  catalog: exampleCatalog,
  shards: {
    champion: exampleChampionShard,
    item: exampleItemShard,
    rune: exampleRuneShard,
  },
} as const;
