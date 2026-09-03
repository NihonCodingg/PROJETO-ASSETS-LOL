import type { Metadata } from "next";

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
    <html lang="pt-BR">
      <body className="min-h-screen">
        {children}
        <footer className="border-t border-neutral-800 px-6 py-8 text-xs text-neutral-500">
          {siteConfig.riotLegalNotice}
        </footer>
      </body>
    </html>
  );
}
