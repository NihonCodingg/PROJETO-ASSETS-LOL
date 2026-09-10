/**
 * Os dois rótulos tipográficos do design.
 *
 * `RotuloDeSecao` é o texto em caixa alta com espacejamento de `0.06em` que
 * abre cada bloco ("CATEGORIAS", "VARIANTES"). `Meta` é a linha de metadado
 * técnico — resolução, formato, bytes, contagem — sempre em mono, porque é
 * assim que o design separa número de linguagem.
 *
 * Os dois usam `texto-suave` e não os cinzas mais escuros do design: ver a
 * decisão de contraste de 10/09 em `docs/design/TOKENS.md`.
 */
import { cn } from "@/lib/utils";

export function RotuloDeSecao({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "font-mono text-10 uppercase tracking-rotulo text-texto-suave",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Meta({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("font-mono text-11 text-texto-suave", className)}>{children}</span>;
}

/** A etiqueta "skin" do canto do cartão (RF-05: skin é resultado de busca). */
export function Etiqueta({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "rounded-min px-1 py-px font-mono text-9 uppercase tracking-rotulo",
        "text-acento-mais-claro",
        className,
      )}
      style={{ background: "var(--etiqueta-skin)" }}
    >
      {children}
    </span>
  );
}
