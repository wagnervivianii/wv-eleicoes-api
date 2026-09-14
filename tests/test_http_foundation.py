from uuid import UUID

from fastapi.testclient import TestClient

from wv_eleicoes_api.app import create_app
from wv_eleicoes_api.config import Settings


def client() -> TestClient:
    return TestClient(create_app(Settings(environment="test", _env_file=None)))


def test_api_v1_root_contract() -> None:
    response = client().get("/api/v1")
    assert response.status_code == 200
    assert response.json() == {
        "name": "wv-eleicoes-api",
        "version": "0.1.0",
        "status": "ok",
    }


def test_request_id_is_generated() -> None:
    response = client().get("/health/live")
    generated = response.headers["X-Request-ID"]
    assert str(UUID(generated)) == generated


def test_safe_request_id_is_preserved() -> None:
    response = client().get("/health/live", headers={"X-Request-ID": "wve-test-001"})
    assert response.headers["X-Request-ID"] == "wve-test-001"
