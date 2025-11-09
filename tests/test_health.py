from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_health_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    get_settings.cache_clear()
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "agents-service"
    assert "version" in body


def test_invalid_log_level(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "HTTP")
    get_settings.cache_clear()
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200

