/**
 * Botão — as três variantes que o design usa, e nenhuma a mais.
 *
 * Lendo `docs/design/telas/biblioteca-de-assets-v2.html`, todo botão do arquivo
 * cai num destes três desenhos:
 *
 * - **primário** (`#8b5cf6` com texto `#0b0b0d`): "Baixar .zip", "Baixar
 *   original". É a ação que a tela existe para oferecer, e há no máximo uma por
 *   contexto.
 * - **contorno** (transparente com borda `#27272a`): "Limpar", "Baixar PNG",
 *   fechar, setas de skin. A ação secundária.
 * - **fantasma** (sem borda, ganha fundo no `hover`): item da barra lateral,
 *   `esc` dentro do campo, remover da bandeja.
 *
 * O tamanho é altura, porque é assim que o design pensa: `28 · 30 · 32`, mais o
 * `24` e o `26` dos botões-ícone. Ver a tabela "Altura de controle" no TOKENS.
 */
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export type VarianteDoBotao = "primario" | "contorno" | "fantasma";
export type TamanhoDoBotao = "xs" | "sm" | "md" | "padrao" | "lg";

const VARIANTE: Record<VarianteDoBotao, string> = {
  primario: "bg-acento text-superficie font-semibold hover:bg-acento-claro",
  contorno: "border border-borda-forte text-texto-forte hover:bg-campo",
  fantasma: "text-texto-suave hover:bg-campo hover:text-texto",
};

const TAMANHO: Record<TamanhoDoBotao, string> = {
  xs: "h-controle-xs w-controle-xs justify-center text-11",
  sm: "h-controle-sm w-controle-sm justify-center text-12",
  md: "h-controle-md px-2.5 text-12",
  padrao: "h-controle px-2.5 text-12",
  lg: "h-controle-lg px-2.5 text-12",
};

export interface BotaoProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  readonly variante?: VarianteDoBotao;
  readonly tamanho?: TamanhoDoBotao;
}

export function Botao({
  variante = "contorno",
  tamanho = "padrao",
  className,
  type = "button",
  ...resto
}: BotaoProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex cursor-pointer items-center gap-1.5 rounded-padrao",
        "whitespace-nowrap font-interface",
        // `disabled` precisa parecer desabilitado: um botão que só ignora o
        // clique é indistinguível de um botão quebrado.
        "disabled:cursor-not-allowed disabled:opacity-45",
        VARIANTE[variante],
        TAMANHO[tamanho],
        className,
      )}
      {...resto}
    />
  );
}
