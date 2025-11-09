from __future__ import annotations

from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def _client(monkeypatch) -> TestClient:
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    monkeypatch.setenv("MISTRAL_OCR_API_KEY", "dummy")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_rest_chat(monkeypatch) -> None:
    client = _client(monkeypatch)

    async def fake_chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        return {"candidates": [{"content": {"parts": [{"text": "Respuesta REST"}]}}]}

    monkeypatch.setattr("app.api.rest.GeminiClient.chat", fake_chat, raising=True)

    response = client.post(
        "/agent/chat",
        json={"messages": [{"role": "user", "content": "Hola"}]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["messages"][0]["content"] == "Respuesta REST"
    assert "raw" in data


def test_rest_chat_with_prompt(monkeypatch) -> None:
    client = _client(monkeypatch)

    async def fake_chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        assert messages[0]["role"] == "user"
        assert messages[0]["text"] == "Hola" or messages[0]["content"] == "Hola"
        return {"candidates": [{"content": {"parts": [{"text": "Respuesta prompt"}]}}]}

    monkeypatch.setattr("app.api.rest.GeminiClient.chat", fake_chat, raising=True)

    response = client.post("/agent/chat", json={"prompt": "Hola"})
    assert response.status_code == 200
    assert response.json()["messages"][0]["content"] == "Respuesta prompt"


def test_rest_chat_validation(monkeypatch) -> None:
    client = _client(monkeypatch)
    response = client.post("/agent/chat", json={"messages": []})
    assert response.status_code == 422

    response = client.post("/agent/chat", json={"prompt": "   "})
    assert response.status_code == 422


def test_rest_ocr(monkeypatch) -> None:
    client = _client(monkeypatch)

    async def fake_ocr(self, document_url: str) -> Dict[str, Any]:
        return {"text": "Contenido OCR", "confidence": 0.9}

    monkeypatch.setattr("app.api.rest.MistralOCRClient.extract_text", fake_ocr, raising=True)

    response = client.post("/agent/ocr", json={"document_url": "https://example.com/doc.pdf"})

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Contenido OCR"
    assert data["confidence"] == 0.9

