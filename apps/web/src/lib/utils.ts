/**
 * `cn` — o utilitário que o shadcn/ui espera encontrar aqui ([ADR 0011]).
 *
 * `clsx` resolve condicional; `twMerge` resolve conflito. Sem o segundo,
 * `cn("px-2", props.className)` com `px-4` vindo de fora deixa as duas classes
 * no elemento e quem vence é a ordem do CSS gerado, não a intenção de quem
 * chamou.
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...classes: ClassValue[]): string {
  return twMerge(clsx(classes));
}
