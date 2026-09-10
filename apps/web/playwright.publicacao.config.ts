/**
 * A conferência no navegador (T-43) — **fora da CI**, porque fala com o ddragon e
 * o cdragon de verdade (§10 da Spec: teste que toca a rede não roda em PR).
 *
 *   pnpm -C apps/web conferir:navegador
 *     o build de produção local, servido como http://biblioteca-de-assets.test:3200
 *   URL_PUBLICADA=https://biblioteca-de-assets.vercel.app pnpm -C apps/web conferir:navegador
 *     o site no ar
 *
 * O domínio falso termina em `.test`, reservado para teste. Não em `.app`: o
 * Chromium força HTTPS em `.app` por HSTS pré-carregado, e o servidor local é
 * HTTP. O Chromium resolve o nome para 127.0.0.1 — para as fontes, a origem é
 * um domínio qualquer, e nenhum atalho de `localhost` ajuda. O que o modo local
 * **não** reproduz é o HTTPS; o cenário que depende dele só roda com
 * `URL_PUBLICADA`.
 */
import { defineConfig, devices } from "@playwright/test";

const PUBLICADA = process.env.URL_PUBLICADA?.replace(/\/+$/, "");
const PORTA = 3200;
const LOCAL = `http://biblioteca-de-assets.test:${PORTA}`;

export default defineConfig({
  testDir: "./publicacao",
  timeout: 90_000,
  expect: { timeout: 20_000 },
  // Poucas requisições às fontes, uma de cada vez — o espírito da regra 4.
  workers: 1,
  reporter: "list",

  use: {
    ...devices["Desktop Chrome"],
    baseURL: PUBLICADA ?? LOCAL,
    acceptDownloads: true,
    launchOptions: PUBLICADA
      ? {}
      : { args: ["--host-resolver-rules=MAP biblioteca-de-assets.test 127.0.0.1"] },
  },

  webServer: PUBLICADA
    ? undefined
    : {
        // O build de produção, que é o que a Vercel serve — não o `next dev`.
        command: `pnpm run build && node node_modules/next/dist/bin/next start --port ${PORTA}`,
        url: `http://127.0.0.1:${PORTA}/indice/manifest.json`,
        reuseExistingServer: false,
        timeout: 300_000,
      },
});
