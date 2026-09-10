import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  // O Next resolve `@/` pelo `paths` do tsconfig e transforma o JSX sozinho; o
  // vitest não sabe de nenhum dos dois, e sem isto os testes de componente nem
  // carregam o arquivo.
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  esbuild: { jsx: "automatic" },
  test: {
    // jsdom para os testes de componente do T-15 em diante. Os testes de lógica
    // pura não se importam com o ambiente, e um ambiente só evita a pergunta
    // "por que este arquivo não enxerga o DOM?".
    environment: "jsdom",
    // Só `src/`: os `*.spec.ts` do Playwright vivem em `e2e/` e morreriam
    // aqui, porque `@playwright/test` não roda dentro do vitest.
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    globals: false,
    setupFiles: ["./vitest.setup.ts"],
  },
});
