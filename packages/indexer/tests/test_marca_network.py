"""O meta-teste do T-18: a marca `network` exclui mesmo os testes lentos.

Critério 1: `pytest` sem argumento (o que a CI de PR roda) **não** pode executar
nenhum teste que toque a rede. Isso depende de duas coisas concordarem — o
`addopts` do `pyproject.toml` e o `pytestmark` do módulo — e as duas ficam longe
uma da outra.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
CONTRATO = "packages/indexer/tests/test_contrato_das_fontes.py"


def coletados(*extra: str) -> str:
    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *extra],
        cwd=RAIZ,
        capture_output=True,
        text=True,
    )
    return resultado.stdout


def test_a_suite_padrao_nao_coleta_teste_de_rede() -> None:
    assert CONTRATO.replace("/", "\\") not in coletados().replace("/", "\\")


def test_a_marca_liga_os_testes_de_rede() -> None:
    saida = coletados("-m", "network", CONTRATO)
    # Com `-q` o pytest imprime "<arquivo>: <quantos>". Zero seria a marca errada.
    assert "test_contrato_das_fontes.py" in saida.replace("\\", "/")
    assert ": 0" not in saida


def test_todo_teste_de_contrato_esta_marcado() -> None:
    """Um teste novo sem a marca entraria na suíte de PR sem ninguém notar."""
    codigo = (RAIZ / CONTRATO).read_text(encoding="utf-8")
    assert "pytestmark = pytest.mark.network" in codigo
