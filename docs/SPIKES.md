# SPIKES — números reais das fontes

> Medições feitas em **03/09/2026** contra o patch **16.17.1**.
> Tudo aqui foi medido, não estimado. Os resultados brutos estão em
> [`docs/evidencias/spikes/`](evidencias/spikes/) (versionados como evidência).
> Onde a Parte B do [KICKOFF](KICKOFF.md) se mostrou errada, está marcado com **[CORRIGE B.x]**.

## Como reproduzir

Os scripts viviam em `prototype/spikes/` e foram apagados no ticket T-01, junto com o
resto do protótipo. Continuam recuperáveis pelo histórico:

```bash
git show 0410fd7 -- prototype/spikes   # S1, S2, S3 e o cliente HTTP compartilhado
git show 388ea0a -- prototype/spikes   # S4
```

A partir da Onda 1, o cliente HTTP com a mesma etiqueta passa a viver em
`packages/indexer/src/lol_assets_indexer/http.py` (ticket T-03), aí sim com testes.

Todas as requisições usaram
`User-Agent: lol-assets-indexer/0.0.0-spike (+https://github.com/NihonCodingg/PROJETO-ASSETS-LOL; …)`,
concorrência 4 e backoff exponencial, conforme a regra 4 do [CLAUDE.md](../CLAUDE.md).

## Wiki — status do consentimento

**`WIKI_CONSENT_GRANTED = false`.** Nenhuma requisição a `wiki.leagueoflegends.com`
foi feita em nenhum spike. O cliente HTTP usado por eles tinha uma trava explícita que
levantava exceção se qualquer URL da wiki fosse passada, e o **T-03 recria essa trava** em
`packages/indexer/.../http.py`, com teste. A regra 3 é imposta pelo código, não só pela
disciplina. O spike **S4 não foi executado** e só será depois que
o consentimento da Weird Gloop for obtido e registrado aqui, com data e evidência.

---

## S1 — Data Dragon

### Descoberta

| O quê | Valor medido |
|---|---|
| `/api/versions.json` | 498 versões; mais recente **16.17.1** |
| Versões seguintes | 16.16.1, 16.15.1, 16.14.1, 16.13.1, 16.12.1 |
| `/cdn/languages.json` | 28 idiomas; `pt_BR` presente |
| `/realms/br.json` | `v` = 16.17.1, `l` = pt_BR |
| `/cdn/dragontail-16.17.1.tgz` | HTTP 200 · **2,39 GB** (2.564.139.878 bytes) · `application/x-tar` |
| `/cdn/cdragontail-16.17.1.tgz` | **HTTP 403 — não existe** |
| Download do tarball | 83,7 s (~30 MB/s nesta máquina) |
| Conteúdo | **34.305 arquivos**, 2,67 GB descompactados |
| Inspeção completa (Pillow em toda imagem) | 63,3 s · **0 imagens ilegíveis** |

**[CORRIGE B.6]** o tarball tem **2,39 GB**, não "~1 GB".
**[CORRIGE B.1.1]** não existe `cdragontail-{versão}.tgz`; só `dragontail`.

### Tamanho em disco por recorte

| Recorte | Bytes | Legível |
|---|---:|---|
| `data/pt_BR` | 9.758.542 | 9,3 MB |
| `data/en_US` | 9.363.539 | 8,9 MB |
| `data/` (28 idiomas) | 282.954.412 | 270 MB |
| `img/` versionado (`{v}/img/…`) | 1.428.492.458 | 1,33 GB |
| `img/` não versionado | 1.158.165.430 | 1,08 GB |

Ficar só com `pt_BR + en_US` em vez dos 28 idiomas economiza **~252 MB por patch**.

### Imagens dentro e fora do escopo da v1

| Fatia | Arquivos | Tamanho |
|---|---:|---:|
| **No escopo da v1** (campeão, item, feitiço, passiva, profileicon, runa, mapa) | 15.539 | **1,34 GB** |
| Fora do escopo | 11.138 | 1,07 GB |
| · TFT (`img/tft-*`) | 4.391 | 634,0 MB |
| · Challenges | 3.388 | 139,7 MB |
| · Modo League Classic | 2.492 | 172,7 MB |
| · Sprites (atlas) | 575 | 90,9 MB |
| · Missões | 292 | 56,6 MB |

Descartar o que está fora do escopo corta **44 % do peso de imagem** do tarball.

### Dimensões reais por tipo — medidas em 100 % dos arquivos

| Tipo | Caminho | Arquivos | Dimensão | Formato | Modo |
|---|---|---:|---|---|---|
| Square do campeão | `{v}/img/champion/{Id}.png` | 173 | **128×128** | PNG | RGB |
| Splash | `img/champion/splash/{Id}_{num}.jpg` | 2.118 | **1215×717** | JPEG | RGB |
| **Splash centralizada** | `img/champion/centered/{Id}_{num}.jpg` | 2.118 | **1280×720** | JPEG | RGB |
| Loading | `img/champion/loading/{Id}_{num}.jpg` | 2.118 | **308×560** | JPEG | RGB |
| **Tile** | `img/champion/tiles/{Id}_{num}.jpg` | 2.118 | **380×380** | JPEG | RGB |
| Ícone de item | `{v}/img/item/{id}.png` | 868 | 64×64 (865), 128×128 (2), 512×512 (1) | PNG | RGB |
| Ícone de habilidade/feitiço | `{v}/img/spell/…` | 726 | 64×64 | PNG | RGB |
| Ícone de passiva | `{v}/img/passive/…` | 173 | 64×64 | PNG | RGB |
| Ícone de perfil | `{v}/img/profileicon/{id}.png` | 5.021 | **300×300** (4.543), 128×128 (333), 256×256 (117) | PNG | RGB |
| Runas | `img/perk-images/**` | 88 | 256×256 (keystones), 128×128, 64×64, 32×32 (statmods) | PNG | **RGBA** |
| Minimapa | `{v}/img/map/map{id}.png` | 5 | 512×512 (3), 1024×1024 (2) | PNG | RGB / P |

**[CORRIGE B.1.7]** o square é **128×128**, não 120×120.
**[CORRIGE B.1.3]** `img/champion/centered/` e `img/champion/tiles/` **existem** no
ddragon e não estavam documentados. A centralizada (1280×720) é **maior** que a
splash clássica (1215×717) — testadas também via URL direta no CDN, HTTP 200.
**[CORRIGE B.1.7]** ícones de perfil são majoritariamente 300×300, não "pequenos".

### Transparência na fonte — responde à pergunta A.9

Só têm canal alfa de verdade (alpha mínimo 0 em amostras reais):

- `img/perk-images/**` (runas e stat mods) — RGBA
- `img/challenges-images` — RGBA
- `img/item-modifiers` — RGBA
- parte dos assets de TFT e de missão

**Não têm transparência** (RGB puro): squares de campeão, ícones de item, de
feitiço, de passiva, de perfil, splashes, loading e tiles. Ou seja: converter esses
para PNG **não** produz fundo transparente — só troca o container.

### CORS — as duas fontes liberam leitura pelo navegador

Medido com `Origin: http://localhost:3000` em JSONs e imagens das duas fontes:

| Recurso | `Access-Control-Allow-Origin` |
|---|---|
| `ddragon /api/versions.json` | `*` |
| `ddragon /cdn/{v}/data/pt_BR/champion.json` | `*` |
| `ddragon /cdn/{v}/img/champion/Jax.png` | `*` |
| `ddragon /cdn/img/champion/centered/Jax_0.jpg` | `*` |
| `cdragon /…/v1/champion-icons/24.png` | `*` |

O ddragon ainda manda `Access-Control-Allow-Methods: GET, HEAD`. Consequência prática:
o navegador consegue desenhar essas imagens em `<canvas>` com `crossOrigin="anonymous"`
sem contaminar o canvas, então **converter para PNG no cliente é viável sem proxy** —
é a base técnica do [ADR 0001](adr/0001-formato-de-entrega-dos-assets.md).

### Conferência das URLs de §B.1.3 direto no CDN

Todas responderam HTTP 200 com as dimensões acima. `/cdn/16.17.1/img/profileicon/1.png`
veio 128×128, o que é consistente com a distribuição do tarball (nem todo ícone é 300×300).

---

## S2 — Community Dragon

Campeões medidos: **Jax (24), Lux (99), Nunu (20)** — 54 skins, 559 assets medidos.

### A listagem em JSON funciona

`https://raw.communitydragon.org/json/latest/plugins/rcp-be-lol-game-data/global/default/v1/`
→ HTTP 200, **108 entradas**, entre elas `champions`, `champion-icons`,
`champion-splashes`, `champion-chroma-images`, `perk-images`, `profile-icons`,
`hextech-images`, `map-assets`. Confirma §B.2.1.

### Os caminhos declarados no JSON funcionam; os montados à mão, não

| Origem do caminho | Assets | HTTP 200 | HTTP 404 |
|---|---:|---:|---:|
| Declarado no `v1/champions/{key}.json` (regra de mapeamento §B.2.1) | 397 | **397** | 0 |
| Montado à mão a partir de §B.2.3 | 165 | 3 | **162** |

**[CORRIGE B.2.3]** estes três caminhos da tabela de §B.2.3 dão **404 em 100 % das
54 skins testadas**:

- `v1/champion-splashes/{key}/{skinId}.jpg`
- `v1/champion-splashes/uncentered/{key}/{skinId}.jpg`
- `v1/champion-tiles/{key}/{skinId}.jpg`

Só `v1/champion-icons/{key}.png` funciona (128×128 PNG). Isso valida a regra do
próprio KICKOFF de §B.2.2: **partir sempre dos caminhos que o JSON declara**.

### Tipos de asset descobertos pelo JSON, com dimensões medidas

| Campo no JSON | Unidades | Dimensão | Formato | Mediana |
|---|---:|---|---|---:|
| `squarePortraitPath` | 1 por campeão | 128×128 | PNG | 27 KB |
| `skins[].splashPath` | 1 por skin | **1280×720** | JPEG | 94 KB |
| `skins[].uncenteredSplashPath` | 1 por skin | **1215×717** | JPEG | 177 KB |
| `skins[].tilePath` | 1 por skin | 380×380 | JPEG | 41 KB |
| `skins[].loadScreenPath` | 1 por skin | 308×560 | JPEG | 48 KB |
| `skins[].loadScreenVintagePath` | 23 das 54 skins | 308×560 | JPEG | 53 KB |
| `skins[].chromaPath` | 1 por skin com chroma | 270×303 | PNG | 56 KB |
| `skins[].chromas[].chromaPath` | 1 por chroma | 270×303 | PNG | 59 KB |
| `skins[].chromas[].tilePath` | 1 por chroma | 270×303 | PNG | 59 KB |
| `spells[].abilityIconPath` | 4 por campeão | 64×64 | PNG | 5 KB |
| `passive.abilityIconPath` | 1 por campeão | 64×64 | PNG | 5 KB |

Caminhos relativos do tipo `champion-abilities/0024/ability_0024_P1.jpg` aparecem no
JSON mas **não** seguem a regra `/lol-game-data/assets/…`; testados sob a base `v1/`
retornaram 404. A base correta deles ficou **em aberto** — não bloqueia a v1.

### ddragon × cdragon: as dimensões empatam

| Tipo | ddragon | cdragon | Vencedor |
|---|---|---|---|
| Square | 128×128 PNG | 128×128 PNG | empate |
| Splash centralizada | 1280×720 (`centered/`) | 1280×720 (`splashPath`) | empate |
| Splash não centralizada | 1215×717 (`splash/`) | 1215×717 (`uncenteredSplashPath`) | empate |
| Loading | 308×560 | 308×560 | empate |
| Tile | 380×380 | 380×380 | empate |

**[CORRIGE A.3 / B.1.7]** a premissa de que "o cdragon tem maior resolução" é **falsa
para assets de campeão**. O cdragon acrescenta **cobertura**, não resolução: chromas,
loading screens *vintage*, e a estrutura por skin já resolvida em JSON. Em bytes o
ddragon costuma vir um pouco maior (splash de Jax: 169 KB no ddragon contra 157 KB no
cdragon, mesma dimensão), ou seja, JPEG com qualidade um pouco melhor.

### Pegadinha de terminologia — vale um ADR

Os dois nomeiam a mesma coisa ao contrário:

| Imagem | ddragon | cdragon |
|---|---|---|
| 1280×720 | `centered` | `splashPath` |
| 1215×717 | `splash` | `uncenteredSplashPath` |

O índice precisa de nomes próprios e de um mapa por fonte, ou vai misturar as duas.

### Chromas confirmados

Jax tem **44 entradas** em `skins[]` no ddragon, mas só **18** têm arquivo de splash —
as outras 26 são chromas e são exatamente as que trazem o campo `parentSkin`. O cdragon
reporta 18 skins para Jax. Confirma §B.1.4 sem ressalvas: filtrar por presença de
`parentSkin` antes de montar URL de splash.

---

## S3 — Volume real e custo do PNG

### Contagens reais do catálogo (cdragon, patch atual)

| Coisa | Quantidade |
|---|---:|
| Campeões | **173** |
| Skins (inclui a base de cada campeão) | **2.149** |
| Chromas | **7.037** |
| Itens | 868 |
| Ícones de perfil | 5.078 |
| Emotes | 2.347 |
| Ward skins | 265 |
| Runas (perks) | 103 |
| Campeões extras do modo League Classic | 63 |

**[CORRIGE B.6]** são **2.149 skins**, não "~1.700". O número de campeões (173) bate
exatamente com a contagem de `data/pt_BR/champion/*.json` do tarball.
`champion-summary.json` traz 236 entradas porque inclui os 63 do modo Classic (ids 60xxx)
— filtrar por `id < 60000`.

### Converter JPG para PNG multiplica o tamanho por ~5,7

12 imagens reais (splash, centered, tile e loading) baixadas e reencodadas com Pillow
`optimize=True`:

| Métrica | Valor |
|---|---:|
| Razão mediana PNG/JPEG | **5,712×** |
| Razão média | 5,595× |
| Mínimo | 3,412× |
| Máximo | 6,974× |

Exemplos: 1280×720 de 73 KB → 491 KB; 380×380 de 29 KB → 186 KB; 308×560 de 38 KB → 229 KB.

**No navegador o custo é ainda maior.** Medido dentro do protótipo, com o mesmo caminho
que o [ADR 0001](adr/0001-formato-de-entrega-dos-assets.md) define
(`fetch` → `createImageBitmap` → `canvas` → `toBlob("image/png")`), na splash centralizada
de Miss Fortune:

| | Bytes | Razão |
|---|---:|---:|
| Origem (JPEG 1280×720, ddragon) | 123.478 | 1× |
| PNG gerado pelo Chrome | 1.005.101 | **8,14×** |

O encoder PNG do navegador é menos eficiente que o do Pillow com `optimize=True` (5,71×).
Isso reforça a decisão: guardar PNG no bucket custaria 5,7× **e** o usuário receberia
mesmo assim um PNG de 8,1× quando pedisse a conversão. Não há ganho em pré-gerar.
Confirmado também que o canvas **não é contaminado**, porque o bitmap vem de um `Blob`
obtido por `fetch` com CORS, não de um `<img>` de outra origem.

Isso é **o número mais importante desta sessão**, porque a §A.4 promete "PNG sempre" e
a §A.5 exige custo perto de zero. Converter não recupera qualidade nenhuma (a fonte é
JPEG e não tem alfa), só multiplica o armazenamento e a banda por ~5,7.

### Extrapolação para o catálogo inteiro (uma versão)

| Tipo | Fonte | Unidades | Mediana | Total na origem | Total em PNG |
|---|---|---:|---:|---:|---:|
| Splash centralizada | JPEG | 2.149 | 93 KB | 196,4 MB | 1,1 GB |
| Splash não centralizada | JPEG | 2.149 | 177 KB | 372,1 MB | 2,1 GB |
| Tile | JPEG | 2.149 | 40 KB | 84,2 MB | 481,1 MB |
| Loading | JPEG | 2.149 | 48 KB | 101,8 MB | 581,6 MB |
| Chromas | PNG | 7.037 | 59 KB | 408,7 MB | 408,7 MB |
| Square | PNG | 173 | 26 KB | 4,5 MB | 4,5 MB |
| Ícones de habilidade | PNG | 692 | 4 KB | 3,1 MB | 3,1 MB |
| Ícones de passiva | PNG | 173 | 4 KB | 780,5 KB | 780,5 KB |
| **Total** | | | | **~1,1 GB** | **~4,6 GB** |

Somando o que o tarball já entrega em PNG e que está no escopo (ícones de perfil
554,0 MB, itens 5,5 MB, feitiços 4,2 MB, runas 2,1 MB, passivas 1,0 MB, mapas 0,6 MB
= **567,4 MB**), uma versão completa fica em torno de **5,2 GB em PNG** contra
**1,7 GB** se cada asset for servido no formato de origem. Emotes (2.347) e ward skins
(265) só existem no cdragon e não foram medidos em bytes nesta sessão.

---

## S4 — Orçamento fechado (decisão D4)

Emotes e ward skins eram os dois buracos do RNF-05: contados, nunca medidos em bytes.
Medidos por amostragem aleatória com semente fixa (`20260903`), 40 arquivos por categoria.
De quebra, fecharam-se os dois buracos menores que sobravam.

| Categoria | Arquivos | Medição | Mediana | Total |
|---|---:|---|---:|---:|
| Emotes | 2.338 | amostra de 40, todos 256×256 PNG | 70,2 KB | **156,5 MB** |
| Ward skins | 530 | amostra de 40, 460×550 PNG | 15,3 KB | **7,7 MB** |
| Loading vintage | 915 | proporção medida no S2 (42,6 % das skins) | 58,5 KB | **51,1 MB** |
| Emblemas de elo | zip | `Content-Length` do zip oficial da Riot | — | **61,5 MB** |

Notas honestas sobre a amostragem:

- **Emotes:** 9 das 2.347 entradas têm `inventoryIcon` vazio; sobram 2.338 arquivos reais.
  A amostra veio homogênea — 40 de 40 em 256×256 PNG.
- **Ward skins:** cada ward tem **duas** imagens (`wardImagePath` e `wardShadowImagePath`),
  então são 530 arquivos, não 265. A distribuição é torta: mediana 15,3 KB contra média
  56,3 KB, com um caso de 1623×1536 e 685 KB. Usando a média em vez da mediana o total
  vai de 7,7 MB para 29,8 MB — **irrelevante** para a decisão, porque muda o orçamento
  total de 2,00 GB para 2,03 GB.
- **Emblemas de elo:** `ranked-emblems-latest.zip` respondeu **HTTP 200 · 64.478.096 bytes**,
  o que confirma §B.4 e dispensa o cdragon para esta categoria.

### Orçamento de uma versão completa

Onde havia número exato (o tarball, medido em 100 % dos arquivos no S1), usou-se o exato;
extrapolação só onde não havia.

| Categoria | Arquivos | Tamanho | % | Origem do número |
|---|---:|---:|---:|---|
| Ícone de perfil | 5.021 | 554,0 MB | 26,9 % | S1, exato |
| Chromas | 7.037 | 408,7 MB | 19,9 % | S3, extrapolado |
| `splash_wide` | 2.118 | 367,4 MB | 17,8 % | S1, exato |
| `splash_centered` | 2.118 | 219,6 MB | 10,7 % | S1, exato |
| Emotes | 2.338 | 156,5 MB | 7,6 % | **S4** |
| Loading | 2.118 | 124,4 MB | 6,0 % | S1, exato |
| Tile | 2.118 | 89,4 MB | 4,3 % | S1, exato |
| Emblemas de elo | zip | 61,5 MB | 3,0 % | **S4** |
| Loading vintage | 915 | 51,1 MB | 2,5 % | **S4** |
| Ward skins | 530 | 7,7 MB | 0,4 % | **S4** |
| Ícone de item | 868 | 5,5 MB | 0,3 % | S1, exato |
| Square do campeão | 173 | 4,6 MB | 0,2 % | S1, exato |
| Ícone de habilidade e feitiço | 726 | 4,2 MB | 0,2 % | S1, exato |
| Runas | 88 | 2,1 MB | 0,1 % | S1, exato |
| Ícone de passiva | 173 | 1014,0 KB | 0,0 % | S1, exato |
| Minimapa | 5 | 577,9 KB | 0,0 % | S1, exato |
| **Total** | **26.346** | **2,0 GB** | | |

### Veredito

**Cabe.** 2,0 GB = **20,1 %** do tier gratuito de 10 GB do R2, e bem abaixo do limite de
aborto de 8 GB do RNF-05. A condição de parada do T-02 **não** foi disparada.

A projeção do [ADR 0007](adr/0007-politica-de-versoes-e-orcamento.md) era "~1,9 GB"; o
medido é 2,0 GB. A estimativa estava certa.

Sobra que vale registrar: com uma versão ocupando 2,0 GB, caberiam **quatro** versões
completas nos 10 GB. A política de uma versão só continua valendo — o custo constante é o
que garante que o orçamento nunca é atingido por acúmulo —, mas há folga real se algum dia
fizer sentido guardar a anterior.

E se um dia apertar, a primeira fatia a sair continua sendo a mesma: **ícones de perfil**,
sozinhos 26,9 % do total e a categoria que menos serve a um editor de vídeo.

---

## O que estes números mudam no plano

Recomendações para a Spec. Cada uma vira ADR.

1. **Servir os bytes de origem e converter para PNG no cliente.** ✅ **Decidido em
   03/09/2026** — ver [ADR 0001](adr/0001-formato-de-entrega-dos-assets.md), que revoga
   o princípio "PNG sempre" da §A.4. O CDN guarda o original, o indexador nunca re-encoda,
   e o botão "Baixar PNG" converte no navegador. Economia medida: ~76 % de armazenamento
   e egress por versão.
2. **ddragon como fonte única dos assets de campeão.** As dimensões empatam e o tarball
   entrega tudo em uma requisição. O cdragon entra para o que o ddragon não tem:
   chromas, loading vintage, emotes, ward skins, ícones de posição, elos.
3. **Filtrar TFT, challenges, missões, sprites e modo Classic** na entrada do indexador:
   44 % do peso de imagem do tarball está fora do escopo da v1.
4. **Baixar só `pt_BR` e `en_US`** dos 28 idiomas: −252 MB por patch.
5. **O adaptador cdragon nunca monta caminho.** Sempre parte do JSON. Está provado que
   caminho montado à mão dá 404, mesmo quando a documentação diz o contrário.
6. **Teste de contrato obrigatório por adaptador** cobrindo exatamente os caminhos que
   este spike mediu — foi assim que se descobriu que três caminhos documentados estavam
   mortos.
7. **Cortes de splash são dois tipos distintos**, com nomes canônicos próprios porque
   ddragon e cdragon usam os nomes trocados — ver
   [ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md).
8. **Política de versões:** guardar assets completos só da versão atual; a anterior fica
   com índice e URLs apontando para o ddragon, que serve splash e loading sem versão na
   URL (portanto sempre disponíveis). Com ~1,7 GB por versão no formato de origem, cabe
   folgado no plano gratuito de um R2.

---

## Ambiente — o acento no caminho quebra o pnpm (RESOLVIDO em 03/09/2026)

> **Resolvido.** O repositório foi movido para `D:\PROJETOS\PROJETO-ASSETS-LOL` e o
> `pnpm install` passou a terminar em exit 0. O espelho ASCII foi apagado. A regra que
> fica: **o caminho do repositório não pode ter caractere não-ASCII.** O diagnóstico
> abaixo é o registro de como isso foi isolado.

`pnpm install` **falha** dentro de um caminho com acento (era `D:\PROGRAMAÇÃO\…`) com
`ERR_PNPM_EPERM: operation not permitted, rename` ao instalar pacotes com binário
nativo (`esbuild`, `unrs-resolver`). Isolado com quatro testes controlados:

| Caminho | Resultado |
|---|---|
| `C:\…\lolassets-ascii-test` (ASCII, sem espaço) | instala |
| `C:\…\lol assets com espaco` (ASCII, com espaço) | instala |
| `C:\…\lolassets-ACENTUAÇÃO` (acentuado, sem espaço) | **EPERM** |
| `D:\PROGRAMAÇÃO\…\PROJETO-ASSETS-LOL` (acentuado) | **EPERM** |

Ou seja: **o acento no caminho é a causa**, não o espaço nem o antivírus. Seis tentativas
com limpeza dos diretórios temporários não resolveram.

Contorno usado enquanto durou: o workspace foi espelhado em `C:\…\lolassets-mirror`,
onde `pnpm install`, `eslint`, `tsc` e `vitest` rodaram e passaram; o `pnpm-lock.yaml`
gerado lá foi commitado. A CI roda em Linux e nunca foi afetada.

**Confirmação da causa.** Depois de mover o repositório para
`D:\PROJETOS\PROJETO-ASSETS-LOL` — mesma máquina, mesmo pnpm, mesmo Defender ligado,
mesmo lockfile — o `pnpm install` terminou em **exit 0**, com os postinstall de `esbuild`
e `unrs-resolver` executados. Foi a única variável alterada. O espelho foi apagado.

Descoberta relacionada: o pnpm 11 **não lê mais** o campo `pnpm` do `package.json`.
`onlyBuiltDependencies` virou `allowBuilds` no `pnpm-workspace.yaml` — sem isso o
`pnpm install` termina com `ERR_PNPM_IGNORED_BUILDS` e a CI quebraria.

---

## Perguntas de A.9 que continuam abertas

- Assets exclusivos da wiki (monstros, minions, torres, artes promocionais): dependem do
  consentimento da Weird Gloop. Nada foi testado. **Virou prioridade de projeto em
  03/09/2026** — a categoria HD da wiki é a única fonte conhecida acima de 1280×720
  ([ADR 0004](adr/0004-consentimento-da-wiki-e-teto-de-resolucao.md)).
- Base correta de `champion-abilities/…` no cdragon (ícones de habilidade por forma,
  tipo Jayce e Nidalee).
- Histórico: o cdragon serve patches antigos em `raw.communitydragon.org/{patch}/`, mas o
  layout muda entre versões — não medido nesta sessão.
- ~~Emblemas de elo: `static.developer.riotgames.com` não foi testado (§B.4).~~
  ✅ Testado no S4: `ranked-emblems-latest.zip` responde HTTP 200 com 61,5 MB.
