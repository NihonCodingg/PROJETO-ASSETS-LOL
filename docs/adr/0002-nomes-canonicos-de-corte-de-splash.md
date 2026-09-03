# ADR 0002 — Nomes canônicos dos cortes de splash

- **Status:** aceito
- **Data:** 2026-09-03
- **Evidência:** [SPIKES](../SPIKES.md) — S1 e S2

## Contexto

Cada skin tem dois recortes distintos da mesma arte, com proporções diferentes. **As duas
fontes usam nomes trocados para eles**, o que foi medido nos spikes:

| Imagem medida | ddragon chama de | cdragon chama de |
|---|---|---|
| **1280×720** (16:9, enquadramento fechado) | `img/champion/centered/{Id}_{num}.jpg` | `skins[].splashPath` |
| **1215×717** (~1,69:1, enquadramento aberto) | `img/champion/splash/{Id}_{num}.jpg` | `skins[].uncenteredSplashPath` |

Ler "splash" nas duas fontes e tratar como a mesma coisa produz um catálogo em que metade
dos campeões tem o corte errado — e o erro é silencioso, porque as duas imagens são
válidas, parecidas e da mesma skin. Nenhum teste de status HTTP pega isso.

Some-se a isso: o `img/champion/centered/` do ddragon **não estava documentado** na Parte B
e é justamente o maior dos dois.

## Decisão

1. O índice usa **nomes canônicos próprios**, independentes de qualquer fonte:
   - `splash_centered` — 1280×720
   - `splash_wide` — 1215×717
2. Os dois cortes são **catalogados**; nenhum substitui o outro. Não são candidatos à
   mesma identidade na etapa de fusão — são tipos de asset diferentes.
3. **`splash_centered` é o padrão** exibido e o primeiro oferecido, por ser o maior.
4. Cada adaptador declara seu mapa fonte → canônico em um único lugar, coberto por teste:

   | Canônico | ddragon | cdragon |
   |---|---|---|
   | `splash_centered` | `centered/` | `splashPath` |
   | `splash_wide` | `splash/` | `uncenteredSplashPath` |

5. O teste de contrato de cada adaptador **valida as dimensões**, não só o status HTTP:
   `splash_centered` precisa medir 1280×720 e `splash_wide` 1215×717. Se as fontes
   trocarem os nomes de novo, o teste quebra.
6. O nome do arquivo entregue ao usuário usa o nome canônico
   (`Jax_0_splash_centered.jpg`), nunca o nome da fonte.

## Consequências

- A tabela de aliases de tipo de asset vira parte do contrato do adaptador, não uma
  convenção informal. Mudança nela exige novo ADR.
- O índice fica com dois registros de splash por skin, o que aumenta a contagem de assets
  mas dá ao editor exatamente a escolha que ele já faria manualmente.
- O teste de contrato passa a depender de dimensões fixas. Se a Riot mudar a resolução de
  publicação, o teste falha e alguém precisa olhar — que é o comportamento desejado
  (alerta, não deploy silencioso).
- Os termos "centered" e "uncentered" ficam **proibidos** no código e no índice: são
  ambíguos justamente por causa da inversão.
