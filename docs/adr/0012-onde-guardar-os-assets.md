# ADR 0012 — Onde guardar os assets

- **Status:** 🟡 **proposto** — aguardando decisão do dono do projeto
- **Data:** 2026-09-05
- **Reabre:** a parte de storage do [ADR 0005](0005-arquitetura-estatica-custo-zero.md) e o
  [ADR 0007](0007-politica-de-versoes-e-orcamento.md) inteiro
- **Restrição declarada:** não cadastrar cartão na Cloudflare

## Contexto

O [ADR 0005](0005-arquitetura-estatica-custo-zero.md) escolheu o Cloudflare R2 com dois
argumentos: custo zero e **poupar as fontes do tráfego dos usuários** — este último herdado
da §A.6 do KICKOFF, escrita quando o projeto ainda mirava público amplo.

O escopo mudou desde então: o site é para o dono e uns poucos amigos. Nessa escala o segundo
argumento perde força — dez pessoas navegando não são tráfego que a Riot ou o Community
Dragon sintam. Sobra o custo, que é zero nas três alternativas, e o que cada uma custa em
promessas quebradas.

Antes de comparar, medi o que ainda não tinha medido. **Tudo abaixo é medição desta sessão,
não estimativa.**

---

## O que foi medido

### 1. CORS: vale para todos os tipos, não só os que eu tinha testado

Testado com `Origin: https://exemplo.vercel.app` em **18 tipos de asset**, nas três fontes:

| Fonte | Tipos testados | `Access-Control-Allow-Origin` |
|---|---|---|
| ddragon | square, splash_wide, splash_centered, loading, tile, item, spell, passive, profileicon, rune, map, tarball | **`*` em todos** |
| cdragon | champion JSON, champion-icon, chroma, emote, ward skin, ranked crest | **`*` em todos** |
| Riot static | `ranked-emblems-latest.zip` | **`*`** |

A resposta à sua pergunta é: **vale para todos**. Não achei um único recurso das fontes sem
CORS aberto.

### 2. Mas as fontes não declaram cache

| Recurso | `Cache-Control` | Observação |
|---|---|---|
| ddragon (qualquer imagem) | **ausente** | CloudFront + S3, com `ETag` e `Last-Modified`; o navegador cai em cache heurístico |
| cdragon | `max-age=3600` | 1 hora, para arquivo que nunca muda |
| R2 sob nosso controle | `max-age=31536000, immutable` | é o que o T-06 já publica |

Isso importa mais do que parece: a grade de 173 campeões são 173 miniaturas. Com o R2 elas
são imutáveis e vêm do cache do navegador para sempre. Direto do ddragon, a revalidação fica
na heurística do navegador; do cdragon, expira a cada hora.

Medi o custo real de carregar a grade direto da fonte: **20 squares em 0,71 s, 538 KB**
(média 26,9 KB). Extrapolando para 173: ~4,6 MB e ~6 s numa carga fria. Não é proibitivo —
mas é toda visita fria, não só a primeira.

### 3. JSZip com bytes de terceiros: **testado, funciona**

Você perguntou se era suposição. Era. Agora não é.

Montei uma página local, carreguei o JSZip 3.10.1 e zipei **cinco arquivos buscados por
`fetch` cross-origin** de dois hosts diferentes (ddragon e cdragon), sem nenhum servidor
próprio no meio:

```
Jax_square.png                 27.107 B   ddragon.leagueoflegends.com
Jax_000_splash_centered.jpg    92.299 B   ddragon.leagueoflegends.com
Jax_000_splash_wide.jpg       139.824 B   ddragon.leagueoflegends.com
Item_3031.png                   7.104 B   ddragon.leagueoflegends.com
Chroma_24009.png               58.336 B   raw.communitydragon.org
→ zip de 325.258 B em 1,5 s, relido com os 5 arquivos, bytes preservados
```

Funciona porque o CORS permite **ler** os bytes, não só exibi-los. E o T-08 já baixa por
`fetch`+blob em vez de `<a download>` — o que, de quebra, nos deixa imunes ao fato de o
atributo `download` ser ignorado em URL de outra origem.

### 4. GitHub: os assets de release **não mandam CORS**

Esta é a medição que decide a opção C.

| Origem | `Access-Control-Allow-Origin` | `Cache-Control` |
|---|---|---|
| **release asset** (`release-assets.githubusercontent.com`) | **AUSENTE** | `no-cache` |
| `raw.githubusercontent.com` | `*` | `max-age=300` |
| `cdn.jsdelivr.net/gh` | `*` | `public, max-age=604800` |
| GitHub Pages | `*` | `max-age=600` |

Confirmado em três repositórios diferentes (ripgrep, bat, fd) — não é caso isolado.

### 5. Limites documentados

| Limite | Valor | Fonte |
|---|---|---|
| Assets por release | **1.000** | docs do GitHub |
| Tamanho por arquivo em release | 2 GiB | docs do GitHub |
| Tamanho total / banda de release | **sem limite declarado** | docs do GitHub |
| Arquivo no repositório | 100 MiB (bloqueio), aviso em 50 MiB | docs do GitHub |
| Tamanho do repositório | "idealmente < 1 GB, fortemente recomendado < 5 GB" | docs do GitHub |
| jsDelivr: arquivos por repo | recomendado **≤ 10.000** ativos; soft limit 100.000 | AUP do jsDelivr |
| R2 free tier | 10 GB-mês, 1M Classe A, 10M Classe B, **egress grátis** | docs da Cloudflare |

---

## A) Manter o R2

### Custo real nesta escala

Com **26.346 arquivos e 2,0 GB** ([S4](../SPIKES.md)):

| Recurso | Consumo estimado | Tier gratuito | Uso |
|---|---:|---:|---:|
| Armazenamento | 2,0 GB | 10 GB-mês | **20 %** |
| Classe A (escritas) | ~58.000/mês (2,2 indexações × 26.357 objetos) | 1.000.000 | **5,8 %** |
| Classe B (leituras) | ~60.000/mês (10 pessoas × 30 sessões × ~200 GET) | 10.000.000 | **0,6 %** |
| Egress | irrelevante | grátis | — |

**R$ 0,00 por mês**, com o recurso mais apertado em 20 % do teto. Para estourar o
armazenamento seria preciso guardar **cinco versões** simultâneas — e a política do
ADR 0007 guarda uma.

### O que exige de você

Cartão (ou outro meio de pagamento) no perfil de cobrança, um API token com escopo de
leitura e escrita **só neste bucket**, e rotação manual desse token quando você quiser.

> ⚠️ **A premissa vale ser checada antes de decidir.** A documentação da Cloudflare **não
> diz** que o R2 exige meio de pagamento; quem diz são relatos da comunidade, incluindo um
> de agosto de 2026 descrevendo um diálogo obrigatório de cobrança ao habilitar o R2. As
> fontes se contradizem. **Abra o painel e tente habilitar o R2 sem cartão** — leva dois
> minutos e, se passar, esta decisão inteira deixa de existir.

**O que quebra se você perder o token:** a indexação para de publicar. O site continua
servindo normalmente, porque o `manifest.json` não muda e o bucket continua lá. Você gera um
token novo e volta. **Nada é perdido**: o conteúdo do bucket é dado derivado — o
`lol-assets-indexer` reconstrói tudo a partir das fontes.

### O que se ganha

- **Resiliência (RNF-07):** o site funciona com ddragon e cdragon fora do ar.
- **Integridade real:** o `sha256` do índice descreve exatamente os bytes que serão
  entregues, porque são os mesmos bytes que medimos. É uma garantia, não uma expectativa.
- **Cache imutável:** a segunda visita não baixa nada de novo.
- **Zips por categoria pré-gerados (RF-16):** "todos os ícones de item" é um arquivo pronto.
- **Fusão entre fontes com efeito real:** escolher a melhor resolução importa quando você
  copia o vencedor. Sem copiar, "escolher" é só registrar uma URL.

### Impacto

| | |
|---|---|
| ADRs invalidados | **nenhum** |
| T-06 (publicador) | **fica como está**, já mergeado e testado |
| T-11 (rotação) | implementável exatamente como especificado |
| Tickets a ajustar | **zero** |
| Ganha | Mantém todas as promessas da Spec sem exceção |
| Perde | Exige um meio de pagamento cadastrado |

---

## B) Sem storage — o índice aponta para as fontes

O índice, o catálogo e o manifesto (~350 KB juntos) viram arquivos estáticos do próprio
app na Vercel. Nenhum asset é copiado; cada registro carrega só `sourceUrl`.

### As suas perguntas, respondidas

**CORS:** aberto em todos os 18 tipos testados. Não é obstáculo.

**Estabilidade das URLs:** aqui há uma nuance que vale separar em dois casos.

- *Versões anteriores:* o [ADR 0007](0007-politica-de-versoes-e-orcamento.md) já reconhece
  que splash, centered, loading e tile **não são versionados** no ddragon e por isso não
  existem historicamente. A opção B **não piora** isso — o histórico já era impossível.
- *Versão atual:* aqui a opção B introduz um problema novo. Quando a Riot publica um patch,
  aquelas URLs passam a servir a arte nova **antes** de reindexarmos. Durante a janela do
  RNF-06 (≤ 24 h), o site serve arte mais nova do que o índice descreve, e o `sha256` não
  bate. Com o R2, servimos exatamente o que medimos.

**A fusão sobrevive.** Ela decide *qual URL registrar*, não *o que copiar* — e continua
valendo. Vale lembrar, porém, que o S2 mediu **empate de dimensão em todo asset de
campeão** entre ddragon e cdragon, então na prática a fusão já escolhe o ddragon quase
sempre. O que se perde não é a fusão: é o efeito de tê-la escolhido.

**O `sha256` deixa de ser garantia e vira detector.** O front ainda pode calcular o hash do
que baixou e comparar — o T-08 já tem `sha256Hex`. A diferença é que a divergência passa a
ser possível, e o melhor que dá para fazer é avisar em vez de impedir.

**JSZip: funciona** — testado acima, com bytes de dois hosts diferentes.

**A resiliência morre, e nessa escala isso importa pouco.** Se o ddragon cair, o site
mostra o catálogo com imagens quebradas. Para dez pessoas, o custo é "volta mais tarde".
É a promessa mais fácil de abrir mão de todas.

### O que eu descobri e você não perguntou

**Duas perdas concretas que a opção B causa:**

1. **Os zips por categoria (RF-16) deixam de existir.** Não há onde pré-gerar. "Todos os
   ícones de item" viram 868 requisições no navegador — pelos 28 arquivos/s que medi, uns
   **31 s** e 5,5 MB. Tolerável. Já "todos os ícones de perfil" são **5.021 arquivos e
   554 MB**: uns três minutos e meio GB na memória do navegador. Essa categoria
   simplesmente não tem download em lote na opção B.
2. **Os emblemas de elo ficam sem fonte utilizável.** O emblema composto só existe dentro do
   `ranked-emblems-latest.zip`, de **61,5 MB**. Verifiquei o cdragon: ele tem as *peças*
   (`diamond_base.png`, `diamond_crown_d1.png`, `backlight.png`…) com CORS aberto, mas não o
   emblema montado. Compor as peças seria manipular imagem — o que o
   [ADR 0001](0001-formato-de-entrega-dos-assets.md) proíbe no indexador e exigiria storage
   de qualquer jeito. Sem storage, a categoria `rank` ou sai da v1, ou vira "baixe o zip de
   61,5 MB da Riot".

### Impacto

| | |
|---|---|
| ADRs a emendar | **0005** (a linha de storage), **0007** (inteiro: não há o que copiar nem o que rotacionar) |
| RNF/RF perdidos | **RNF-07** (resiliência), **RF-16** (zip por categoria pré-gerado) |
| T-06 (publicador) | **Reescrito.** O `S3ObjectStore` sai; o `LocalObjectStore` e a trava de ordem sobrevivem, escrevendo o índice para dentro do app |
| T-11 (rotação) | **Some quase todo.** Sem assets copiados, não há o que remover |
| Tickets a ajustar | **9**: T-06, T-10, T-11, T-12, T-13, T-22, T-23, T-25, T-26 |
| Ganha | Nenhum serviço externo, nenhum segredo, nenhuma conta a manter |
| Perde | Resiliência, integridade garantida, zips por categoria e a categoria de elos |

### E uma propriedade que vale ouro: **é reversível de graça**

O contrato já foi desenhado para os dois mundos. `storageKey` é **opcional** no
`index-shard.schema.json`, e o catálogo tem `thumbnailKey` **e** `thumbnailUrl` — isso
existe desde o ADR 0007, para as versões antigas. E o T-08 já implementa o fallback:

```ts
export function assetUrl(asset: Asset, assetsBaseUrl?: string): string {
  if (asset.storageKey && assetsBaseUrl) return `${assetsBaseUrl}/${asset.storageKey}`;
  return asset.sourceUrl;   // ← já testado
}
```

Migrar de B para A depois é **preencher `storageKey`** e ligar a base pública. O front não
muda uma linha.

---

## C) GitHub como storage

### C1 — Releases: **não funciona**

Os assets de release são servidos por `release-assets.githubusercontent.com` **sem
`Access-Control-Allow-Origin`** e com `Cache-Control: no-cache`. Confirmado em três
repositórios.

Sem CORS, o navegador **não pode ler os bytes**. Isso derruba, de uma vez:

- a conversão para PNG no canvas ([ADR 0001](0001-formato-de-entrega-dos-assets.md) regra 2),
- o zip no cliente (RF-17, RF-18),
- a verificação de `sha256`,
- e o próprio "Baixar original", porque `<a download>` é ignorado em outra origem e o
  navegador navega em vez de salvar.

Só o `<img src>` continuaria funcionando — daria para *ver* as miniaturas e não para
*baixar* nada. Num site cujo verbo é "baixar", isso é fatal.

Sobre a pergunta do zip por patch: nem seria preciso. O limite é de **1.000 assets por
release**, então 26.346 arquivos cabem em **27 releases** de arquivos individuais, sem
obrigar ninguém a baixar 2 GB para ver uma miniatura. O problema não é o empacotamento — é
o CORS.

Sobre rate limit: o GitHub documenta explicitamente **"we don't limit the total size of the
binary files in the release or the bandwidth used to deliver them"**. Não achei limite
numérico publicado para download de asset de release. O que existe é a cláusula da AUP
(abaixo), que é qualitativa.

### C2 — Arquivos versionados no repositório

`raw.githubusercontent.com` **tem CORS** (`*`) e `max-age=300`. Tecnicamente funciona. Dois
problemas:

1. **O repositório cresce para sempre.** 2,0 GB de binário já ficaria acima do "idealmente
   < 1 GB" do GitHub. Pior: a rotação de versão do ADR 0007 apaga arquivos — mas **o git
   guarda todo blob apagado no histórico**. Cada patch somaria ~2 GB permanentes. Em cinco
   patches o repositório passa de 10 GB, e o "fortemente recomendado < 5 GB" fica para trás
   em dois meses e meio. Fugir disso exigiria force-push de branch órfã a cada patch, o que
   é feio e nem coleta lixo na hora.
2. **`max-age=300`** e as novas cotas para requisições não autenticadas, que o GitHub
   passou a aplicar em 2025 justamente a clone e a `raw.githubusercontent.com`.

### C3 — jsDelivr sobre o repositório

Tecnicamente é a melhor variante: CORS `*` e `Cache-Control: public, max-age=604800` — cache
melhor até que o do ddragon. Mas:

- **A AUP do jsDelivr manda o conteúdo obedecer também às regras do GitHub**: *"any content
  accessed via jsDelivr must conform to the terms of the service from which it was
  retrieved"*. O crescimento do repositório de C2 continua igual — o jsDelivr não lava a
  banda do GitHub.
- **Uso proibido**, textualmente: *"Abusing the service and its resources, or using jsDelivr
  as a general-purpose file or media hosting service. This includes, for example: running an
  image hosting website and using jsDelivr as a storage for all uploaded images"*. Há uma
  ressalva: *"We recognize that there are legitimate projects that consist of a large number
  of files… For example: icons packs, apps, or games with a large number of assets."*
- **Onde caímos?** Zona cinzenta, e na minha leitura pendendo para o lado proibido. A
  ressalva descreve um projeto que *usa* seus assets; o nosso é um projeto cujo produto
  *são* os assets, e cuja tela principal é uma galeria para baixar imagem. É literalmente
  "um site de hospedagem de imagem" na função, ainda que as imagens não sejam upload de
  usuário. A própria AUP convida a perguntar (*"We will be happy to remove limits or provide
  custom solutions for legitimate projects"*), então dá para tirar a dúvida na fonte — mas
  hoje é dúvida, não permissão.
- Some-se: **26.346 arquivos** contra o recomendado de **10.000 ativos por repositório**.

E a cláusula do GitHub que atravessa as três variantes: *"If we determine your bandwidth
usage to be significantly excessive in relation to other users of similar features, we
reserve the right to suspend your Account."* Nesta escala ninguém vai notar — mas é uma
cláusula discricionária sobre a conta que hospeda o código do projeto, não sobre um bucket
descartável.

### Impacto

| | |
|---|---|
| ADRs a emendar | **0005**, **0007**, mais um ADR novo para a decisão de usar o GitHub como CDN e a leitura de ToS |
| T-06 (publicador) | **Reescrito** para publicar por commit em vez de por API S3 |
| T-11 (rotação) | **Piora**: apagar não recupera espaço; vira problema de histórico do git |
| Tickets a ajustar | **6+**: T-06, T-10, T-11, T-12, T-13, T-23, mais um ticket novo para a mecânica de repositório/CDN |
| Ganha | Nada que o R2 não dê, exceto não precisar de cartão |
| Perde | C1 é inviável por CORS; C2/C3 trocam o cartão por crescimento perpétuo do repositório e uma zona cinzenta de ToS |

---

## Comparativo

| | A) R2 | B) Sem storage | C) GitHub |
|---|---|---|---|
| Custo | R$ 0 (20 % do teto) | R$ 0 | R$ 0 |
| Exige cartão | **sim** (a confirmar) | não | não |
| CORS | nosso | aberto nas fontes ✅ | ❌ release · ✅ raw/jsDelivr |
| Cache | `immutable` | ausente (ddragon) / 1 h (cdragon) | 5 min (raw) / 7 d (jsDelivr) |
| Resiliência (RNF-07) | ✅ | ❌ | ✅ |
| `sha256` como garantia | ✅ | detector | ✅ |
| Zip por categoria (RF-16) | ✅ | ❌ | ✅ |
| Emblemas de elo | ✅ | ❌ (só o zip de 61,5 MB) | ✅ |
| Escala no tempo | constante (~2 GB) | zero | **cresce ~2 GB/patch** |
| ToS | limpo | limpo | zona cinzenta |
| ADRs a emendar | 0 | 2 | 2 + 1 novo |
| Tickets a ajustar | **0** | 9 | 6+ |

---

## Recomendação

**Primeiro: cheque se a premissa existe.** A documentação da Cloudflare não afirma que o R2
exige meio de pagamento — só relatos de comunidade afirmam, e se contradizem. Tente
habilitar o R2 sem cartão. Se der, escolha **A** e nada nesta análise precisa acontecer:
zero ADRs emendados, zero tickets mexidos, todas as promessas da Spec mantidas, 20 % do teto
gratuito.

**Se realmente exigir cartão e você mantiver a restrição: escolha B.**

Não porque B seja tão bom quanto A — não é. B custa quatro coisas medidas: a resiliência, a
garantia de integridade, os zips por categoria e a categoria de elos. **Mas nenhuma delas
quebra o projeto nesta escala**, e o que sobra é exatamente o que você usa: achar um asset,
ver a ficha, baixar o arquivo. Isso continua funcionando, e o teste de JSZip mostra que até
o lote por seleção continua.

O que decide entre B e C é que **C não compra nada que B não dê**. C1 é tecnicamente
inviável por falta de CORS. C2 e C3 funcionam, mas trocam o cartão por um repositório que
cresce 2 GB por patch e por uma leitura de ToS que eu não conseguiria defender com
convicção. Se é para abrir mão de storage próprio, é mais honesto abrir mão de vez (B) do
que fingir que o GitHub é um bucket (C).

**E o custo de escolher B agora é baixo porque B é reversível.** O contrato já trata
`storageKey` como opcional e o front já cai para `sourceUrl` — código que existe, testado,
desde o T-08. Se um dia você mudar de ideia sobre o cartão, migrar é preencher um campo.

### Onde eu discordo de você

Se a sua objeção ao cartão for **medo de conta surpresa**, os números não sustentam o medo:
o recurso mais apertado é o armazenamento, em 20 % do teto, e seria preciso guardar cinco
versões simultâneas para estourá-lo — enquanto a política guarda uma. Nesse caso, **A é a
escolha melhor e eu recomendaria vencer a objeção**, não contorná-la.

Se a objeção for **não querer cartão cadastrado em mais um serviço**, por princípio ou por
superfície de risco, isso é uma preferência legítima que número nenhum derruba. Aí B é o
segundo lugar honesto, e a lista do que se perde está acima para você decidir com ela à
vista — em especial o item que ninguém tinha notado: **os emblemas de elo saem da v1**.

## Próximo passo

Nenhum código foi tocado. Spec e tickets estão intactos. Este ADR fica em **proposto** até
sua decisão; aceito ele, faço as emendas nos ADRs 0005 e 0007 e ajusto os tickets nomeados
acima, na ordem, antes de seguir para a Onda 2.
