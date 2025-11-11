from __future__ import annotations

from typing import Any, List

import httpx
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, HttpUrl, model_validator

from ..orchestrator import AgentOrchestrator
from ..services.gemini_client import GeminiClient
from ..services.mistral_client import MistralOCRClient

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatMessageModel(BaseModel):
    role: str
    content: str

    @model_validator(mode="after")
    def validate_model(self) -> "ChatMessageModel":
        self.role = self.role.lower().strip()
        if self.role not in {"user", "model", "system"}:
            raise ValueError("El rol debe ser user, model o system")
        if not self.content or not self.content.strip():
            raise ValueError("El contenido no puede estar vacío")
        self.content = self.content.strip()
        return self


class ChatRequest(BaseModel):
    messages: List[ChatMessageModel] | None = None
    prompt: str | None = None

    @model_validator(mode="after")
    def validate_request(self) -> "ChatRequest":
        if self.messages:
            return self
        if self.prompt and self.prompt.strip():
            self.messages = [
                ChatMessageModel(role="user", content=self.prompt.strip()),
            ]
            return self
        raise ValueError("Debes enviar al menos un mensaje o un prompt")


class GeminiMessageModel(BaseModel):
    role: str
    content: str


class ChatResponseModel(BaseModel):
    messages: List[GeminiMessageModel]
    raw: dict[str, Any] | None = None


class OCRRequest(BaseModel):
    document_url: HttpUrl


class OCRResponseModel(BaseModel):
    text: str
    confidence: float | None = None
    raw: dict[str, Any] | None = None


async def _call_gemini(messages: List[ChatMessageModel]) -> dict[str, Any]:
    from ..config import get_settings
    from ..services.mock_agent import MockAgent
    
    try:
        settings = get_settings()
        
        # Si no hay API key, usar mock
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY no configurada, usando agente mock")
            mock = MockAgent()
            payload = [{"text": msg.content, "role": msg.role} for msg in messages]
            return await mock.chat(payload)
        
        # Usar Gemini real
        client = GeminiClient()
        payload = [{"text": msg.content, "role": msg.role} for msg in messages]
        return await client.chat(payload)
    except (RuntimeError, httpx.HTTPError) as exc:
        logger.error("Error en Gemini, usando fallback mock: {}", exc)
        # Fallback a mock
        mock = MockAgent()
        payload = [{"text": msg.content, "role": msg.role} for msg in messages]
        return await mock.chat(payload)


def _format_gemini_response(data: dict[str, Any]) -> List[GeminiMessageModel]:
    candidates = data.get("candidates", [])
    formatted: List[GeminiMessageModel] = []
    for candidate in candidates:
        parts = candidate.get("content", {}).get("parts", [])
        content = " ".join(part.get("text", "") for part in parts)
        formatted.append(GeminiMessageModel(role="model", content=content.strip()))
    return formatted


@router.post("/chat", response_model=ChatResponseModel)
async def chat_endpoint(request: ChatRequest) -> ChatResponseModel:
    assert request.messages  # asegurado por el validador
    data = await _call_gemini(request.messages)
    formatted = _format_gemini_response(data)
    return ChatResponseModel(messages=formatted, raw=data)


async def _call_mistral(document_url: str) -> dict[str, Any]:
    try:
        client = MistralOCRClient()
        return await client.extract_text(str(document_url))
    except (RuntimeError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo procesar el documento: {exc}",
        ) from exc


@router.post("/ocr", response_model=OCRResponseModel)
async def ocr_endpoint(request: OCRRequest) -> OCRResponseModel:
    data = await _call_mistral(request.document_url)
    return OCRResponseModel(
        text=data.get("text", ""),
        confidence=data.get("confidence"),
        raw=data,
    )


# --- Endpoints del orquestador proactivo ---


class BudgetAuditResponse(BaseModel):
    status: str
    analysis: str | None = None
    budgets_reviewed: int | None = None
    message: str | None = None


@router.post("/audit-budget", response_model=BudgetAuditResponse)
async def audit_budget_endpoint(user_id: str, authorization: str | None = Header(None)) -> BudgetAuditResponse:
    """Auditoría proactiva de presupuestos del usuario."""
    orchestrator = AgentOrchestrator(user_id=user_id, token=authorization)
    result = await orchestrator.run_budget_audit()
    return BudgetAuditResponse(**result)


class ProcessDocumentRequest(BaseModel):
    document_url: HttpUrl
    account_id: str


class ProcessDocumentResponse(BaseModel):
    status: str
    transaction: dict | None = None
    ocr_text: str | None = None
    message: str | None = None


@router.post("/process-document", response_model=ProcessDocumentResponse)
async def process_document_endpoint(
    request: ProcessDocumentRequest, user_id: str, authorization: str | None = Header(None)
) -> ProcessDocumentResponse:
    """Procesa un documento con OCR y registra la transacción automáticamente."""
    orchestrator = AgentOrchestrator(user_id=user_id, token=authorization)
    result = await orchestrator.process_document_and_register(str(request.document_url), request.account_id)
    return ProcessDocumentResponse(**result)


class SavingsPlanRequest(BaseModel):
    target_amount: float
    months: int


class SavingsPlanResponse(BaseModel):
    status: str
    plan: str | None = None
    target: float | None = None
    months: int | None = None


@router.post("/savings-plan", response_model=SavingsPlanResponse)
async def savings_plan_endpoint(
    request: SavingsPlanRequest, user_id: str, authorization: str | None = Header(None)
) -> SavingsPlanResponse:
    """Genera un plan de ahorro personalizado con IA."""
    orchestrator = AgentOrchestrator(user_id=user_id, token=authorization)
    result = await orchestrator.generate_savings_plan(request.target_amount, request.months)
    return SavingsPlanResponse(**result)


# --- Endpoints avanzados con ML ---


class SmartCategorizeRequest(BaseModel):
    transaction_text: str
    account_id: str
    amount: float


class SmartCategorizeResponse(BaseModel):
    status: str
    transaction: dict | None = None
    category: str | None = None
    ml_confidence: float | None = None
    method: str | None = None


@router.post("/smart-categorize", response_model=SmartCategorizeResponse)
async def smart_categorize_endpoint(
    request: SmartCategorizeRequest, user_id: str, authorization: str | None = Header(None)
) -> SmartCategorizeResponse:
    """Categoriza inteligentemente una transacción usando ML + Gemini."""
    orchestrator = AgentOrchestrator(user_id=user_id, token=authorization)
    result = await orchestrator.smart_categorize_transaction(
        request.transaction_text, request.account_id, request.amount
    )
    return SmartCategorizeResponse(**result)


class FinancialInsightsResponse(BaseModel):
    status: str
    patterns: list | None = None
    forecast: list | None = None
    analysis: str | None = None
    generated_at: str | None = None


@router.post("/financial-insights", response_model=FinancialInsightsResponse)
async def financial_insights_endpoint(user_id: str, authorization: str | None = Header(None)) -> FinancialInsightsResponse:
    """Genera reporte financiero completo con ML + DL + Gemini."""
    orchestrator = AgentOrchestrator(user_id=user_id, token=authorization)
    result = await orchestrator.generate_financial_insights()
    return FinancialInsightsResponse(**result)


class SpendingAlertResponse(BaseModel):
    status: str
    message: str | None = None
    anomalies: int | None = None
    anomalies_detected: int | None = None


@router.post("/spending-alert", response_model=SpendingAlertResponse)
async def spending_alert_endpoint(user_id: str, authorization: str | None = Header(None)) -> SpendingAlertResponse:
    """Monitoreo proactivo de gastos con detección de anomalías."""
    orchestrator = AgentOrchestrator(user_id=user_id, token=authorization)
    result = await orchestrator.proactive_spending_alert()
    return SpendingAlertResponse(**result)


