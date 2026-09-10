/**
 * As duas famílias do design, servidas pelo próprio app.
 *
 * `next/font` baixa os arquivos no build e os serve do nosso domínio: sem
 * requisição ao `fonts.googleapis.com` em tempo de execução, sem *layout shift*
 * e sem um terceiro vendo quem visita. O design carregava por `<link>` porque
 * era um mock; num app Next isso seria uma regressão gratuita.
 *
 * Os pesos são os que o design usa, e nenhum a mais: 400, 500 e 600 na de
 * interface; 400 e 500 na mono.
 */
import { Inter_Tight, JetBrains_Mono } from "next/font/google";

export const fonteInterface = Inter_Tight({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--fonte-interface",
  display: "swap",
});

export const fonteMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--fonte-mono",
  display: "swap",
});
