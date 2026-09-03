# ADRs — decisões de arquitetura

Regra 12 do [CLAUDE.md](../../CLAUDE.md): toda decisão estrutural vira um registro aqui,
com contexto, decisão e consequências. A Spec referencia; não repete.

| # | Decisão | Status |
|---|---|---|
| [0001](0001-formato-de-entrega-dos-assets.md) | Melhor fonte disponível, sem re-encode; PNG gerado no cliente | aceito — revoga "PNG sempre" |
| [0002](0002-nomes-canonicos-de-corte-de-splash.md) | `splash_centered` e `splash_wide` como nomes canônicos | aceito |
| [0003](0003-nome-publico-do-produto.md) | Nome público [A DECIDIR]; interno permanece | aceito |
| [0004](0004-consentimento-da-wiki-e-teto-de-resolucao.md) | Consentimento da Weird Gloop vira prioridade | aceito — ação humana pendente |
| [0005](0005-arquitetura-estatica-custo-zero.md) | Arquitetura estática por padrão, custo de operação zero | aceito |
| [0006](0006-api-como-componente-opcional.md) | API FastAPI fora do caminho crítico | aceito |
| [0007](0007-politica-de-versoes-e-orcamento.md) | Assets só da versão atual; orçamento de 10 GB | aceito |
| [0008](0008-catalogo-de-skins-e-seletor.md) | O catálogo é de skins; seletor de skin na v1 | aceito |
| [0009](0009-apelidos-de-busca-mantidos-a-mao.md) | Apelidos em JSON estático mantido à mão | aceito |
