/**
 * O que o `tsc` precisa saber e o Next só conta depois de rodar.
 *
 * O `next-env.d.ts` saiu do controle de versão no T-35: o `next dev` acrescenta
 * sozinho uma linha apontando para `.next/types/routes.d.ts`, e `.next/` é
 * gerado e ignorado — commitar essa linha faz a CI, que roda de um clone limpo,
 * falhar procurando um arquivo que não existe lá. O Next reescreve o arquivo em
 * todo `dev` e todo `build`, então nada se perde.
 *
 * O que sobra é isto: as declarações que o `tsc` da CI precisa sem os tipos
 * gerados. Hoje é uma só.
 */

declare module "*.css";
