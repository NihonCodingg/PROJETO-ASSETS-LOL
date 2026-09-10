"use client";

/**
 * O aviso de índice velho (T-31).
 *
 * Discreto de propósito, e `role="status"` em vez de `role="alert"`: não é uma
 * emergência que interrompe quem está no meio de baixar uma splash — é uma
 * informação que precisa estar na tela para quem for olhar. Leitor de tela
 * anuncia sem cortar o que estava sendo lido.
 *
 * Tela crua de propósito; o design chega no T-30.
 */

import type { IndexManifest } from "@lol-assets/schema";

import { dataLegivel, idadeEmPalavras, medirFrescor } from "@/lib/frescor";

export interface AvisoDeIndiceVelhoProps {
  readonly manifest: IndexManifest;
  /** Injetável para o teste não depender do relógio da máquina. */
  readonly agora?: Date;
}

export function AvisoDeIndiceVelho({ manifest, agora }: AvisoDeIndiceVelhoProps) {
  const frescor = medirFrescor(manifest, agora);
  if (!frescor.velho) return null;

  return (
    <p
      role="status"
      data-indice="velho"
      className="flex-none border-b border-borda bg-acento-suave px-3.5 py-2 text-11 leading-cartao text-texto-medio"
    >
      Este índice foi gerado há {idadeEmPalavras(frescor.horas)}, em{" "}
      <time dateTime={manifest.generatedAt}>{dataLegivel(frescor.geradoEm)}</time>. A
      indexação automática pode ter parado — o que está aqui continua funcionando, mas pode
      não ser o patch mais recente.
    </p>
  );
}
