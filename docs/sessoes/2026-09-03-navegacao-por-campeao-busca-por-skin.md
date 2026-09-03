# Sessão 03/09/2026 — correção do modelo: navegação por campeão, busca por skin

Correção de escopo vinda do dono do projeto. O ADR 0008 tinha concluído que "a unidade do
catálogo é a skin, 2.149 entradas, não 173". Isso está certo para **busca** e errado para
**navegação**.

## O que foi feito

### ADR 0010 (novo) e ADR 0008 (emendado)

[`docs/adr/0010-navegacao-por-campeao-busca-por-skin.md`](../adr/0010-navegacao-por-campeao-busca-por-skin.md)
registra o modelo híbrido e **por que** as duas superfícies operam em níveis diferentes:

| Superfície | Unidade | Entradas |
|---|---|---:|
| Navegação (grade padrão) | campeão | 173 |
| Busca | skin, e também campeão | 2.149 |
| Painel do campeão | skin | as do campeão |

Com as regras que faltavam: um campeão casado aparece **uma** vez (não 18); clicar num
resultado de skin abre o painel do campeão **já com aquela skin selecionada**.

O ADR 0008 não foi apagado nem reescrito — ganhou cabeçalho de emenda e os itens 2 e 3
riscados com o apontamento para o 0010. O diagnóstico dele continua válido; foi a
conclusão que passou do ponto.

### A regra dos 3 cliques fecha exatamente

| Caminho | Cliques |
|---|---|
| Buscar "deus da guerra" → skin → baixar | 2 |
| Buscar "jax" → campeão → baixar asset de campeão | 2 |
| Buscar "jax" → campeão → escolher skin → baixar | 3 |
| Navegar sem digitar → campeão → escolher skin → baixar | 3 |

Buscar pelo nome da skin é o atalho que pula o seletor. É por isso que o nível de skin na
busca não é enfeite: é o que mantém o caminho longo dentro do orçamento.

### Contrato: 1.0.0 → 1.1.0

A correção obrigou uma mudança no contrato, e ela **melhora** a carga inicial.

Documento novo: `packages/schema/schemas/catalog.schema.json`, com `champions[]` (173) e
`skins[]` (2.149) e **nenhum asset**. O manifesto passa a exigir `catalog` em cada versão.
A fatia de assets deixa de ser o documento de entrada e passa a ser carregada **sob
demanda**, na primeira abertura de painel.

Motivo: derivar as duas projeções de uma fatia com ~10 mil registros de asset significava
baixar ~1 MB comprimido para desenhar 173 cartões. Com o catálogo, a carga inicial cai para
a casa das dezenas de KB e a busca fica disponível antes de qualquer asset.

Também atualizados: modelos e caminhos no pacote Python, tipos TypeScript (`Catalog`,
`CatalogChampion`, `CatalogSkin`, `LocalizedName`) e o README do pacote.

**Três testes novos**, um deles negativo: catálogo válido, skin sem `championKey` rejeitada,
e manifesto sem `catalog` rejeitado. Suíte Python foi de 8 para **12 testes**.

### Spec

- **RF-04** e **RF-05** reescritos; **RF-24** (busca transversal, "K/DA" e "Prestígio") e
  **RF-25** (seletor de skin no painel do campeão) acrescentados **no fim** da numeração,
  de propósito, para não invalidar as referências já feitas em `TICKETS.md`.
- **RNF-03** trocado: era "fatia `champion` < 1,5 MB"; virou "catálogo ≤ 150 KB comprimido
  na abertura, fatia de assets ≤ 1,5 MB e sob demanda".
- Novo job **J7** ("skins K/DA de vários campeões").
- Diagramas de arquitetura e de consulta atualizados; §6, §6.1, §8 e §9 reescritos nos
  trechos afetados; rastreabilidade do ADR 0010 acrescentada.

### Tickets

Sete tickets ajustados, **nenhum criado ou removido**: T-04, T-07, T-08, T-10, T-14, T-19
e T-20. O mais afetado é o T-19, que deixa de ser "catálogo de skins" e passa a ser "grade
de campeões e painel com seletor de skin". T-07 ganha a projeção do catálogo já no
esqueleto andante, para o caminho fino continuar sendo fino de ponta a ponta.

## O que foi assumido

- **"K/DA" e "Prestígio" funcionam sem campo novo.** Os nomes das skins já contêm os
  termos, e a normalização do ADR 0009 (que remove a barra e o acento) faz `kda` casar
  "K/DA Ahri" e `prestigio` casar "Edição Prestígio". Não acrescentei um campo `skinLine`:
  seria duplicar dado que já existe no nome. Se aparecer linha de skin cujo nome não a
  contenha, aí sim vira ticket.
- **Numeração incremental, não renumeração.** RF-24 e RF-25 entram no fim porque renumerar
  invalidaria referências já escritas nos 33 tickets. Está dito no cabeçalho da Spec.
- **Um arquivo de assets, não 173.** Considerei publicar uma fatia por campeão; troca uma
  requisição por até 173 e complica invalidação sem ganho real. Está nas alternativas
  descartadas do ADR.
- **1.1.0, não 2.0.0.** A adição de `catalog` é obrigatória no manifesto, o que tecnicamente
  quebra o 1.0.0 — mas o 1.0.0 nunca foi publicado e nada o consome. Registrado no ADR.

## Verificação

- Python: ruff, `ruff format --check`, mypy strict e **12 testes** verdes.
- Web: eslint, tsc nos dois pacotes e 3 testes verdes.
- Script de conferência: 33 tickets sem duplicata, **todos os 25 RF e 12 RNF cobertos**,
  nenhum link relativo quebrado em SPEC, TICKETS e ADRs.

## O que ficou pendente

Nada desta correção. As decisões abertas seguem as mesmas: **D1**, **D2**, **D4**, **D5**,
**D6** e **D7** da §13 da Spec.

## Próximo passo sugerido

O mesmo de antes: aprovar a lista de tickets e liberar a **Onda 0** (T-02 → T-01).
