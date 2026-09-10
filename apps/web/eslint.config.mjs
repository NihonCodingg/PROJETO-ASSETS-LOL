import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { FlatCompat } from "@eslint/eslintrc";

import semCorLiteral from "./eslint-regras/sem-cor-literal.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({ baseDirectory: __dirname });

const eslintConfig = [
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts", "playwright-report/**"] },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    // T-34, critério 2: cor literal fora do tema é erro, não observação de
    // revisão. Ver o cabeçalho de `eslint-regras/sem-cor-literal.mjs`.
    files: ["src/**/*.{ts,tsx}"],
    plugins: { design: { rules: { "sem-cor-literal": semCorLiteral } } },
    rules: { "design/sem-cor-literal": "error" },
  },
];

export default eslintConfig;
