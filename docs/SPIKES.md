# SPIKES — números reais das fontes

> Medições feitas em **03/09/2026** contra o patch **16.17.1**.
> Tudo aqui foi medido, não estimado. Os scripts estão em `prototype/spikes/` e
> os resultados brutos em `prototype/spikes/results/*.json` (versionados como evidência).
> Onde a Parte B do [KICKOFF](KICKOFF.md) se mostrou errada, está marcado com **[CORRIGE B.x]**.

## Como reproduzir

```bash
uv sync --all-packages
python prototype/spikes/s1_ddragon.py   # baixa ~2,4 GB para prototype/spikes/.cache/
python prototype/spikes/s2_cdragon.py
python prototype/spikes/s3_volume.py    # depende dos resultados de S1 e S2
```

Todas as requisições usaram
`User-Agent: lol-assets-indexer/0.0.0-spike (+https://github.com/NihonCodingg/PROJETO-ASSETS-LOL; …)`,
concorrência 4 e backoff exponencial, conforme a regra 4 do [CLAUDE.md](../CLAUDE.md).

## Wiki — status do consentimento

**`WIKI_CONSENT_GRANTED = false`.** Nenhuma requisição a `wiki.leagueoflegends.com`
foi feita nesta sessão. `prototype/spikes/common.py` tem uma trava explícita que
levanta exceção se qualquer URL da wiki for passada, então a regra 3 é imposta pelo
código, não só pela disciplina. O spike **S4 não foi executado** e só será depois que
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

## O que estes números mudam no plano

Recomendações para a Spec. Cada uma vira ADR.

1. **Servir JPEG quando a fonte é JPEG, e oferecer PNG sob demanda.** Manter "PNG
   sempre" como padrão custa 3× mais armazenamento e banda para entregar exatamente os
   mesmos pixels — a fonte não tem alfa e o JPEG já está comprimido. Sugestão: botão
   "Baixar PNG" continua existindo e converte **no cliente** (canvas), como o protótipo
   vai demonstrar; o CDN guarda o original. Isso preserva a promessa da §A.4 sem pagar
   por ela no bucket. **Precisa da sua decisão** — é a única recomendação que contraria
   um princípio declarado não negociável.
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
7. **Política de versões:** guardar assets completos só da versão atual; a anterior fica
   com índice e URLs apontando para o ddragon, que serve splash e loading sem versão na
   URL (portanto sempre disponíveis). Com ~1,7 GB por versão no formato de origem, cabe
   folgado no plano gratuito de um R2.

---

## Ambiente — um bloqueio local encontrado nesta sessão

`pnpm install` **falha** dentro de `D:\PROGRAMAÇÃO\…` com
`ERR_PNPM_EPERM: operation not permitted, rename` ao instalar pacotes com binário
nativo (`esbuild`, `unrs-resolver`). Isolado com três testes controlados:

| Caminho | Resultado |
|---|---|
| `C:\…\lolassets-ascii-test` (ASCII, sem espaço) | instala |
| `C:\…\lol assets com espaco` (ASCII, com espaço) | instala |
| `C:\…\lolassets-ACENTUAÇÃO` (acentuado, sem espaço) | **EPERM** |
| `D:\PROGRAMAÇÃO\…\PROJETO-ASSETS-LOL` (acentuado) | **EPERM** |

Ou seja: **o acento no caminho é a causa**, não o espaço nem o antivírus. Seis tentativas
com limpeza dos diretórios temporários não resolveram.

Contorno usado nesta sessão: o workspace foi espelhado em `C:\…\lolassets-mirror`,
onde `pnpm install`, `eslint`, `tsc` e `vitest` rodaram e passaram; o `pnpm-lock.yaml`
gerado lá foi commitado. A CI roda em Linux e não é afetada.

**Precisa da sua decisão:** mover o repositório para um caminho sem acento (por
exemplo `D:\PROJETOS\PROJETO-ASSETS-LOL`) resolve de vez e é o que eu recomendo.
Enquanto isso, o desenvolvimento Python funciona normalmente no caminho atual.

Descoberta relacionada: o pnpm 11 **não lê mais** o campo `pnpm` do `package.json`.
`onlyBuiltDependencies` virou `allowBuilds` no `pnpm-workspace.yaml` — sem isso o
`pnpm install` termina com `ERR_PNPM_IGNORED_BUILDS` e a CI quebraria.

---

## Perguntas de A.9 que continuam abertas

- Assets exclusivos da wiki (monstros, minions, torres, artes promocionais): dependem do
  consentimento da Weird Gloop. Nada foi testado.
- Base correta de `champion-abilities/…` no cdragon (ícones de habilidade por forma,
  tipo Jayce e Nidalee).
- Histórico: o cdragon serve patches antigos em `raw.communitydragon.org/{patch}/`, mas o
  layout muda entre versões — não medido nesta sessão.
- Emblemas de elo: `static.developer.riotgames.com` não foi testado (§B.4).
