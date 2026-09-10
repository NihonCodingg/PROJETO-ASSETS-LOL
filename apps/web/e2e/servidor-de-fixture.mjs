/**
 * O "bucket" do e2e: índice e imagens, servidos de outra origem.
 *
 * **Outra origem de propósito.** Em produção o app e as imagens nunca são o
 * mesmo host: os bytes vêm do ddragon e do cdragon. Servir a fixture de
 * `127.0.0.1:4321` enquanto o app está em `localhost:3000` reproduz isso, e é o
 * que faz o teste do RF-11 valer alguma coisa — sem CORS aberto o canvas fica
 * *tainted* e o `toBlob` falha, que é exatamente a hipótese do [ADR 0001].
 *
 * Sem dependência nenhuma: `node:http` e `node:fs`. Uma biblioteca de servidor
 * estático aqui seria uma dependência a mais para fazer trinta linhas.
 */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = fileURLToPath(new URL("./fixture/", import.meta.url));
const PORTA = Number(process.env.PORTA_DA_FIXTURE ?? 4321);

const TIPOS = {
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
};

const servidor = createServer(async (requisicao, resposta) => {
  // O ADR 0001 inteiro depende disto: sem `*`, o `fetch` do cliente não lê os
  // bytes e não há conversão para PNG nem zip no navegador.
  resposta.setHeader("Access-Control-Allow-Origin", "*");

  const caminho = new URL(requisicao.url ?? "/", "http://x").pathname;
  // `..` num caminho de URL é o bug clássico de servidor estático. Aqui ele não
  // vale nada, mas um servidor que sai da raiz é um hábito ruim de qualquer jeito.
  const destino = normalize(join(RAIZ, decodeURIComponent(caminho)));
  if (!destino.startsWith(RAIZ.split("/").join(sep))) {
    resposta.writeHead(403).end("fora da raiz");
    return;
  }

  try {
    const conteudo = await readFile(destino);
    resposta.writeHead(200, {
      "Content-Type": TIPOS[extname(destino).toLowerCase()] ?? "application/octet-stream",
      "Content-Length": conteudo.byteLength,
      "Cache-Control": "no-store",
    });
    resposta.end(conteudo);
  } catch {
    resposta.writeHead(404).end("não encontrado");
  }
});

servidor.listen(PORTA, "127.0.0.1", () => {
  console.log(`fixture em http://127.0.0.1:${PORTA}/`);
});
