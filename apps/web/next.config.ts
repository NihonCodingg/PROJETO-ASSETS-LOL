import type { NextConfig } from "next";

import { cabecalhosDoSite } from "./src/lib/cabecalhos";

/**
 * Se buscadores podem indexar o site. O padrão é **não**: aberto por URL, sem
 * divulgação ([ADR 0016]). É a mesma variável que o layout lê para o
 * `<meta name="robots">` — por isso o `NEXT_PUBLIC_`.
 */
const indexavel = process.env.NEXT_PUBLIC_SITE_INDEXABLE === "true";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async headers() {
    return cabecalhosDoSite({ indexavel });
  },
};

export default nextConfig;
