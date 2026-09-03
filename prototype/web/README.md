# Protótipo descartável — fluxo buscar → baixar

Valida a **regra dos 3 cliques** (§A.4 item 2) e o [ADR 0001](../../docs/adr/0001-formato-de-entrega-dos-assets.md):
o CDN entrega os bytes originais e o PNG é gerado no navegador.

Sem back-end, sem testes, sem polimento. Fala direto com o ddragon.
Some junto com `prototype/` no primeiro ticket da etapa 6.

```bash
pnpm install
pnpm --filter @lol-assets/prototype-web dev   # http://localhost:3100
```

O que ele exercita de verdade:

- busca no cliente, tolerante a acento, maiúscula e apóstrofo (`kaisa`, `chogath`, `belveth`)
- atalho `/` para focar a busca
- os quatro tipos de asset da skin base, com os **nomes canônicos** do
  [ADR 0002](../../docs/adr/0002-nomes-canonicos-de-corte-de-splash.md)
- formato, resolução e tamanho reais mostrados **antes** do download
- "Baixar original" (bytes da fonte) e "Baixar PNG" (canvas, no clique)
- "Copiar URL"
