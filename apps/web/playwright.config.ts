/**
 * O e2e do T-29: o fluxo inteiro, contado em cliques e em milissegundos.
 *
 * Dois servidores, e os dois são de propósito:
 *
 * - `next dev` em 3000 é o app;
 * - `e2e/servidor-de-fixture.mjs` em 4321 é o "bucket", **de outra origem**,
 *   como o ddragon é em produção. É isso que faz o teste de conversão para PNG
 *   provar alguma coisa: sem CORS aberto o canvas fica *tainted*.
 *
 * `next dev` e não `next build && next start` porque o que se testa aqui é
 * comportamento, não bundle — e o `dev` sobe em segundos.
 */
import { defineConfig, devices } from "@playwright/test";

const APP = "http://localhost:3000";
const FIXTURE = "http://127.0.0.1:4321";

export default defineConfig({
  testDir: "./e2e",
  // Um teste de fluxo que passa em 30 s e falha em 60 é um teste que está
  // medindo a máquina, não o produto. O RNF-02 pede 1 s para a prévia.
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI ? [["github"], ["list"]] : "list",

  use: {
    baseURL: APP,
    trace: "on-first-retry",
    // O download de verdade é metade do que este ticket prova (critério 2).
    acceptDownloads: true,
  },

  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],

  webServer: [
    {
      command: "node e2e/servidor-de-fixture.mjs",
      url: `${FIXTURE}/indice/manifest.json`,
      reuseExistingServer: !process.env.CI,
      stdout: "pipe",
    },
    {
      command: "pnpm exec next dev --port 3000",
      url: APP,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        // O app aponta para o bucket de fixture em vez do índice publicado.
        NEXT_PUBLIC_INDEX_BASE_URL: `${FIXTURE}/indice`,
      },
    },
  ],
});
