import { siteConfig } from "@/lib/site-config";

export default function HomePage() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-24">
      <h1 className="text-3xl font-semibold">{siteConfig.name}</h1>
      <p className="text-neutral-400">{siteConfig.description}</p>
      <p className="text-sm text-neutral-500">
        Esqueleto do app. A busca chega com os tickets da etapa 6.
      </p>
    </main>
  );
}
