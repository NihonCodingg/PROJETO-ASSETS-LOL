# ADR 0001 — Formato de entrega dos assets: melhor fonte, sem re-encode

- **Status:** aceito
- **Data:** 2026-09-03
- **Revoga:** o princípio "PNG sempre" da §A.4 do [KICKOFF](../KICKOFF.md)
- **Evidência:** [SPIKES](../SPIKES.md) — S1 e S3

## Contexto

A §A.4 do KICKOFF listava "PNG sempre" como princípio de UX não negociável: o usuário
nunca receberia JPG ou WebP, mesmo quando a fonte fosse JPG. A própria nota reconhecia
que a conversão não recupera qualidade; a promessa real era "melhor fonte disponível,
entregue sem perda adicional".

Os spikes mediram o preço dessa promessa e o que ela entrega:

| Fato medido | Valor |
|---|---|
| Razão PNG/JPEG ao reencodar a fonte (12 amostras reais, Pillow `optimize=True`) | **5,712×** mediana (3,412× a 6,974×) |
| Catálogo completo de uma versão, nos bytes de origem | ~1,1 GB |
| O mesmo catálogo convertido para PNG | ~4,6 GB |
| Canal alfa em splash, centered, loading, tile, square, item, feitiço, passiva, profileicon | **nenhum** — todos RGB |
| Canal alfa em runas e stat mods | **presente** — RGBA, alfa mínimo 0 |

Ou seja: converter multiplica armazenamento e banda por ~5,7 e devolve exatamente os
mesmos pixels, porque não há transparência a preservar e o JPEG de origem já perdeu o
que tinha de perder. O único ganho real é o container do arquivo.

Também foi medido que **ddragon e cdragon servem tudo com `Access-Control-Allow-Origin: *`**,
inclusive as imagens — o que torna a conversão no navegador tecnicamente viável sem
proxy e sem canvas contaminado.

## Decisão

"PNG sempre" está revogado. O novo princípio é **melhor fonte disponível, servida sem
re-encode, com PNG gerado no cliente sob demanda**:

1. O CDN **armazena e serve os bytes originais**. O indexador **nunca re-encoda**.
2. O botão "Baixar PNG" **converte no navegador**, via canvas, no momento do clique.
3. O card mostra **formato e resolução antes do download** e oferece as duas opções:
   arquivo original e PNG.
4. Assets cuja origem já é PNG permanecem PNG de ponta a ponta. **Runas e stat mods têm
   canal alfa e nunca podem virar JPG.**
5. **Nunca fazer upscale.**

## Consequências

**Boas**

- Armazenamento e egress caem de ~4,6 GB para ~1,1 GB por versão (−76 %), o que sustenta
  a meta de custo próximo de zero da §A.5.
- O indexador fica mais simples e mais rápido: copia bytes, não decodifica nem recodifica.
  Só precisa do Pillow para **ler** dimensões e modo de cor, não para escrever.
- O hash `sha256` do índice passa a identificar o arquivo exatamente como a Riot o
  publicou, o que torna a deduplicação e a verificação triviais.
- A promessa ao usuário fica honesta: "os pixels originais, do jeito que a Riot publicou".

**Ruins / custos aceitos**

- A conversão passa a consumir CPU e memória do navegador do usuário. Para 1280×720 é
  irrelevante; para downloads em lote de dezenas de splashes pode pesar. Mitigação: o zip
  em lote entrega os originais, e o PNG em lote fica para a v2 se alguém pedir.
- O card fica com dois botões em vez de um, o que adiciona uma decisão à interface. A §A.4
  exige que o padrão seja óbvio: o botão primário é o original, o PNG é secundário.
- Depende do CORS das fontes continuar aberto. Está coberto por teste de contrato:
  se `Access-Control-Allow-Origin` sumir, o alerta dispara e o fallback é converter na API.
- O nome do arquivo baixado precisa refletir o formato real (`Jax_0_centered.jpg` para o
  original, `Jax_0_centered.png` para o convertido), o que muda a §A.4 item 4.

## Alternativas descartadas

- **Pré-gerar PNG no indexador (o plano original).** Custa 4,6 GB por versão e não entrega
  nenhum pixel a mais.
- **Converter na API por requisição.** Move o custo de armazenamento para CPU e latência,
  contraria a §A.5 ("não convertidos por requisição") e cria um vetor de abuso trivial.
- **Servir WebP/AVIF.** Menor, mas o público-alvo edita em Premiere e Photoshop, onde o
  suporte é irregular. Fora de questão para a v1.
