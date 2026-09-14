from fastapi.testclient import TestClient

from wv_eleicoes_api.app import create_app
from wv_eleicoes_api.config import Settings
from wv_eleicoes_api.health import router as health_router_module


def client() -> TestClient:
    return TestClient(create_app(Settings(environment="test", _env_file=None)))


def test_liveness_is_independent_from_database() -> None:
    response = client().get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(health_router_module, "database_is_ready", lambda: False)
    response = client().get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_readiness_returns_200_when_database_is_available(monkeypatch) -> None:
    monkeypatch.setattr(health_router_module, "database_is_ready", lambda: True)
    response = client().get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
