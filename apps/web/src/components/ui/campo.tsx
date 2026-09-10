/**
 * Campo de texto e a tecla (`kbd`) que aparece dentro dele.
 *
 * O `caret-acento` não é enfeite: no design o cursor do campo é violeta, e é o
 * único sinal de que o campo tem foco quando o anel de `:focus-visible` não
 * aparece — porque quem clicou com o mouse não recebe anel.
 */
import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export type CampoProps = InputHTMLAttributes<HTMLInputElement>;

export function Campo({ className, ...resto }: CampoProps) {
  return (
    <input
      className={cn(
        "h-controle-lg w-full rounded-padrao border border-borda-forte bg-campo",
        "font-interface text-13 text-texto caret-acento",
        "placeholder:text-texto-suave focus:border-acento",
        className,
      )}
      {...resto}
    />
  );
}

/** A tecla desenhada, como no campo de busca (`/`) e na paleta (`esc`). */
export function Tecla({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <kbd
      className={cn(
        "rounded-tecla border border-borda-tecla bg-campo-alto px-1.25 py-px",
        "font-mono text-10 text-texto-suave",
        className,
      )}
    >
      {children}
    </kbd>
  );
}
