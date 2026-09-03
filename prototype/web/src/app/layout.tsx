import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Protótipo — catálogo de assets",
  description: "Descartável. Valida a regra dos 3 cliques e a conversão PNG no cliente.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
