/**
 * `cn` — o utilitário que o shadcn/ui espera encontrar aqui ([ADR 0011]).
 *
 * `clsx` resolve condicional; `twMerge` resolve conflito. Sem o segundo,
 * `cn("px-2", props.className)` com `px-4` vindo de fora deixa as duas classes
 * no elemento e quem vence é a ordem do CSS gerado, não a intenção de quem
 * chamou.
 *
 * ## Por que o `twMerge` precisa ser ensinado
 *
 * Os tamanhos de texto do design são `text-9` … `text-19`, e o `tailwind-merge`
 * não tem como saber que `text-12` é **tamanho** e `text-superficie` é **cor** —
 * os dois começam com `text-`. Sem a configuração abaixo ele trata os dois como
 * o mesmo grupo e descarta o primeiro.
 *
 * O sintoma foi exatamente este: o botão primário perdeu `text-superficie`,
 * herdou o branco do corpo e passou a ter **3,1:1** de contraste sobre o violeta
 * em vez de 4,64:1. Nenhum teste de unidade pegou — quem pegou foi o axe do
 * T-28, no e2e, porque só ali as classes viram cor de verdade.
 */
import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [{ text: ["9", "10", "11", "12", "13", "14", "19"] }],
    },
  },
});

export function cn(...classes: ClassValue[]): string {
  return twMerge(clsx(classes));
}
