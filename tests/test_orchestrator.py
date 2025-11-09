"""Tests para el orquestador del agente."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.orchestrator import AgentOrchestrator


@pytest.fixture
def mock_gateway(monkeypatch):
    """Mock del GatewayClient."""
    mock = MagicMock()
    mock.get_user_budgets = AsyncMock(
        return_value=[
            {"id": "1", "category": "Alimentación", "limitAmount": 500, "periodStart": "2025-01-01", "periodEnd": "2025-01-31"}
        ]
    )
    mock.get_recent_transactions = AsyncMock(
        return_value=[
            {"id": "t1", "amount": -50, "category": "Alimentación", "description": "Supermercado", "date": "2025-01-10"}
        ]
    )
    mock.get_user_accounts = AsyncMock(return_value=[{"id": "a1", "balance": 1000}])
    mock.register_transaction = AsyncMock(return_value={"id": "t2", "amount": -30})
    return mock


@pytest.fixture
def mock_gemini(monkeypatch):
    """Mock del GeminiClient."""
    mock = MagicMock()
    mock.chat = AsyncMock(
        return_value={"candidates": [{"content": {"parts": [{"text": '{"alerts":[],"recommendations":["Ahorrar 10%"],"summary":"Todo bien"}'}]}}]}
    )
    return mock


@pytest.fixture
def mock_mistral(monkeypatch):
    """Mock del MistralOCRClient."""
    mock = MagicMock()
    mock.extract_text = AsyncMock(return_value={"text": "Total: 30 Bs. Categoría: Transporte"})
    return mock


@pytest.fixture
def mock_notifier(monkeypatch):
    """Mock del NotificationClient."""
    mock = MagicMock()
    mock.send_notification = AsyncMock(return_value={"status": "ok", "notification_id": "n1"})
    return mock


def test_orchestrator_init():
    """Verifica que el orquestador se inicializa correctamente."""
    orch = AgentOrchestrator(user_id="user123", token="fake-token")
    assert orch.user_id == "user123"
    assert orch.gateway is not None
    assert orch.gemini is not None


@pytest.mark.asyncio
async def test_run_budget_audit(monkeypatch, mock_gateway, mock_gemini, mock_notifier):
    """Verifica que la auditoría de presupuesto funciona."""

    def mock_gateway_client(*args, **kwargs):
        return mock_gateway

    def mock_gemini_client(*args, **kwargs):
        return mock_gemini

    def mock_notification_client(*args, **kwargs):
        return mock_notifier

    monkeypatch.setattr("app.orchestrator.agent_orchestrator.GatewayClient", mock_gateway_client)
    monkeypatch.setattr("app.orchestrator.agent_orchestrator.GeminiClient", mock_gemini_client)
    monkeypatch.setattr("app.orchestrator.agent_orchestrator.NotificationClient", mock_notification_client)

    orch = AgentOrchestrator(user_id="user123")
    result = await orch.run_budget_audit()

    assert result["status"] == "completed"
    assert "analysis" in result
    mock_gateway.get_user_budgets.assert_called_once_with("user123")
    mock_gemini.chat.assert_called_once()


@pytest.mark.asyncio
async def test_process_document_and_register(monkeypatch, mock_gateway, mock_gemini, mock_mistral, mock_notifier):
    """Verifica que el procesamiento de documentos funciona."""

    def mock_gateway_client(*args, **kwargs):
        return mock_gateway

    def mock_gemini_client(*args, **kwargs):
        # Simular respuesta de Gemini con JSON embebido
        mock_gemini.chat = AsyncMock(
            return_value={
                "candidates": [{"content": {"parts": [{"text": '{"amount": 30, "category": "Transporte", "description": "Taxi"}'}]}}]
            }
        )
        return mock_gemini

    def mock_mistral_client(*args, **kwargs):
        return mock_mistral

    def mock_notification_client(*args, **kwargs):
        return mock_notifier

    monkeypatch.setattr("app.orchestrator.agent_orchestrator.GatewayClient", mock_gateway_client)
    monkeypatch.setattr("app.orchestrator.agent_orchestrator.GeminiClient", mock_gemini_client)
    monkeypatch.setattr("app.orchestrator.agent_orchestrator.MistralOCRClient", mock_mistral_client)
    monkeypatch.setattr("app.orchestrator.agent_orchestrator.NotificationClient", mock_notification_client)

    orch = AgentOrchestrator(user_id="user123")
    result = await orch.process_document_and_register("https://example.com/doc.pdf", "acc1")

    assert result["status"] == "success"
    assert "transaction" in result
    mock_mistral.extract_text.assert_called_once()
    mock_gateway.register_transaction.assert_called_once()
    mock_notifier.send_notification.assert_called_once()

