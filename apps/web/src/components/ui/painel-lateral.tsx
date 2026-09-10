"use client";

/**
 * O painel que entra pela direita, sobre Radix Dialog ([ADR 0011]).
 *
 * Este é o único primitivo que justifica a dependência do Radix, e justifica
 * bem: o painel do design é um diálogo modal com véu, e um diálogo modal escrito
 * à mão erra sempre nas mesmas três coisas — o foco não fica preso dentro dele,
 * o fundo continua rolando atrás, e o leitor de tela continua lendo a página
 * embaixo como se ela estivesse acessível.
 *
 * O T-28 já cobre `Escape` e ordem de tabulação por teste. Trocar o `<section>`
 * escrito à mão por este componente é o que faz esses testes passarem por
 * construção em vez de por vigilância.
 */
import * as Dialog from "@radix-ui/react-dialog";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface PainelLateralProps {
  readonly aberto: boolean;
  readonly onFechar: () => void;
  /** Lido por leitor de tela como o nome do diálogo. Obrigatório. */
  readonly titulo: string;
  readonly children: ReactNode;
  readonly className?: string;
}

export function PainelLateral({
  aberto,
  onFechar,
  titulo,
  children,
  className,
}: PainelLateralProps) {
  return (
    <Dialog.Root open={aberto} onOpenChange={(proximo) => !proximo && onFechar()}>
      <Dialog.Portal>
        <Dialog.Overlay
          className="fixed inset-0 z-20"
          style={{ background: "var(--veu)" }}
        />
        <Dialog.Content
          aria-label={titulo}
          className={cn(
            "fixed inset-y-0 right-0 z-25 flex w-[min(540px,74%)] flex-col",
            "border-l border-borda-forte bg-superficie",
            className,
          )}
        >
          {/* O título existe para o leitor de tela mesmo quando a tela mostra
              um cabeçalho próprio: sem ele o Radix avisa no console, e com
              razão — um diálogo sem nome é um diálogo que ninguém anuncia. */}
          <Dialog.Title className="sr-only">{titulo}</Dialog.Title>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

/** O botão de fechar do canto, com o `×` do design. */
export function FecharPainel({ className }: { className?: string }) {
  return (
    <Dialog.Close
      className={cn(
        "grid h-controle-sm w-controle-sm flex-none cursor-pointer place-items-center",
        "rounded-padrao border border-borda-forte font-mono text-12 text-texto-suave",
        "hover:bg-campo hover:text-texto",
        className,
      )}
      aria-label="Fechar"
      title="Fechar (Esc)"
    >
      ×
    </Dialog.Close>
  );
}
