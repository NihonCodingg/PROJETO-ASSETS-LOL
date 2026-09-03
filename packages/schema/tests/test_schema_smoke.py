from lol_assets_schema import SCHEMA_VERSION


def test_schema_version_is_exposed() -> None:
    assert SCHEMA_VERSION
