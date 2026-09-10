# ADRs — decisões de arquitetura

Regra 12 do [CLAUDE.md](../../CLAUDE.md): toda decisão estrutural vira um registro aqui,
com contexto, decisão e consequências. A Spec referencia; não repete.

| # | Decisão | Status |
|---|---|---|
| [0001](0001-formato-de-entrega-dos-assets.md) | Melhor fonte disponível, sem re-encode; PNG gerado no cliente | aceito — revoga "PNG sempre" |
| [0002](0002-nomes-canonicos-de-corte-de-splash.md) | `splash_centered` e `splash_wide` como nomes canônicos | aceito |
| [0003](0003-nome-publico-do-produto.md) | Nome público: **Biblioteca de Assets**; interno permanece | ✅ aceito — nome definido em 10/09 |
| [0004](0004-consentimento-da-wiki-e-teto-de-resolucao.md) | Consentimento da Weird Gloop vira prioridade | aceito — ação humana pendente |
| [0005](0005-arquitetura-estatica-custo-zero.md) | Arquitetura estática por padrão, custo de operação zero | ⚠️ emendado pelo 0012 |
| [0006](0006-api-como-componente-opcional.md) | API FastAPI fora do caminho crítico | aceito |
| [0007](0007-politica-de-versoes-e-orcamento.md) | Assets só da versão atual; orçamento de 10 GB | ⚠️ largamente emendado pelo 0012 |
| [0008](0008-catalogo-de-skins-e-seletor.md) | O catálogo é de skins; seletor de skin na v1 | ⚠️ emendado pelo 0010 |
| [0009](0009-apelidos-de-busca-mantidos-a-mao.md) | Apelidos em JSON estático mantido à mão | aceito |
| [0010](0010-navegacao-por-campeao-busca-por-skin.md) | Navegação por campeão, busca por skin; catálogo vira documento próprio | aceito — emenda o 0008 |
| [0011](0011-base-de-componentes-do-front.md) | shadcn/ui sobre Radix, TanStack Virtual, cmdk; Fuse.js fora | aceito |
| [0012](0012-onde-guardar-os-assets.md) | **Sem storage**: o índice aponta para as URLs das fontes | ✅ aceito — emenda 0005 e 0007 |
| [0013](0013-uma-versao-por-vez-no-indice.md) | **Uma versão por vez** no índice; histórico sai da v1 | ✅ aceito — emenda 0007 |
| [0014](0014-onde-vive-o-indice-gerado.md) | Índice gerado vive no `main`; crescimento medido | ✅ aceito |
| [0015](0015-orcamento-do-indice-depois-da-segunda-fonte.md) | Teto do índice vai a **24 MiB**; emotes, wards e chromas cabem | ✅ aceito — emenda 0007 e 0013 |
