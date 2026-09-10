/**
 * Os cabeçalhos HTTP que o site controla (§9 da Spec, [ADR 0016]).
 *
 * Moram aqui, e não direto no `next.config.ts`, para serem testáveis: o config
 * lê a variável de ambiente na carga do módulo, e o teste precisa das duas
 * versões — indexável e não.
 *
 * ## Cache do índice
 *
 * Catálogo e fatias têm o **hash do conteúdo no nome**
 * (`catalog-c63d0024187c.json`): o mesmo nome nunca tem outro conteúdo, então o
 * navegador guarda para sempre sem perguntar de novo. É o que faz a segunda
 * visita não revalidar os 13 MB da fatia de campeão.
 *
 * `manifest.json` e `status.json` têm nome fixo e **sempre revalidam**. A §9
 * pedia 5 min de cache com um dia de `stale-while-revalidate`, e na Vercel isso
 * quebra: cada deploy é atômico e **apaga** os arquivos com hash do deploy
 * anterior. Um manifesto velho servido do cache aponta para fatias que já não
 * existem — 404 na primeira categoria aberta. Revalidar custa um 304 de 2,5 KB.
 *
 * ## Sem divulgação
 *
 * O site é aberto por URL e não é divulgado (decidido em 10/09/2026). Enquanto
 * `indexavel` for falso, toda resposta leva `X-Robots-Tag` — inclusive os JSON
 * do índice, que o `<meta name="robots">` do HTML não alcança.
 */

export const CACHE_IMUTAVEL = "public, max-age=31536000, immutable";
export const CACHE_REVALIDAR = "public, max-age=0, must-revalidate";
export const SEM_INDEXACAO = "noindex, nofollow";

/**
 * Nome com hash do conteúdo, como o indexador escreve.
 *
 * Exportado cru porque o teste o confere contra os arquivos de `public/indice`:
 * se o indexador passar a escrever outro formato de nome, o teste acusa antes de
 * um arquivo novo cair no cache padrão sem ninguém ver.
 */
export const NOME_COM_HASH = "(?:catalog|index-[a-z_]+)-[0-9a-f]+\\.json";
export const NOME_FIXO = "(?:manifest|status)\\.json";

export interface Cabecalho {
  readonly key: string;
  readonly value: string;
}

export interface RegraDeCabecalho {
  readonly source: string;
  readonly headers: Cabecalho[];
}

export function cabecalhosDoSite({ indexavel }: { indexavel: boolean }): RegraDeCabecalho[] {
  const regras: RegraDeCabecalho[] = [
    {
      source: `/indice/:arquivo(${NOME_COM_HASH})`,
      headers: [{ key: "Cache-Control", value: CACHE_IMUTAVEL }],
    },
    {
      source: `/indice/:arquivo(${NOME_FIXO})`,
      headers: [{ key: "Cache-Control", value: CACHE_REVALIDAR }],
    },
  ];
  if (!indexavel) {
    regras.push({ source: "/:caminho*", headers: [{ key: "X-Robots-Tag", value: SEM_INDEXACAO }] });
  }
  return regras;
}
