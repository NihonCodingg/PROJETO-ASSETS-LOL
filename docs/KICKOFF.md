# LoL Assets — Documento de Kickoff para o Claude Code

> Este arquivo unifica tudo o que foi definido antes de escrever código: o processo de trabalho, os padrões de engenharia, a ideia cristalizada (Parte A) e a pesquisa verificada (Parte B). Ele deve ser commitado em `docs/KICKOFF.md` no repositório e é a fonte de verdade até a Spec existir.

**Repositório oficial:** `https://github.com/NihonCodingg/PROJETO-ASSETS-LOL.git`
**Regra absoluta:** tudo — código, docs, decisões, resultados de spikes, evidências de consentimento, relatórios de sessão — é registrado nesse repositório. Nada vive só no chat ou só na máquina local. Todo commit é enviado (`git push`) ao final de cada bloco de trabalho.

---

## Parte 0 — Como vamos trabalhar

### 0.1 As 7 etapas e onde estamos

| Etapa | Status | Responsável | Entregável |
|---|---|---|---|
| 1. Ideia | ✅ Concluída | Humano + Claude (chat) | Parte A deste documento |
| 2. Pesquisa | ✅ Concluída | Claude (chat) | Parte B deste documento |
| 3. Protótipo + Spikes | ⏳ Próxima | Claude Code | `prototype/` descartável + `docs/SPIKES.md` com números reais |
| 4. Spec / PRD | ⏳ | Claude Code escreve, humano aprova | `docs/SPEC.md` |
| 5. Tickets | ⏳ | Claude Code escreve, humano aprova | `docs/TICKETS.md` (≤ 500 linhas de lógica cada) |
| 6. Execução | ⏳ | Claude Code, um ticket por sessão | PRs pequenos |
| 7. QA / Review | ⏳ | CI + humano | Testes verdes, preview na Vercel, review |

**Regra de ouro:** o Claude Code não avança de etapa sem aprovação explícita do humano. Cada etapa termina com um resumo do que foi feito, o que foi assumido e o que precisa de decisão.

### 0.2 Regras para o Claude Code (vão para o `CLAUDE.md` do repo)

1. Ler `docs/KICKOFF.md` (este arquivo) antes de qualquer coisa. Depois que existirem, `docs/SPEC.md` e `docs/TICKETS.md` têm precedência sobre ele.
2. Nunca inventar um endpoint, path ou formato de asset. Se não está na Parte B, testar primeiro e registrar o resultado em `docs/SPIKES.md`.
3. Nenhuma requisição automatizada à wiki (`wiki.leagueoflegends.com`) enquanto `WIKI_CONSENT_GRANTED` não estiver documentado em `docs/SPIKES.md` com data e evidência. O adaptador pode existir, mas desligado por flag.
4. Requisições ao ddragon e cdragon sempre com `User-Agent: lol-assets-indexer/{versão} (+https://github.com/NihonCodingg/PROJETO-ASSETS-LOL; contato do mantenedor)`, concorrência ≤ 4, backoff exponencial em 429/5xx.
5. PRs com no máximo ~500 linhas de lógica (exclui lockfiles, fixtures e snapshots). Se um ticket não cabe, dividir o ticket, não inflar o PR.
6. TDD nos módulos de lógica (indexador, fusão, conversão, busca). UI pode ter testes mais leves, mas o fluxo "buscar → baixar" tem teste e2e.
7. Nada de segredo no código. Variáveis de ambiente documentadas em `.env.example`.
8. Commits em Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`). Idioma do código e dos identificadores: inglês. Idioma de docs e commits: português.
9. Ao terminar qualquer tarefa, relatar em português: o que foi feito, o que foi assumido, o que ficou pendente, e qual o próximo passo sugerido. Esse relatório também é salvo em `docs/sessoes/AAAA-MM-DD-{tema}.md` e commitado.
10. Se algo na Parte B se mostrar errado na prática, corrigir `docs/PESQUISA` via PR com a evidência, não contornar em silêncio.
11. **Git:** remoto único é `https://github.com/NihonCodingg/PROJETO-ASSETS-LOL.git`. `main` só recebe merge via PR. Trabalho em branches `feat/T-XX-descricao`, `docs/...`, `chore/...`. Etapas 1–4 (bootstrap, spikes, protótipo, spec) podem ir direto na `main` porque ainda não há código de produção; a partir dos tickets, só PR. Push ao final de cada bloco, sem exceção — trabalho não enviado é trabalho que não existe.
12. Decisões de arquitetura viram ADRs em `docs/adr/NNNN-titulo.md` (contexto, decisão, consequências). A Spec referencia os ADRs, não os repete.

### 0.3 Padrões de engenharia

**Monorepo** (pnpm workspaces + uv para Python):

```
PROJETO-ASSETS-LOL/
├── CLAUDE.md                 # regras da §0.2
├── docs/
│   ├── KICKOFF.md            # este arquivo
│   ├── SPIKES.md             # números reais dos spikes
│   ├── SPEC.md               # etapa 4
│   ├── TICKETS.md            # etapa 5
│   ├── adr/                  # decisões de arquitetura
│   └── sessoes/              # relatório de cada sessão do Claude Code
├── apps/
│   ├── web/                  # Next.js (App Router, TS, Tailwind) — Vercel
│   └── api/                  # FastAPI — Railway/Fly
├── packages/
│   ├── indexer/              # Python: adaptadores + fusão + conversão + publicação
│   └── schema/               # JSON Schema do índice + tipos TS gerados + modelos Pydantic gerados
├── prototype/                # descartável, apagado após a Spec
└── .github/workflows/        # ci.yml (lint+test), index.yml (agendado por patch)
```

**Stack fixada:**
- Front: Next.js 15+, TypeScript strict, Tailwind, Fuse.js para busca no cliente, JSZip apenas como fallback offline.
- API: Python 3.12+, FastAPI, Pydantic v2, httpx, Pillow, uvicorn. Testes com pytest.
- Indexador: mesmo Python; CLI com Typer; roda em GitHub Actions.
- Storage: bucket compatível com S3 (Cloudflare R2 como padrão) + CDN. Localmente, MinIO ou pasta em disco.
- Qualidade: ruff + mypy (Python), eslint + tsc (TS), Vitest + Playwright (web), GitHub Actions em todo PR.

**Contrato central — o índice.** Um `assets-{versão}.json` (ou NDJSON, se passar de 10 MB) com um registro por asset:

```
id, type, version, championKey?, skinId?, itemId?, names{pt_BR,en_US}, aliases[],
tags[], source, sourceUrl, storageKey, width, height, format, bytes, sha256
```

O schema vive em `packages/schema` e é a única coisa que front, API e indexador compartilham. Mudança no schema = ADR + versão nova.

**Princípios de system design que a Spec deve respeitar:**
- Indexação separada da consulta; o tráfego de usuário nunca toca ddragon/cdragon/wiki.
- Tudo que puder ser pré-gerado, é pré-gerado no indexador (PNGs, zips por categoria, índice de busca).
- A API é fina: serve índice, gera zips sob demanda com cache por hash da seleção, e expõe `/health` e `/versions`.
- Front carrega o índice uma vez por versão e busca no cliente; imagens vêm direto do CDN.
- Degradação graciosa: se a API cair, busca e download individual continuam funcionando (só o zip sob demanda para).
- Observabilidade mínima desde o início: logs estruturados, métricas de indexação (assets por fonte, falhas, duração), alerta quando o teste de contrato de uma fonte falha.

### 0.4 Definição de pronto (por ticket)

- Código + testes no PR; CI verde.
- Nenhum `TODO` sem issue vinculada.
- Documentação atualizada se o comportamento observável mudou.
- Preview na Vercel (web) ou ambiente de staging (API) funcionando.
- Relatório final da sessão em português.

---

## Parte A — Ideia cristalizada

*Numeração A.x pertence a esta parte.*

## A.1. Objetivo

Um site público onde qualquer editor de vídeo/thumbnail de League of Legends encontra e baixa, em PNG e na melhor qualidade disponível, qualquer asset visual do jogo — em segundos, sem login, sem navegar por wiki ou Google.

## A.2. Usuário

**Quem:** editores de vídeo, criadores de thumbnail, designers de overlay e streamers de LoL. Nível técnico variado; muitos não sabem o que é "ddragon".

**Situação:** está com Premiere/After Effects/Photoshop aberto, no meio de uma edição, e precisa de um asset específico agora.

**Trabalho a ser feito (job to be done):**
- "Preciso do square do Jax pra colocar no canto do vídeo."
- "Preciso da splash da skin Jax Deus da Guerra em alta pra thumbnail."
- "Preciso de todos os ícones de item pra montar uma build animada."
- "Preciso do ícone de Diamante IV pro vídeo de elo."
- "Esse vídeo é do patch antigo, preciso do square antigo do Aatrox."

**O que o usuário NÃO quer:** ler texto, criar conta, aprender uma ferramenta, lidar com JPG/WebP, descobrir que a imagem veio em 64×64.

## A.3. Escopo

### Dentro (v1)

Catálogo completo de assets visuais, sempre na maior resolução disponível entre as fontes:

| Categoria | Assets | Fonte provável |
|---|---|---|
| Campeões | square, splash (todas as skins, centralizada e não centralizada), loading screen, ícones de habilidade (P/Q/W/E/R), ícone de passiva | ddragon + cdragon |
| Skins | splash, tile, chroma icons, splash de skins lendárias/ultimate com variações | cdragon |
| Itens | ícone de todos os itens, filtro por comprável / mapa | ddragon + cdragon |
| Runas | ícone de cada runa e de cada árvore | ddragon |
| Feitiços | ícones de feitiços de invocador | ddragon |
| Ícones de perfil | todos os profile icons | ddragon + cdragon |
| Emotes | todos os emotes | cdragon |
| Ranks | emblemas de elo (Ferro → Desafiante), divisões | cdragon |
| Ward skins | ícones de sentinela | cdragon |
| Mapas | minimapa e imagens dos mapas (Summoner's Rift, ARAM, etc.), mapas por temporada | ddragon + cdragon + wiki |
| Diversos | ícones de posição/lane, moedas (RP, essência azul), logo do jogo | cdragon + wiki |
| Artes HD | renders, artes promocionais, concept art, splashes em alta definição | wiki (categoria de imagens HD) |
| Unidades não-campeão | monstros (Barão, Arauto, dragões), minions, torres, inibidores, nexus | wiki |
| Histórico | squares/splashes de versões antigas de campeões e skins removidas | wiki + ddragon (versões antigas) |

**Fontes de dados, em ordem de prioridade:**
1. **Data Dragon (ddragon)** — oficial, versionado por patch, base do catálogo.
2. **Community Dragon (cdragon)** — extraído do cliente, maior resolução, cobre o que o ddragon não expõe.
3. **League of Legends Wiki (wiki.leagueoflegends.com)** — MediaWiki hospedado pela Weird Gloop. Fonte secundária para artes HD, unidades não-campeão, histórico e curadoria de nomes. Acessada via `api.php` apenas pelo indexador, nunca em tempo real pelo usuário. Quando o mesmo asset existe em mais de uma fonte, vence a de maior resolução; a fonte usada fica registrada no índice e visível no card.

Funcionalidades:
- Busca instantânea tolerante a erro (acento, apóstrofo, apelidos: "mf", "kaisa", "wukong", "tf", "j4").
- Navegação por categoria com filtros (função, lane, comprável, árvore de runa, elo…).
- Seletor de versão/patch, com a versão atual como padrão.
- Preview em tamanho real com dimensões visíveis.
- Download individual em PNG com nome de arquivo previsível.
- Download em lote (zip): por seleção, por categoria, por campeão ("tudo do Jax").
- Copiar URL direta do PNG.
- Página "Sobre" com créditos e aviso legal.

### Fora (v1)

- Stats, builds, patch notes, guias, dados de partida.
- Contas, login, favoritos sincronizados, histórico.
- Edição de imagem (remover fundo, recortar, redimensionar).
- Upload de assets pelo usuário.
- Assets de outros jogos da Riot (TFT, Wild Rift, Valorant) — candidatos a v2.
- API pública documentada para terceiros — candidata a v2.

## A.4. Princípios de UX (não negociáveis)

1. **Busca é a home.** Campo de busca com foco automático; resultados aparecem enquanto digita.
2. **Regra dos 3 cliques.** Do carregamento do site ao arquivo salvo no disco: no máximo 3 cliques.
3. **Melhor fonte disponível, sem re-encode.** *(Revoga "PNG sempre" em 03/09/2026 — ver [ADR 0001](adr/0001-formato-de-entrega-dos-assets.md).)* O CDN guarda e serve os bytes originais; o indexador nunca re-encoda. O botão "Baixar PNG" converte no navegador (canvas) no momento do clique, e o card oferece as duas opções — original e PNG. Assets cuja origem já é PNG seguem PNG de ponta a ponta; runas e stat mods têm canal alfa e nunca podem virar JPG. Nunca há upscale. Motivo: os spikes mediram que converter os JPEGs da fonte para PNG multiplica o armazenamento por 5,7× sem ganhar um pixel, porque a fonte não tem canal alfa ([SPIKES](SPIKES.md)).
4. **Nome de arquivo previsível.** `Jax_square.png`, `Jax_skin07_splash_centered.png`, `Item_3031_Infinity_Edge.png`, `Rank_Diamond_IV.png`.
5. **Zero texto obrigatório.** Nenhuma tela exige leitura pra ser usada.
6. **Funciona com o Premiere aberto.** Leve, rápido, sem animação pesada, atalho de teclado pra busca (`/`).
7. **Transparência de qualidade.** Cada asset mostra **formato**, resolução e fonte antes do download.
8. **`splash` e `centered` são cortes diferentes.** Os dois entram no catálogo. O padrão é `centered` (1280×720), por ser o maior. Os nomes são invertidos entre ddragon e cdragon — ver [ADR 0002](adr/0002-nomes-canonicos-de-corte-de-splash.md).

## A.5. Requisitos não funcionais

- **Performance:** busca responde em < 50 ms (índice no cliente); imagem abre em < 1 s.
- **Custo:** o site precisa ser sustentável de graça ou quase. Consequência: os assets são servidos como estáticos via CDN nos bytes de origem, sem conversão no servidor nem por requisição ([ADR 0001](adr/0001-formato-de-entrega-dos-assets.md)).
- **Resiliência:** se ddragon/cdragon caírem, o site continua funcionando com o último índice publicado.
- **Atualização:** novo patch refletido em até 24 h, sem intervenção manual.
- **Abuso:** rate limit em geração de zip; zips de categoria inteira pré-gerados.
- **Legal:** aviso obrigatório da Riot (Legal Jibber Jabber) visível; sem monetização direta dos assets; sem "Riot", "League of Legends" ou "LoL" no nome público do produto — o nome exibido está [A DECIDIR] até o lançamento ([ADR 0003](adr/0003-nome-publico-do-produto.md)); repositório e pacotes internos ficam como estão. Assets vindos da wiki exibem crédito à League of Legends Wiki / Weird Gloop (o texto da wiki é CC BY-SA; as imagens continuam sendo propriedade da Riot).
- **Etiqueta com a wiki:** indexador usa a API oficial do MediaWiki com User-Agent identificado (nome do projeto + contato), rate limit conservador, cache agressivo e respeito aos termos de uso da Weird Gloop. O site nunca faz hotlink de imagens da wiki — tudo é copiado pro storage próprio no momento da indexação.
- **Acessibilidade básica:** navegável por teclado, contraste adequado, alt em todas as imagens.

## A.6. Decisões de arquitetura (nível de ideia)

- **Indexação separada da consulta.** Dados mudam por patch, não por usuário. Um job de indexação roda por patch, gera o índice normalizado e os PNGs, e publica tudo em storage estático. O tráfego dos usuários não toca a Riot.
- **Front-end:** Next.js + TypeScript + Tailwind, hospedado na Vercel. Busca no cliente sobre o índice.
- **API:** Python + FastAPI. Responsabilidades: servir índices, gerar zips sob demanda (com cache), expor metadados. Serve de portfólio de back-end.
- **Indexador:** Python (mesmo repositório da API), com Pillow para conversão. Roda como GitHub Action agendada. Estruturado em **adaptadores por fonte** (`ddragon`, `cdragon`, `wiki`), cada um produzindo assets no mesmo schema; uma etapa de **fusão** deduplica por identidade (campeão + skin + tipo) e escolhe a melhor resolução. Isso permite adicionar ou remover fontes sem tocar no resto.
- **Storage/CDN:** bucket com egress barato ou gratuito (ex.: Cloudflare R2) + CDN na frente, servindo PNGs e zips pré-gerados.
- **Monorepo:** `apps/web` (Next), `apps/api` (FastAPI), `packages/indexer` (Python), `packages/schema` (contrato do índice compartilhado).

## A.7. Métricas de sucesso

- Métrica pessoal: o autor para de abrir Google/wiki durante edições.
- Tempo mediano da chegada ao primeiro download < 20 s.
- ≥ 95 % das buscas por nome de campeão retornam o campeão certo em primeiro lugar.
- Novo patch refletido em ≤ 24 h em 100 % dos casos.
- Custo mensal de infra próximo de zero até ~10 k usuários/mês.

## A.8. Riscos conhecidos

| Risco | Mitigação |
|---|---|
| cdragon muda paths sem aviso | Indexador com testes de contrato; alerta quando um path some |
| Assets com resolução baixa na fonte | Mostrar resolução no card; preferir cdragon quando existir |
| Custo de banda com splashes de alta resolução | R2 (egress gratuito) + CDN; zips pré-gerados |
| Abuso de geração de zip | Rate limit por IP; limite de itens por zip; cache por hash da seleção |
| Questão legal com a Riot | Seguir Legal Jibber Jabber; aviso visível; sem ads sobre os assets na v1 |
| Nomes/IDs inconsistentes entre fontes | Tabela de aliases mantida no indexador e coberta por testes |
| Wiki muda convenção de nomes ou estrutura de categorias | Adaptador da wiki isolado; testes de contrato; a wiki nunca é a única fonte de um asset essencial |
| Wiki bloqueia o indexador por excesso de requisições | User-Agent identificado, rate limit baixo, indexação incremental (só o que mudou desde o último patch) |
| Confusão de licença (CC BY-SA vs. assets da Riot) | Crédito visível por fonte; página "Sobre" explica as duas licenças |

## A.9. Perguntas em aberto (para a Pesquisa)

- Quais assets existem só no cdragon, e em que resolução exata?
- O ddragon versiona tudo por patch? O cdragon mantém histórico ou só "latest"?
- Existem PNGs com transparência na fonte (ícones de item, runas) ou tudo tem fundo?
- Qual o tamanho total, em GB, de "tudo" na versão atual? Isso define custo de storage.
- O cdragon tem limite de requisições ou pede User-Agent específico?
- A API da wiki (`api.php`) está aberta? Quais módulos funcionam (`allimages`, `categorymembers`, `imageinfo`)? Existe consulta estruturada via Bucket/Cargo?
- Quais são exatamente as convenções de nome de arquivo da wiki (`_OriginalSquare`, `_{Skin}Loading`, `_{Skin}Centered`, `_HD`) e elas cobrem 100 % dos campeões?
- O que a categoria de imagens HD contém, em que resolução e quantos arquivos?
- Termos de uso da Weird Gloop permitem indexação automatizada? Qual rate limit é aceitável?

## A.10. Próxima etapa

**Pesquisa (etapa 2):** produzir `PESQUISA.md` com inventário verificado de endpoints (ddragon e cdragon), formato e resolução de cada tipo de asset, pegadinhas de ID, política de uso e estimativa de volume. Só depois disso: protótipo descartável e Spec.


---

## Parte B — Pesquisa verificada das fontes

*Numeração B.x pertence a esta parte. Verificada em 03/09/2026.*

## B.0. Resumo executivo — o que muda o plano

1. **A wiki proíbe uso automatizado sem consentimento prévio.** Os Termos de Uso da Weird Gloop listam "usar os Sites de forma automatizada sem consentimento prévio da empresa" como uso indevido. Em março/2026 eles publicaram um post dizendo que ~95 % dos problemas de servidor em wikis vêm de scrapers. **Decisão necessária:** a wiki sai da v1 como fonte automatizada. Pedimos consentimento em paralelo (contato/Discord da Weird Gloop) e o adaptador só é ligado se autorizado. Ver §4.
2. **O Data Dragon tem um tarball com tudo por patch** (`dragontail-{versão}.tgz`, ~1 GB). O indexador baixa um arquivo por patch em vez de fazer milhares de requisições. Isso simplifica muito o adaptador ddragon.
3. **O Community Dragon tem listagem de diretórios em JSON** (prefixo `json/`) e JSON de campeões com o caminho de cada asset. Dá pra descobrir assets programaticamente, sem chutar paths.
4. **A Riot exige um texto legal específico** visível no produto e registro no Developer Portal quando o produto serve jogadores. Ver §5.
5. **Emblemas de elo têm zip oficial da Riot** no Developer Portal — fonte melhor que cdragon pra ranks.

## B.1. Fonte primária — Data Dragon (ddragon)

**Base:** `https://ddragon.leagueoflegends.com`
**Natureza:** oficial, público, sem chave, versionado por patch. Atualização é manual pela Riot e pode atrasar 1–2 dias depois do patch.
**Versão atual na documentação:** `16.17.1`.

### B.1.1 Descoberta

| O quê | URL |
|---|---|
| Lista de versões (mais recente primeiro) | `/api/versions.json` |
| Versão em uso por região | `/realms/br.json` (também `na`, `euw`, etc.) |
| Idiomas disponíveis (inclui `pt_BR`) | `/cdn/languages.json` |
| Tarball completo do patch | `/cdn/dragontail-{versão}.tgz` (patch 10.10 é `.zip`) |

**Pegadinha:** pode haver mais de um build por patch (ex.: `16.17.1`, `16.17.2`) quando o primeiro sai com erro. Usar sempre o build mais recente de cada patch. A versão 9.22.1 é conhecida por estar quebrada.

### B.1.2 Dados (JSON)

Formato: `/cdn/{versão}/data/{idioma}/{arquivo}.json`

| Arquivo | Conteúdo |
|---|---|
| `champion.json` | Resumo de todos os campeões: `id` (nome interno), `key` (id numérico), `name`, `title`, `tags`, `image` |
| `champion/{Id}.json` | Campeão completo: `skins[]` (`id`, `num`, `name`, `chromas`, `parentSkin`), `spells[]`, `passive`, lore |
| `item.json` | Todos os itens: `name`, `gold.purchasable`, `maps{}`, `tags`, `image`, `from`, `into` |
| `summoner.json` | Feitiços de invocador |
| `profileicon.json` | Ícones de perfil |
| `runesReforged.json` | Runas e árvores (caminho de ícone dentro de `img/`) |
| `mode/classic/champion.json` | Campeões do modo League Classic, com chave própria (ex.: `Jade_Ahri`) pra não colidir com os normais |

### B.1.3 Imagens

| Asset | URL | Formato | Versionado? |
|---|---|---|---|
| Square do campeão | `/cdn/{v}/img/champion/{Id}.png` | PNG | Sim |
| Splash | `/cdn/img/champion/splash/{Id}_{num}.jpg` | JPG | **Não** (sem versão na URL) |
| Loading screen | `/cdn/img/champion/loading/{Id}_{num}.jpg` | JPG | **Não** |
| Passiva | `/cdn/{v}/img/passive/{arquivo}` (nome vem do JSON) | PNG | Sim |
| Habilidade | `/cdn/{v}/img/spell/{arquivo}` (nome vem do JSON) | PNG | Sim |
| Item | `/cdn/{v}/img/item/{itemId}.png` | PNG | Sim |
| Feitiço de invocador | `/cdn/{v}/img/spell/Summoner{Nome}.png` | PNG | Sim |
| Ícone de perfil | `/cdn/{v}/img/profileicon/{id}.png` | PNG | Sim |
| Runa | `/cdn/img/{caminho do runesReforged.json}` | PNG | Não |
| Minimapa | `/cdn/{v}/img/map/map{mapId}.png` | PNG | Sim |
| Sprites (atlas) | `/cdn/{v}/img/sprite/{grupo}{n}.png` | PNG | Sim |
| Ícones de placar (legado) | `/cdn/5.5.1/img/ui/*.png` | PNG | Fixo |
| Imagens do modo Classic | `/cdn/{v}/img/mode/classic/...` | — | Sim |

### B.1.4 Regras de skin (do `champion/{Id}.json`)

- `num` é o número usado no nome do arquivo de splash/loading.
- Nem toda entrada de `skins[]` tem splash: **chromas não têm**. Chroma é identificado pelo campo `parentSkin` (skins base não têm esse campo). Filtrar `parentSkin` fora antes de gerar URLs.
- `chromas: true` na skin base indica que ela possui chromas.

### B.1.5 Pegadinhas de identidade

- Nome interno ≠ nome exibido. Usar sempre `id` do JSON para URLs e `name` para exibição. Casos conhecidos: `MonkeyKing` → Wukong, `Nunu` → Nunu & Willump, `Renata` → Renata Glasc, `Belveth`, `Chogath`, `KSante`, `Kaisa`, `Khazix`, `Kogmaw`, `Leblanc`, `RekSai`, `Velkoz`, `DrMundo`, `JarvanIV`, `MasterYi`, `MissFortune`, `TahmKench`, `TwistedFate`, `XinZhao`, `AurelionSol`, `LeeSin`, `FiddleSticks` (grafia varia por versão).
- `key` (numérico, ex.: Jax = 24) é o ID estável entre fontes — é ele que o cdragon usa. **Usar `key` como chave de fusão entre ddragon e cdragon.**
- Tabela de aliases pra busca (mf, tf, j4, asol, kaisa, wukong, mundo...) não existe em nenhuma fonte; é responsabilidade nossa.

### B.1.6 Itens — filtros

- `maps["11"] == true` → disponível no Summoner's Rift; `maps["12"]` → ARAM; `maps["30"]` → Arena.
- `gold.purchasable == false` → item de missão/interno/legado.
- Itens de modos antigos, Ornn upgrades e itens removidos permanecem no JSON de versões antigas — bom pra histórico, ruim pra listagem padrão. Filtro padrão: comprável e presente no SR; toggle "mostrar tudo".

### B.1.7 Qualidade

- Squares (120×120), ícones de item/habilidade/feitiço (64×64) e ícones de perfil são pequenos. **Pra esses tipos, o cdragon deve ser a fonte preferida e o ddragon o fallback.**
- Splash (~1215×717) e loading (~308×560) são JPG. Não existe versão PNG na fonte; a conversão só evita perda adicional. **[A VERIFICAR]** dimensões exatas por tipo com uma amostra real.

## B.2. Fonte secundária — Community Dragon (cdragon)

**Base:** `https://raw.communitydragon.org/{versão}/` onde `{versão}` é `latest`, `pbe` ou um patch (ex.: `15.1`, `8.23`).
**Natureza:** projeto comunitário open-source, criado sob a política Legal Jibber Jabber da Riot, reconhecido no Developer Portal (não afeta chave de API). Tem Patreon; mantido por voluntários. Existe também `cdn.communitydragon.org` (mais estruturado), mas **a própria documentação avisa que o CDN será descontinuado** — usar só o `raw`.

### B.2.1 Como navegar programaticamente

- Qualquer diretório tem listagem JSON: prefixar o caminho com `json/`. Ex.: `https://raw.communitydragon.org/json/latest/game/`.
- Barra de busca do site aceita regex; existe lista completa de arquivos exportados por patch.
- Ferramentas prontas pra baixar diretórios inteiros: `cd-dd` e `snip-snip` (GitHub). Podem servir de referência pro adaptador.
- **Regra de mapeamento:** caminhos nos JSONs do cliente no formato `/lol-game-data/assets/<Path>` viram `plugins/rcp-be-lol-game-data/global/default/<path em minúsculas>`.

### B.2.2 JSON de dados (ponto de partida do adaptador)

Diretório: `plugins/rcp-be-lol-game-data/global/default/v1/`
Contém JSONs de campeões (`champions/{key}.json`, com caminhos de todos os assets da ficha, inclusive por skin), skins, itens, ícones de perfil, emotes, ward skins, skinlines, mapas, filas, etc. **Os caminhos dentro desses JSONs são a fonte de verdade — não montar URLs na mão, porque o layout muda por campeão e a doc avisa que nem todos foram migrados.**

### B.2.3 Assets (caminhos documentados)

Prefixo comum `P = plugins/rcp-be-lol-game-data/global/default`

| Asset | Caminho | Observação |
|---|---|---|
| Square (skin base) | `P/v1/champion-icons/{key}.png` | Maior que o ddragon |
| Square (todas as skins, "tile") | `P/v1/champion-tiles/{key}/{skinId}.jpg` | Como na loja |
| Retrato redondo (todas as skins) | `game/assets/characters/{nome}/hud/` | |
| Splash centralizada | `P/v1/champion-splashes/{key}/{skinId}.jpg` | Como no perfil |
| Splash não centralizada | `P/v1/champion-splashes/uncentered/{key}/{skinId}.jpg` | Como na coleção |
| Fundo de skin ultimate (animado) | `P/v1/summoner-backdrops/` | |
| Chromas | `P/v1/champion-chroma-images/` | Como no champ select |
| Loading screen (+ bordas LE) | `P/assets/characters/{nome}/skins/` ou `game/assets/characters/{nome}/skins/` | |
| Ícones de habilidade (todas as formas) | `game/assets/characters/{nome}/hud/icons2d/` | Cobre Jayce/Nidalee/etc. |
| Ícones de perfil | `P/v1/profile-icons/{id}.jpg` | |
| Runas | `P/v1/perk-images/styles/` | Stat mods em `perk-images/statmods/` |
| Ward skins | `P/content/src/leagueclient/wardskinimages/` | |
| Emotes | `P/assets/loadouts/summoneremotes/` | |
| Ícones de modo de jogo | `P/content/src/leagueclient/gamemodeassets/` | |
| Fundos de loading screen | `game/assets/ux/loadingscreen/` | |
| Itens | `P/assets/items/icons2d/` | Nome de arquivo vem do JSON de itens |
| Hextech / loot | `plugins/rcp-fe-lol-loot/.../loot_item_icons/`, `P/assets/loot/`, `P/v1/hextech-images/` | |
| Ícones de posição/lane | `plugins/rcp-fe-lol-clash/.../position-selector/positions/` (PNG), `plugins/rcp-fe-lol-static-assets/.../svg/` (SVG) | Várias cores |
| Emblemas de elo (partes) | `P/content/src/leagueclient/rankedcrests/{tier}/images/` | Ver §5.3 pro zip oficial |
| Ícones de elo | `plugins/rcp-fe-lol-shared-components/global/default/` | |
| Mini emblemas de elo | `plugins/rcp-fe-lol-static-assets/.../ranked-mini-crests/` | |
| Bordas de loading por elo | `game/assets/ux/loadingscreen/` | |
| Ícones de buff/debuff | `game/data/spells/icons2d/` | |
| Ícones de maestria | `game/assets/ux/mastery/` | |
| Retratos de monstros/dragões | `game/data/images/ui/momentstimelineportraits/`, `game/assets/ux/announcements/` | Cobre parte do que a wiki cobria |
| Ícones de ouro/CS do placar | `plugins/rcp-fe-lol-match-history/global/default/` | |
| Bandeiras de Clash | `P/assets/loadouts/summonerbanners/flags/` | |

### B.2.4 Limitações documentadas

- Imagens que vivem em atlas (ex.: `clarity_hudatlas.png`) **não** são fornecidas separadas. Ignorar na v1.
- Nomes de chroma não existem no cdragon (vêm da loja). Chromas entram com o nome da skin-mãe + número.
- Nenhuma política de rate limit publicada. **Regra nossa:** User-Agent identificado, concorrência ≤ 4, backoff em 429/5xx, e nunca baixar `game/` inteiro — só os diretórios listados acima.
- Versões antigas existem em `raw.communitydragon.org/{patch}/`, mas a doc avisa que layouts mudam entre versões. Histórico pelo cdragon é "melhor esforço"; histórico confiável é o ddragon.

## B.3. Fonte terciária — League of Legends Wiki

**Base:** `https://wiki.leagueoflegends.com/en-us/`
**Natureza:** MediaWiki 1.45.3, hospedado pela Weird Gloop (mesma organização das wikis de RuneScape e Minecraft). Conteúdo textual CC BY-SA 3.0; imagens são propriedade da Riot. O rodapé cita "additional terms may apply" apontando pra página de licenciamento da Weird Gloop.

### B.3.1 O que foi observado na página inicial

- Convenção de nomes de arquivo consistente: `{Campeão}_OriginalSquare.png`, `{Campeão}_{Skin}Loading.jpg`, `{Campeão}_{Skin}Centered.jpg`, sufixo `_HD` em algumas artes.
- Thumbnails seguem o padrão MediaWiki `images/thumb/{arquivo}/{largura}px-{arquivo}`; o original fica em `images/{arquivo}`.
- Existe a categoria "High definition images" (menu "HD Artwork") e um link "View buckets" na página — a wiki usa a extensão **Bucket** da Weird Gloop, que expõe dados estruturados com API própria (documentada em `meta.weirdgloop.org/w/Extension:Bucket/Api`).
- Cobertura que as outras fontes não têm: monstros, minions, torres, mapas por temporada, artes promocionais, skins removidas, versões antigas de campeões.

### B.3.2 Termos de uso — bloqueio pra v1

Os Termos da Weird Gloop (atualizados em 31/01/2025) listam como uso indevido:

- usar os Sites de forma automatizada **sem consentimento prévio da empresa**;
- causar estresse na infraestrutura ou tráfego;
- usar o conteúdo fora das licenças deles.

Contexto adicional: post do blog deles (13/03/2026) sobre scrapers descreve ~250 milhões de requisições de bot por mês e atribui a maior parte dos incidentes a scraping não identificado. Ou seja: mesmo uma indexação "educada" sem autorização é exatamente o que eles estão combatendo.

**Decisão recomendada:**
1. **v1 sem adaptador da wiki ativo.** O código do adaptador pode existir atrás de uma flag, mas desligado.
2. **Pedir consentimento formal** via `weirdgloop.org/contact` ou o Discord da wiki, explicando: o que o projeto é, que só o indexador acessa (nunca o usuário), volume estimado por patch, User-Agent, e que haverá crédito visível. Isso é uma tarefa do humano (você), não do Claude Code.
3. **Se autorizado:** ligar o adaptador usando `api.php` (`list=categorymembers`, `prop=imageinfo`) e/ou a API do Bucket, com o rate limit que eles definirem.
4. **Se negado ou sem resposta:** os assets exclusivos da wiki (monstros, minions, torres, promocionais) ficam em v2 ou são cobertos parcialmente pelo cdragon (§2.3 — retratos de monstros e dragões existem lá).

**[A VERIFICAR — só depois de autorizado]** `api.php` está aberto? Quais módulos respondem? A categoria HD tem quantos arquivos e em que resolução?

## B.4. Emblemas de elo — fonte oficial

O Developer Portal da Riot disponibiliza zips oficiais: `ranked-emblems-latest.zip` (emblemas atuais de todos os tiers), além de `ranked-emblems.zip`, `ranked-positions.zip` e `tier-icons.zip` (versões antigas). São arquivos estáticos em `static.developer.riotgames.com/docs/lol/`. **Usar como fonte primária de ranks**, com cdragon como fonte das partes/variações.

## B.5. Legal — Riot Games

Fonte: Developer API Policy no Developer Portal (`developer.riotgames.com/docs/lol`) e página Legal Jibber Jabber (`riotgames.com/en/legal`).

### B.5.1 Obrigações que se aplicam a nós

- **Texto legal obrigatório**, visível pros jogadores, no formato "[Nome do produto] is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games…" — copiar o texto exato da página da política pro rodapé e pra página "Sobre".
- **Registro do produto** no Developer Portal é exigido pra qualquer produto que sirva jogadores, mesmo sem usar a API. Registrar antes do lançamento público.
- Assets permitidos: press kit e "game-specific static data" — que é exatamente o que ddragon fornece.
- Produto não pode se parecer com produtos da Riot em estilo ou função (não imitar o cliente do jogo no visual).
- Não usar "Riot" ou "League of Legends" como parte do nome do produto.

### B.5.2 Monetização (pra v2, se um dia houver)

Permitido apenas com registro aprovado, tier gratuito obrigatório, e conteúdo "transformativo" se for cobrado. Doações e assinaturas são aceitas; anúncios no tier gratuito também. Sem apostas.

### B.5.3 Wiki

Ver §3.2. Crédito à League of Legends Wiki / Weird Gloop obrigatório nos assets que vierem de lá, respeitando a licença deles.

## B.6. Estimativa de volume

- Tarball do ddragon: ~1 GB por patch (referência de 2022; hoje provavelmente maior, mas na mesma ordem). Inclui todos os idiomas — só precisamos de `pt_BR` e `en_US`, então o índice em disco é bem menor.
- Splashes cdragon (centralizada + não centralizada + tiles) para ~1.700 skins: estimativa **2–4 GB** por versão em JPG; convertido pra PNG, **3–6 GB**. **[A VERIFICAR]** com amostra de 10 campeões.
- Implicação de storage: guardar assets completos só pra **a versão atual + 1 anterior**; versões antigas ficam **só com índice** apontando pros PNGs pequenos do ddragon (que são baratos) e sem splash pré-convertida. Isso mantém o custo perto de zero num bucket com egress gratuito.

## B.7. Decisões derivadas (entram na Spec)

1. **Chave de identidade universal:** `championKey` numérico + `skinId` (formato `{key}{num:03d}`, ex.: Jax Deus da Guerra = `24004`). ddragon e cdragon concordam nisso.
2. **Adaptador ddragon baixa o tarball**, extrai só `data/{pt_BR,en_US}` e `img/`, e registra dimensões reais de cada imagem com Pillow no índice.
3. **Adaptador cdragon parte dos JSONs em `v1/`**, nunca de paths montados na mão; aplica a regra de mapeamento §2.1; baixa só os diretórios listados em §2.3; concorrência limitada.
4. **Adaptador wiki existe atrás de feature flag, desligado por padrão**, e só liga com consentimento documentado no repositório.
5. **Fusão:** para cada `(identidade, tipo)`, vence a maior resolução; empate favorece ddragon (oficial). O índice guarda `source`, `sourceUrl`, `width`, `height`, `format` de cada asset.
6. **Ranks:** zip oficial da Riot como fonte primária.
7. **Idiomas:** `pt_BR` e `en_US` no índice desde o início (busca funciona com nome nas duas línguas, exibição na do usuário).
8. **Política de versões:** assets completos só pra atual + 1; histórico é índice + ddragon direto.
9. **Testes de contrato por adaptador:** um teste que baixa 3 campeões conhecidos e valida que todos os tipos de asset existem e têm dimensão mínima. Falha = alerta, não deploy.

## B.8. Spikes pendentes (tickets de pesquisa, antes da Spec)

| Spike | Objetivo | Effort sugerido pro Claude Code |
|---|---|---|
| S1 — Amostra ddragon | Baixar tarball atual, medir dimensões reais de cada tipo, medir tamanho em disco de `pt_BR + img/` | baixo |
| S2 — Amostra cdragon | Para Jax, Lux e Nunu (casos difíceis), baixar todos os assets via JSON `v1/champions/{key}.json`, medir dimensões, listar quais tipos existem | médio |
| S3 — Volume | Extrapolar S1+S2 pra 170 campeões / 1.700 skins e decidir política de versões final | baixo |
| S4 — Wiki (só se autorizado) | Testar `api.php` e Bucket API, mapear categoria HD | médio |

## B.9. Fontes consultadas

- Riot Developer Portal — League of Legends docs e Developer API Policy: `https://developer.riotgames.com/docs/lol`
- Riot API Libraries — Data Dragon: `https://riot-api-libraries.readthedocs.io/en/latest/ddragon.html`
- CommunityDragon — Asset paths: `https://www.communitydragon.org/documentation/assets`
- CommunityDragon — Docs (GitHub): `https://github.com/CommunityDragon/Docs`
- League of Legends Wiki — página inicial: `https://wiki.leagueoflegends.com/en-us/`
- Weird Gloop — Terms of Use: `https://weirdgloop.org/terms/`
- Weird Gloop — blog sobre scrapers (13/03/2026): `https://weirdgloop.org/blog/clankers`
- Weird Gloop — Bucket API: `https://meta.weirdgloop.org/w/Extension:Bucket/Api`


---

## Parte C — Prompt inicial para o Claude Code

Cole o texto abaixo como primeira mensagem no Claude Code, dentro da pasta onde você clonou o repositório (`git clone https://github.com/NihonCodingg/PROJETO-ASSETS-LOL.git`) e já salvou este arquivo em `docs/KICKOFF.md`.

````
Effort: alto.

Você é o engenheiro principal do projeto "lol-assets", cujo repositório oficial é https://github.com/NihonCodingg/PROJETO-ASSETS-LOL.git (já clonado nesta pasta). Leia `docs/KICKOFF.md` inteiro antes de qualquer ação — ele contém o processo de trabalho (Parte 0), a ideia cristalizada (Parte A) e a pesquisa verificada das fontes de dados (Parte B). Estamos seguindo as 7 Etapas do Desenvolvimento com IA e as etapas 1 e 2 já estão concluídas. Sua missão nesta sessão é a etapa 3 (spikes + protótipo) e, se aprovada, a etapa 4 (Spec).

Regra absoluta: tudo é registrado neste repositório e enviado com `git push` ao final de cada bloco. Se o repositório já tiver conteúdo, me mostre o que existe antes de tocar em qualquer coisa.

Faça nesta ordem, parando nos pontos marcados como [PARADA] para eu aprovar:

1. Bootstrap (effort: baixo)
   - Confirme o remoto (`git remote -v`) e a branch padrão. Trabalhe na `main` durante as etapas 3 e 4.
   - Inicialize o monorepo exatamente com a estrutura da §0.3: pnpm workspaces, uv para Python, `.gitignore`, `.env.example`, `README.md` mínimo, pastas `docs/adr/` e `docs/sessoes/`.
   - Crie `CLAUDE.md` na raiz com as regras da §0.2, palavra por palavra.
   - Crie `.github/workflows/ci.yml` rodando ruff, mypy, pytest, eslint, tsc e vitest (pode ficar tudo vazio/verde por enquanto).
   - Commit `chore: bootstrap do monorepo` e push.

2. Spikes S1, S2 e S3 da §B.8 (effort: médio)
   - Escreva scripts descartáveis em `prototype/spikes/` (Python) que: baixem o tarball atual do ddragon e meçam dimensões e tamanho em disco por tipo de asset (S1); baixem via cdragon todos os assets de Jax (key 24), Lux (99) e Nunu (20) partindo de `v1/champions/{key}.json`, registrando quais tipos existem, dimensões e formato (S2); extrapolem para 170 campeões / 1.700 skins e proponham a política de versões (S3).
   - Respeite a §0.2 item 4 (User-Agent, concorrência, backoff).
   - NÃO acesse a wiki. Consentimento ainda não foi concedido.
   - Escreva os resultados em `docs/SPIKES.md` com números reais, não estimativas, e marque explicitamente qualquer item da Parte B que se mostrou errado.
   - Commit `docs: resultados dos spikes S1-S3`, push, e salve o relatório em `docs/sessoes/`.
   [PARADA] Me mostre o resumo dos spikes e espere aprovação.

3. Protótipo descartável (effort: médio)
   - Em `prototype/web/`, uma única página Next.js sem back-end que: busca a versão mais recente do ddragon, carrega `champion.json` em pt_BR, mostra uma grade de squares com busca em tempo real tolerante a acento e maiúsculas, e ao clicar abre um painel com square, loading e splash da skin base, cada um com botão "Baixar PNG" (conversão no cliente via canvas) e "Copiar URL".
   - Objetivo é validar a regra dos 3 cliques da §A.4, não a arquitetura. Sem testes, sem polimento.
   - Commit `feat(prototype): validação do fluxo buscar->baixar` e push.
   [PARADA] Me diga como rodar e o que você aprendeu sobre a UX. Espere aprovação.

4. Spec / PRD (effort: alto)
   - Escreva `docs/SPEC.md` a partir da Parte A, da Parte B, de `docs/SPIKES.md` e do que o protótipo ensinou. Estrutura mínima: visão e não-objetivos; personas e jobs-to-be-done; requisitos funcionais numerados (RF-01...) com critérios de aceite testáveis; requisitos não funcionais numerados (RNF-01...) com metas mensuráveis; arquitetura (diagrama em Mermaid, componentes, fluxo de indexação, fluxo de consulta, fluxo de download em lote); contrato do índice (JSON Schema completo em `packages/schema`); contrato da API (OpenAPI resumido); modelo de dados e política de versões; estratégia de cache e CDN; estratégia de testes; observabilidade; riscos e mitigações; decisões em aberto que precisam de mim.
   - Onde a pesquisa deixou dúvida, escreva a decisão que você recomenda e por quê — não deixe em branco.
   - Registre cada decisão estrutural como ADR em `docs/adr/`.
   - Commit `docs: spec v1` e push.
   [PARADA] Liste as 5 decisões da Spec que mais mudam o projeto e espere aprovação. Só depois da aprovação passamos para a etapa 5 (Tickets).

Ao final de cada bloco, relate em português: o que foi feito, o que foi assumido, o que ficou pendente — e salve o mesmo relatório em `docs/sessoes/`. Não avance de um [PARADA] sem minha resposta. Nenhum bloco termina sem push.
````

### Depois da Spec aprovada — prompt da etapa 5

````
Effort: alto.

A Spec em `docs/SPEC.md` está aprovada. Quebre-a em tickets em `docs/TICKETS.md`. Cada ticket: id (T-01...), título, objetivo, escopo (o que entra e o que não entra), critérios de aceite, dependências, estimativa em linhas de lógica (máximo 500), effort recomendado para a sessão que vai executá-lo (baixo/médio/alto), e quais testes provam que está pronto. Ordene em ondas de execução: o que pode rodar em paralelo na mesma onda e o que depende da onda anterior. A primeira onda deve entregar o caminho mais fino de ponta a ponta (indexar 1 campeão do ddragon → publicar índice → front busca e baixa 1 square), para validarmos a arquitetura antes de escalar. Apague `prototype/` no primeiro ticket. Commit `docs: tickets v1`, push, e me mostre a lista. Espere aprovação antes de executar qualquer ticket.
````

### Executando um ticket — prompt da etapa 6

````
Effort: {o que está no ticket}.

Execute o ticket T-XX de `docs/TICKETS.md` em uma branch `feat/T-XX-descricao`. Leia `CLAUDE.md` e `docs/SPEC.md` primeiro. Comece pelos testes (TDD). Não toque em nada fora do escopo do ticket; se descobrir algo necessário fora dele, anote em `docs/TICKETS.md` como ticket novo e siga. Ao terminar: push da branch, CI verde, PR aberto no repositório oficial com descrição em português (o que, por quê, como testar), e relatório da sessão em `docs/sessoes/` incluído no PR.
````
