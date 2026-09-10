#!/usr/bin/env node
/**
 * Confere uma publicação do site pelo HTTP, sem navegador (T-42, ADR 0016).
 *
 *   node scripts/conferir-publicacao.mjs <url>              sem divulgação (o padrão)
 *   node scripts/conferir-publicacao.mjs <url> --indexavel  no dia de divulgar
 *
 * A CI roda contra o `next start` do build de produção. O dono roda contra a URL
 * da Vercel depois do primeiro deploy — e depois de cada patch novo, porque é
 * este script que descobre se o commit do índice chegou ao ar.
 *
 * Sem dependência nenhuma: o `fetch` do Node 22 basta.
 */
import { readFile } from "node:fs/promises";

const [base, ...opcoes] = process.argv.slice(2);
if (!base) {
  console.error("uso: node scripts/conferir-publicacao.mjs <url> [--indexavel]");
  process.exit(2);
}
const raiz = base.replace(/\/+$/, "");
const indexavel = opcoes.includes("--indexavel");

const falhas = [];

function conferir(ok, oQue, detalhe) {
  console.log(`${ok ? "ok   " : "FALHA"} ${oQue}${!ok && detalhe ? ` — ${detalhe}` : ""}`);
  if (!ok) falhas.push(oQue);
}

async function buscar(caminho, metodo = "GET") {
  return fetch(`${raiz}${caminho}`, { method: metodo, signal: AbortSignal.timeout(20_000) });
}

/** Imutável de verdade: um ano e a palavra `immutable`. */
function imutavel(resposta) {
  const cache = resposta.headers.get("cache-control") ?? "";
  return cache.includes("immutable") && cache.includes("max-age=31536000");
}

/** Revalida sempre: `max-age=0` ou `no-cache`, e nada de `immutable`. */
function revalida(resposta) {
  const cache = resposta.headers.get("cache-control") ?? "";
  return (cache.includes("max-age=0") || cache.includes("no-cache")) && !cache.includes("immutable");
}

function semIndexacao(resposta) {
  return (resposta.headers.get("x-robots-tag") ?? "").includes("noindex");
}

/** O que se espera de toda resposta, conforme o site seja indexável ou não. */
function conferirIndexacao(resposta, oQue) {
  conferir(
    semIndexacao(resposta) === !indexavel,
    `${oQue}: ${indexavel ? "sem" : "com"} X-Robots-Tag noindex`,
    `veio "${resposta.headers.get("x-robots-tag") ?? ""}"`,
  );
}

// --- as páginas ----------------------------------------------------------------------

for (const caminho of ["/", "/sobre"]) {
  const resposta = await buscar(caminho);
  const html = await resposta.text();
  conferir(resposta.ok, `${caminho} responde`, `HTTP ${resposta.status}`);
  // RF-21: os dois avisos da Riot no HTML servido, não só no componente.
  conferir(html.includes('data-aviso="riot"'), `${caminho} tem o aviso do Developer Portal`);
  conferir(html.includes('data-aviso="jibber-jabber"'), `${caminho} tem o aviso do Legal Jibber Jabber`);
  conferir(
    /<meta name="robots" content="noindex/.test(html) === !indexavel,
    `${caminho}: ${indexavel ? "sem" : "com"} <meta name="robots" noindex>`,
  );
  conferirIndexacao(resposta, caminho);
}

// --- o índice ------------------------------------------------------------------------

const status = await buscar("/indice/status.json");
const estado = status.ok ? await status.json() : null;
conferir(estado?.ok === true, "status.json diz ok", `HTTP ${status.status}`);
conferir(revalida(status), "status.json revalida", status.headers.get("cache-control"));

const manifesto = await buscar("/indice/manifest.json");
conferir(manifesto.ok, "manifest.json responde", `HTTP ${manifesto.status}`);
conferir(revalida(manifesto), "manifest.json revalida", manifesto.headers.get("cache-control"));
conferirIndexacao(manifesto, "manifest.json");

if (manifesto.ok) {
  const publicado = await manifesto.json();
  const versao = publicado.versions.find((v) => v.gameVersion === publicado.currentVersion);
  conferir(
    publicado.currentVersion === estado?.gameVersion,
    "manifesto e status falam do mesmo patch",
    `${publicado.currentVersion} × ${estado?.gameVersion}`,
  );

  // HEAD: o que interessa são os cabeçalhos, e a fatia de campeão tem 13 MB.
  for (const documento of [versao.catalog, ...versao.shards]) {
    const resposta = await buscar(`/indice/${documento.url}`, "HEAD");
    conferir(
      resposta.ok && imutavel(resposta),
      `${documento.url} é imutável`,
      `HTTP ${resposta.status}, ${resposta.headers.get("cache-control")}`,
    );
  }

  // O site no ar está no índice do repositório? Se o workflow commitou um patch
  // e o deploy não saiu, é aqui que aparece — ver o plano B do ADR 0016.
  const local = JSON.parse(
    await readFile(new URL("../public/indice/manifest.json", import.meta.url), "utf-8"),
  );
  const localAtual = local.versions.find((v) => v.gameVersion === local.currentVersion);
  conferir(
    versao.catalog.url === localAtual.catalog.url,
    "o site está no mesmo índice do repositório",
    `no ar ${publicado.currentVersion} (${versao.catalog.url}), no clone ` +
      `${local.currentVersion} (${localAtual.catalog.url}). Faça git pull e rode de novo; ` +
      "se persistir, o deploy do último commit do índice não saiu",
  );
}

console.log(
  falhas.length === 0
    ? `\n${raiz}: tudo certo.`
    : `\n${raiz}: ${falhas.length} ${falhas.length === 1 ? "falha" : "falhas"}.`,
);
process.exit(falhas.length === 0 ? 0 : 1);
