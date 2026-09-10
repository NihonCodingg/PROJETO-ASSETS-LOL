import type { Metadata } from "next";

import { Rodape } from "@/components/rodape";
import { fonteInterface, fonteMono } from "@/lib/fontes";
import { siteConfig } from "@/lib/site-config";

import "./globals.css";

export const metadata: Metadata = {
  title: siteConfig.displayName,
  description: siteConfig.description,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" className={`${fonteInterface.variable} ${fonteMono.variable}`}>
      <body className="min-h-screen">
        {children}
        {/* RF-21: o layout é o único caminho por onde toda página passa. */}
        <Rodape />
      </body>
    </html>
  );
}
