# Spikes — descartável

Scripts que produziram os números de [`docs/SPIKES.md`](../../docs/SPIKES.md).
Não são código de produção: sem testes, sem tipos estritos, excluídos do ruff e do
mypy. Somem junto com `prototype/` no primeiro ticket da etapa 6.

| Arquivo | O que faz |
|---|---|
| `common.py` | Cliente HTTP com a etiqueta da regra 4 e a trava da regra 3 (wiki) |
| `s1_ddragon.py` | Baixa o tarball do patch e mede tudo: dimensões, modos, bytes |
| `s2_cdragon.py` | Descobre os assets de Jax/Lux/Nunu pelos caminhos declarados no JSON |
| `s3_volume.py` | Conta o catálogo real e mede o custo de converter JPEG em PNG |

```bash
uv sync --all-packages
python prototype/spikes/s1_ddragon.py   # ~2,4 GB para .cache/ (ignorado pelo Git)
python prototype/spikes/s2_cdragon.py
python prototype/spikes/s3_volume.py
```

`results/` é versionado — é a evidência das medições. `.cache/` não é.
