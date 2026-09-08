# ADR 0013 — Uma versão por vez no índice

- **Status:** ✅ **aceito** (08/09/2026)
- **Data:** 2026-09-08
- **Depende de:** [ADR 0012](0012-onde-guardar-os-assets.md), [ADR 0007](0007-politica-de-versoes-e-orcamento.md)
- **Evidência:** [`docs/evidencias/t09-indexacao-real.json`](../evidencias/t09-indexacao-real.json) e a execução de duas versões descrita abaixo
- **Emenda:** o item 3 do [ADR 0007](0007-politica-de-versoes-e-orcamento.md)

> **Este ADR só existe por causa da opção B do [ADR 0012](0012-onde-guardar-os-assets.md).**
> Com storage próprio, guardar histórico de índice custaria alguns MB num bucket que
> ninguém baixa inteiro, e a decisão seria irrelevante. Sem storage, o índice mora no
> repositório — e repositório é a única coisa do projeto que **todo mundo baixa inteira,
> toda vez**.

## Contexto

O [ADR 0007](0007-politica-de-versoes-e-orcamento.md) dizia que o índice "acumula, mas é
barato: alguns MB por versão". Isso foi escrito quando o índice ia para um bucket. O
[ADR 0012](0012-onde-guardar-os-assets.md) mudou o destino para o repositório e ninguém
refez a conta.

O T-11 fez a conta, indexando dois patches de verdade um depois do outro:

| | Bytes | Assets | Categorias |
|---|---:|---:|---|
| Versão corrente (16.17.1) | **10.581.799** | 15.515 | champion, item, map, profile_icon, **rune**, summoner_spell |
| Versão anterior reduzida (16.16.1) | **4.429.668** | 6.966 | champion, item, map, profile_icon, summoner_spell |

**A Riot publica um patch a cada duas semanas: ~26 por ano.** Guardar histórico custa
**4,4 MB por patch, ~115 MB por ano**, para sempre.

"Para sempre" é literal. O Git guarda todo blob que já foi commitado, mesmo depois de o
arquivo ser apagado: um `git clone` baixa o histórico inteiro. Apagar o índice antigo do
diretório de trabalho não devolve um byte a quem clona.

E o que se compra com isso é pouco:

- **Histórico de arte não existe.** `splash`, `centered`, `loading` e `tiles` são servidos
  sem versão na URL ([ADR 0007](0007-politica-de-versoes-e-orcamento.md)); numa versão
  antiga eles têm que sumir, senão o site mostra a arte de hoje com rótulo de ontem.
- **Runas também não.** `perk-images` não é versionado, então a **categoria inteira**
  desaparece de qualquer versão antiga. Medido: a fatia `rune` some.
- Sobra square, item, feitiço, passiva, habilidade, ícone de perfil e mapa — ícones que
  quase nunca mudam entre patches.

Ou seja: o histórico custa 115 MB/ano e entrega, na prática, ícones repetidos.

## Decisão

**O índice guarda exatamente uma versão: a corrente.**

1. O `manifest.json` traz **um** item em `versions[]`, sempre igual a `currentVersion`.
2. Ao indexar um patch novo, a versão anterior **sai do manifesto** e os documentos dela
   são **removidos do destino** pela varredura de órfãos — nessa ordem, nunca a inversa.
3. **RF-19** (seletor de versão) e **RF-20** (tipos indisponíveis explicitamente ausentes)
   saem da v1. Não há versão anterior para selecionar nem para explicar.
4. O que seria redução ao histórico **não vai para o código**. Chegou a ser escrita e
   testada durante o T-11 e foi descartada antes de entrar: código que nada exercita
   apodrece, e a regra inteira cabe em seis linhas de texto — estão aqui embaixo.

## Consequências

- O diretório do índice fica **constante em ~10,6 MB**, independente de quantos patches
  passem.
- **O histórico do Git continua crescendo ~10,6 MB por patch**, porque cada indexação
  reescreve o índice inteiro com nomes novos (hash no nome). O teto elimina os 4,4 MB da
  versão reduzida — não os 10,6 MB da corrente. Isso é um problema **separado e maior**
  (~275 MB/ano quando o T-13 rodar sozinho a cada 6 h) e está registrado no **T-37**.
- O front simplifica: não há seletor de versão, e `versions[]` com um item é invariante que
  dá para testar.
- **Perde-se a capacidade de comparar patches.** É real, e é aceita: o dono do projeto
  edita conteúdo atual.
- A guarda de tamanho do T-10 continua valendo por versão (15 MiB) e agora coincide com o
  total, porque só existe uma.

## Como voltar atrás

Se um dia o histórico fizer falta, a regra inteira cabe aqui — não é preciso recuperar
código nenhum, e é de propósito que ela está escrita e não commitada:

1. **Um asset sobrevive a uma versão antiga se, e só se, a `sourceUrl` dele contém
   `/cdn/{gameVersion}/`.** É a URL que decide, não uma lista de tipos: lista escrita à
   mão fica errada assim que o ddragon mudar um caminho de lugar. Na prática sobrevivem
   `square`, `item_icon`, `summoner_spell_icon`, `ability_icon`, `passive_icon`,
   `profile_icon` e `map_image`.
2. **Fatia que fica vazia desaparece da versão.** A `rune` inteira cai por aqui.
3. **No catálogo, a miniatura do campeão sobrevive e a da skin não** — a primeira é o
   `square` (versionado), a segunda é o `tile` (não versionado). Manter o tile mostraria a
   arte de hoje ao lado do nome de uma skin de ontem.
4. A redução é **idempotente**: aplicá-la de novo sobre uma versão já reduzida não muda
   nada, o que faz o hash do documento ser estável entre execuções.
5. A varredura de órfãos já respeita qualquer teto, porque ela olha o que o manifesto
   referencia — não uma contagem.
6. **Refaça a conta de bytes antes, não depois.** Foi ela que derrubou a ideia.

## Alternativas consideradas

- **Acumular sem teto** (o que o ADR 0007 dizia). 115 MB/ano de histórico que ninguém
  usa, num repositório que todo clone paga inteiro.
- **Teto de N versões** (3, 6, 12). Adia a pergunta sem responder nenhuma: o custo continua
  linear e a funcionalidade continua incompleta pelos mesmos motivos.
- **Gerar o índice no build da Vercel**, sem commitar. Resolveria os 10,6 MB/patch do
  T-37 também, mas exigiria baixar 2,39 GB a cada deploy, dentro dos limites do plano
  Hobby — e o [ADR 0012](0012-onde-guardar-os-assets.md) escolheu publicar por commit
  justamente para não depender de nada além do `GITHUB_TOKEN`. Fica anotado no T-37 como
  a alternativa a avaliar lá.
