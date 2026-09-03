# ADR 0008 — O catálogo é de skins, não de campeões

- **Status:** aceito
- **Data:** 2026-09-03
- **Evidência:** [SPIKES](../SPIKES.md) — S3; protótipo do bloco 3

## Contexto

O protótipo mostrou o campeão e, dele, apenas a **skin base**. O fluxo custou 2 cliques —
uma folga sobre a regra dos 3 cliques (§A.4 item 2).

Mas o job to be done da §A.2 não é "preciso do Jax": é *"preciso da splash da skin Jax Deus
da Guerra em alta pra thumbnail"*. Um catálogo de 173 campeões não atende isso; obriga o
usuário a achar o campeão e depois caçar a skin. E os números do S3 mostram a diferença de
escala: **2.149 skins** e **7.037 chromas** contra 173 campeões.

## Decisão

1. **O seletor de skin entra na v1.** A folga do terceiro clique é gasta nele.
2. **A unidade do catálogo é a skin**, não o campeão. Busca, resultados, filtros e índice
   trabalham com ~2.149 entradas.
3. O campeão continua existindo como **agrupamento e como termo de busca**: buscar "jax"
   traz todas as skins de Jax, com a base primeiro.
4. **Chromas não são entradas de primeiro nível.** São 7.037 e poluiriam qualquer
   resultado. Ficam dentro da skin-mãe, atrás de um toggle, ligados por `parentSkinNum`.
5. Fluxo de referência, dentro do orçamento de 3 cliques:
   digitar (0) → clicar na skin (1) → clicar em baixar (2). O seletor de skin é a própria
   grade de resultados, não uma tela a mais.
6. O nome da skin é o texto principal do card; o nome do campeão é o secundário. Buscar
   "deus da guerra" precisa funcionar.

## Consequências

- O índice de campeões passa de ~173 para ~2.149 registros de skin × 4 tipos de asset
  (`square` é por campeão; `splash_centered`, `splash_wide`, `loading`, `tile` são por
  skin). É a fatia maior do índice e define o custo de carregamento inicial — a Spec
  precisa fatiar por categoria por causa disso.
- A busca precisa casar **nome da skin** e **nome do campeão** no mesmo campo, com a skin
  base ranqueada acima das demais quando a busca é pelo campeão.
- O `skinId` (`{championKey}{skinNum:03d}`) vira a chave natural do catálogo, exatamente
  como o [KICKOFF §B.7.1](../KICKOFF.md) já previa.
- Skins com nome longo e nome de campeão repetido exigem cuidado de layout no card. É
  problema de UI, não de dados.
- O protótipo fica desatualizado em relação a esta decisão. Tudo bem: ele é descartável e
  já cumpriu o papel de medir os cliques.
