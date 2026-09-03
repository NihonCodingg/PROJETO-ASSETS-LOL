# ADR 0010 — Navegação por campeão, busca por skin

- **Status:** aceito
- **Data:** 2026-09-03
- **Decidido por:** dono do projeto (correção de escopo)
- **Emenda:** [ADR 0008](0008-catalogo-de-skins-e-seletor.md), que dizia "a unidade do
  catálogo é a skin". A parte de busca continua valendo; a de navegação estava errada.

## Contexto

O ADR 0008 corrigiu um erro real — o protótipo só mostrava a skin base, e o job to be done
da §A.2 é *"preciso da splash da skin Jax Deus da Guerra"*. Mas corrigiu longe demais:
concluiu que **a unidade do catálogo** passava a ser a skin, com ~2.149 entradas no lugar
de 173.

Como modelo de navegação, isso não funciona:

- Uma grade de 2.149 cartões não é navegável. Abrir o site e ver duas mil skins soltas é
  pior do que ver 173 campeões — o editor sabe de que campeão precisa muito antes de saber
  de que skin.
- Um campeão apareceria repetido 18 vezes na tela sem nenhuma busca digitada, o que
  desperdiça a única superfície que orienta quem não sabe o que quer.
- E não resolvia o caso que realmente exige o nível de skin: buscar **"K/DA"** ou
  **"Prestígio"**, termos que atravessam vários campeões e não pertencem a nenhum.

O erro foi tratar navegação e busca como se precisassem da mesma unidade. Não precisam:
são superfícies diferentes, com trabalhos diferentes.

## Decisão

O modelo é **híbrido**. Navegação e busca operam em níveis diferentes, de propósito.

| Superfície | Unidade | Entradas | Para quê |
|---|---|---:|---|
| **Navegação** | campeão | **173** | Quem sabe o campeão e quer chegar nele |
| **Busca** | skin (e campeão) | **2.149** | Quem sabe o nome da skin, ou um termo transversal |
| **Painel do campeão** | skin | as do campeão | Onde vive o seletor de skin |

1. **Navegação por campeão.** A grade padrão tem 173 entradas, uma por campeão, com a arte
   da skin base e o número de skins. É o que aparece sem nada digitado.
2. **Índice de busca no nível de skin.** 2.149 entradas. Buscar "K/DA" ou "Prestígio"
   retorna skins de **vários campeões**, cada uma rotulada com o campeão de origem.
3. **Um campeão casado aparece uma vez.** Buscar "jax" devolve **uma** entrada de campeão,
   não 18 de skin. Só skins cujo próprio nome casa a consulta viram entradas de skin.
4. **O painel do campeão contém as skins.** O seletor de skin vive lá, e é onde os chromas
   ficam atrás do toggle do [ADR 0008](0008-catalogo-de-skins-e-seletor.md).
5. **Clicar num resultado de skin abre o painel do campeão com aquela skin já
   selecionada.** O resultado de busca não é um destino separado; é um atalho para dentro
   do painel.

### O que isso faz com a regra dos 3 cliques

| Caminho | Cliques |
|---|---|
| Buscar "deus da guerra" → clicar na skin → baixar | **2** |
| Buscar "jax" → clicar no campeão → baixar (asset de campeão, ex.: square) | **2** |
| Buscar "jax" → clicar no campeão → escolher a skin → baixar | **3** |
| Navegar sem digitar → clicar no campeão → escolher a skin → baixar | **3** |

O orçamento fecha exatamente. **Buscar pelo nome da skin é o atalho que pula o seletor** —
é por isso que o nível de skin na busca não é luxo: é o que mantém o caminho longo em 3.

## Consequência no contrato: duas projeções, não uma

Se navegação e busca operam em níveis diferentes, o front precisa dos dois níveis **antes**
de precisar de qualquer asset. Derivar isso de uma fatia com ~10 mil registros de asset —
que era o desenho anterior — significa baixar ~1 MB comprimido para desenhar 173 cartões.

Por isso o contrato ganha um documento novo, o **catálogo** (`catalog.schema.json`):

- `champions[]` — 173 entradas: chave, id, nomes, título, tags, contagem de skins e de
  chromas, `baseSkinId` e a chave da miniatura.
- `skins[]` — 2.149 entradas: `skinId`, `skinNum`, `championKey`, nomes, `isBase`,
  contagem de chromas e a chave da miniatura.

Sem asset, sem hash, sem URL de origem. É a projeção de navegação e busca, e só.

Ordem de carga: `manifest.json` → `catalog` (sempre) → fatia de assets do campeão
**sob demanda**, na primeira vez que um painel abre. A fatia continua sendo uma só; o que
muda é que ela deixa de ser bloqueante.

## Consequências

**Boas**

- A carga inicial cai de ~1 MB comprimido para algo na casa das dezenas de KB, e a busca
  fica disponível antes de qualquer asset ter sido baixado (RNF-01, RNF-03).
- A grade padrão volta a ser navegável, e o número de skins em cada cartão vira informação
  útil em vez de ruído.
- Termos transversais ("K/DA", "Prestígio", "Lunar") passam a funcionar sem nenhuma tabela
  extra — os nomes das skins já os contêm, e a normalização do
  [ADR 0009](0009-apelidos-de-busca-mantidos-a-mao.md) cuida da barra e do acento.
- A separação fica explícita no contrato, e não implícita no código do front. Foi a
  ausência dessa separação que produziu o erro do ADR 0008.

**Ruins / custos aceitos**

- Um documento a mais para gerar, validar e publicar. Pequeno, mas é mais uma peça.
- Abrir o primeiro painel de campeão custa uma requisição extra ao CDN. É um JSON já
  comprimido, servido imutável, e acontece enquanto o usuário lê a tela.
- O catálogo duplica nomes que também existem na fatia de assets. Duplicação consciente:
  é o preço de não baixar a fatia para desenhar a home.
- O ranqueamento da busca fica com duas classes de resultado (campeão e skin) e precisa
  decidir a ordem entre elas. Regra: casamento exato de campeão vem antes de casamento
  parcial de skin.

## Alternativas descartadas

- **Manter tudo no nível de skin** (o ADR 0008 como estava). Grade de 2.149 cartões, com o
  mesmo campeão repetido dezenas de vezes.
- **Voltar tudo para o nível de campeão.** Mata "K/DA" e "Prestígio", que são exatamente as
  buscas que só existem no nível de skin.
- **Derivar as duas projeções no cliente a partir da fatia de assets.** Funciona, mas
  obriga a baixar ~1 MB comprimido antes do primeiro pixel útil, e mantém no código do
  front a distinção que deveria estar no contrato.
- **Um arquivo de assets por campeão** (173 arquivos). Resolveria o mesmo problema, mas
  troca uma requisição por até 173 e complica publicação e invalidação sem ganho real.
