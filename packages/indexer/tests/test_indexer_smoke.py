from lol_assets_indexer import __version__
from lol_assets_indexer.cli import app
from typer.testing import CliRunner


def test_cli_reports_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
