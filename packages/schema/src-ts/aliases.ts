/**
 * Apelidos de busca, importados em tempo de build pelo `apps/web`.
 *
 * A lista é mantida à mão ([ADR 0009]): acrescentar `"ww": "Warwick"` ao JSON e
 * dar merge já publica o apelido. Não há gerador, não há script, não é preciso
 * rodar o indexador.
 *
 * A chave é o que a pessoa digita **já normalizada** — minúscula, sem acento,
 * sem apóstrofo, só `[a-z0-9]`. O valor é o `id` do campeão no ddragon.
 */
import aliasesJson from "../data/champion-aliases.json";

export const championAliases: Readonly<Record<string, string>> = aliasesJson.aliases;

/** Metadado do arquivo, para a página "Sobre" poder dizer quando foi revisado. */
export const aliasesMetadata = {
  updatedAt: aliasesJson.atualizadoEm,
  validatedAgainstPatch: aliasesJson.validadoContraPatch,
} as const;
