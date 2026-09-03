"""CLI do indexador. Os comandos de indexação chegam com os tickets da etapa 6."""

import typer

from lol_assets_indexer import __version__

app = typer.Typer(help="Indexador de assets de League of Legends.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Agrupa os subcomandos; sem ele o Typer achata um app de comando único."""


@app.command()
def version() -> None:
    """Imprime a versão do indexador."""
    typer.echo(__version__)


if __name__ == "__main__":  # pragma: no cover
    app()
