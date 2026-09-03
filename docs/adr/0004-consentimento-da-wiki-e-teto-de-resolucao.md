# ADR 0004 — Consentimento da wiki é prioridade: é o único teto acima de 1280×720

- **Status:** aceito — ação pendente do mantenedor humano
- **Data:** 2026-09-03
- **Evidência:** [SPIKES](../SPIKES.md) — S1 e S2; §B.3.2 do [KICKOFF](../KICKOFF.md)

## Contexto

Os spikes mediram o teto de resolução das duas fontes automatizáveis e ele é **o mesmo
nos dois lados**:

| Asset | ddragon | cdragon |
|---|---|---|
| Splash centralizada | 1280×720 | 1280×720 |
| Splash aberta | 1215×717 | 1215×717 |
| Square | 128×128 | 128×128 |
| Loading | 308×560 | 308×560 |

A premissa da §A.3 de que "quando o mesmo asset existe em mais de uma fonte, vence a de
maior resolução" perde a função para assets de campeão: **não há vencedor, há empate**.
O cdragon acrescenta cobertura (chromas, loading vintage), não pixels.

Isso muda o peso da wiki no projeto. A categoria "High definition images" da
League of Legends Wiki é, hoje, **a única fonte conhecida com arte acima de 1280×720** —
e o público-alvo é justamente quem monta thumbnail em 1920×1080 ou 4K, onde 1280×720
obriga a fazer upscale, que o [ADR 0001](0001-formato-de-entrega-dos-assets.md) proíbe.

O bloqueio continua de pé: os Termos de Uso da Weird Gloop classificam uso automatizado
sem consentimento prévio como uso indevido, e o post deles de 13/03/2026 sobre scrapers
deixa claro que não é formalidade.

## Decisão

1. **Obter o consentimento da Weird Gloop passa a ser prioridade de projeto**, não item
   de backlog. É a diferença entre entregar 1280×720 e entregar arte em alta de verdade.
2. A regra 3 do [CLAUDE.md](../../CLAUDE.md) **não muda**: nenhuma requisição automatizada
   à wiki enquanto `WIKI_CONSENT_GRANTED` não estiver documentado em
   [`docs/SPIKES.md`](../SPIKES.md) com data e evidência. A trava em código
   (`prototype/spikes/common.py`) continua ativa.
3. O pedido é **tarefa humana** (mantenedor), não do agente. Deve dizer, no mínimo:
   o que é o projeto; que só o indexador acessa a wiki, nunca o usuário final; volume
   estimado por patch; o User-Agent identificado; a concorrência proposta (1 requisição
   simultânea); que os arquivos são copiados para storage próprio, sem hotlink; e que
   haverá crédito visível à League of Legends Wiki / Weird Gloop.
4. **A v1 não depende disso.** Ela entrega o catálogo completo a 1280×720 com ddragon e
   cdragon. A wiki entra como um *tier* adicional de alta resolução assim que autorizada.
5. Se o consentimento for negado ou não vier resposta, a arte em alta simplesmente não
   existe no produto — e isso precisa ficar dito na página "Sobre", não escondido.

## Consequências

- O adaptador da wiki é escrito atrás de feature flag desligada e **não é ligado** por
  ninguém sem a evidência registrada. Nenhum ticket de execução depende dele.
- A promessa da §A.1 ("na melhor qualidade disponível") tem hoje um teto de 1280×720 para
  splash. A interface precisa ser honesta sobre isso mostrando a resolução no card
  (§A.4 item 7), em vez de sugerir que é a maior que existe no mundo.
- O spike S4 (testar `api.php`, módulos e categoria HD) segue **não executado** e assim
  permanece até a autorização.
- Se o consentimento vier, o volume da categoria HD é desconhecido e precisa de spike
  próprio antes de entrar no orçamento de storage.
