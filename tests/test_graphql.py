from __future__ import annotations

import json
from typing import Any, Dict

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    monkeypatch.setenv("MISTRAL_OCR_API_KEY", "dummy")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_health_query(monkeypatch) -> None:
    client = _build_client(monkeypatch)
    query = """
        query Health {
          health {
            status
            version
            integrations
          }
        }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["health"]["status"] == "OK"
    assert "gemini" in payload["data"]["health"]["integrations"]
    assert "mistral_ocr" in payload["data"]["health"]["integrations"]


def test_chat_mutation(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    async def fake_chat(self, messages):
        return {
            "candidates": [
                {"content": {"parts": [{"text": "Respuesta simulada"}]}},
            ]
        }

    monkeypatch.setattr("app.graphql.schema.GeminiClient.chat", fake_chat, raising=True)

    mutation = """
        mutation Chat($messages: [ChatMessageInput!]!) {
          chat(messages: $messages) {
            messages {
              role
              content
            }
            raw
          }
        }
    """

    variables: Dict[str, Any] = {
        "messages": [
            {"role": "user", "content": "Hola"},
        ]
    }

    response = client.post("/graphql", json={"query": mutation, "variables": variables})
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["chat"]["messages"][0]["content"] == "Respuesta simulada"
    assert json.loads(payload["data"]["chat"]["raw"])["candidates"]


def test_analyze_document_mutation(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    async def fake_extract(self, document_url: str):
        return {"text": "Contenido OCR", "confidence": 0.95}

    monkeypatch.setattr("app.graphql.schema.MistralOCRClient.extract_text", fake_extract, raising=True)

    mutation = """
        mutation Analyze($url: String!) {
          analyzeDocument(documentUrl: $url) {
            text
            confidence
            raw
          }
        }
    """

    response = client.post("/graphql", json={"query": mutation, "variables": {"url": "https://example.com/doc.pdf"}})
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["analyzeDocument"]["text"] == "Contenido OCR"
    assert payload["data"]["analyzeDocument"]["confidence"] == 0.95


