/**
 * "A indexação parou" — detectado sem monitoramento (T-31, §11 da Spec).
 *
 * Não há Sentry, não há uptime check, não há ninguém de plantão: o
 * [ADR 0005] escolheu custo de operação zero, e a consequência é que o próprio
 * site precisa ser o alarme. O sintoma de que o workflow quebrou é sempre o
 * mesmo — o `generatedAt` do manifesto para de andar.
 *
 * **O aviso não bloqueia nada.** Índice de três dias atrás continua servindo
 * arte que existe: as URLs são das fontes, e elas não somem porque o nosso
 * workflow caiu. O que o aviso evita é a pessoa achar que está vendo o patch de
 * hoje quando não está.
 */
import type { IndexManifest } from "@lol-assets/schema";

import { indexAgeHours } from "@/lib/assets-client";

/**
 * 72 horas.
 *
 * O workflow roda a cada 6 h (T-13). Doze execuções seguidas sem sucesso não é
 * lentidão da Riot nem atraso do Actions — é coisa quebrada. Um limite mais
 * apertado transformaria fim de semana de fila do Actions em alarme falso, e
 * alarme falso é como se aprende a ignorar alarme.
 */
export const LIMITE_DE_IDADE_HORAS = 72;

export interface Frescor {
  readonly horas: number;
  readonly velho: boolean;
  /** Quando o índice foi gerado, para o aviso mostrar a data. */
  readonly geradoEm: Date;
}

export function medirFrescor(manifest: IndexManifest, agora: Date = new Date()): Frescor {
  const horas = indexAgeHours(manifest, agora);
  return {
    horas,
    velho: horas > LIMITE_DE_IDADE_HORAS,
    geradoEm: new Date(manifest.generatedAt),
  };
}

/** `9 de setembro de 2026 às 21:24` — data legível, não ISO. */
export function dataLegivel(quando: Date): string {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "long",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(quando);
}

/** "3 dias", "5 dias" — a idade em palavras, arredondada para baixo. */
export function idadeEmPalavras(horas: number): string {
  if (horas < 48) return `${Math.floor(horas)} horas`;
  return `${Math.floor(horas / 24)} dias`;
}
