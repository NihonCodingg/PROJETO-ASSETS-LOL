from fastapi.testclient import TestClient
from lol_assets_api import __version__
from lol_assets_api.main import app


def test_health_returns_ok() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}
