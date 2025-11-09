from __future__ import annotations

import json
from typing import List

import httpx
import strawberry
from loguru import logger
from strawberry.fastapi import GraphQLRouter
from strawberry.federation import Schema
from strawberry.types import Info

from ..config import get_settings
from ..orchestrator import AgentOrchestrator
from ..services.gemini_client import GeminiClient
from ..services.mistral_client import MistralOCRClient
from .orchestrator_types import (
    BudgetAuditResult,
    ProcessDocumentInput,
    ProcessDocumentResult,
    SavingsPlanInput,
    SavingsPlanResult,
)
from .types import ChatMessageInput, ChatResponse, GeminiMessage, HealthStatus, OCRResult


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> HealthStatus:
        settings = get_settings()
        integrations: List[str] = []
        if settings.gemini_api_key:
            integrations.append("gemini")
        if settings.mistral_ocr_api_key:
            integrations.append("mistral_ocr")
        return HealthStatus(status="OK", version="0.1.0", integrations=integrations)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def chat(self, messages: List[ChatMessageInput]) -> ChatResponse:
        try:
            client = GeminiClient()
            payload = [{"text": m.content, "role": m.role} for m in messages]
            response = await client.chat(payload)
            candidates = response.get("candidates", [])
            formatted: List[GeminiMessage] = []
            for candidate in candidates:
                parts = candidate.get("content", {}).get("parts", [])
                content = " ".join(part.get("text", "") for part in parts)
                formatted.append(GeminiMessage(role="model", content=content.strip()))
            return ChatResponse(messages=formatted, raw=json.dumps(response))
        except (RuntimeError, httpx.HTTPError) as exc:
            logger.error("Error en chat Gemini: {}", exc)
            raise ValueError(f"No se pudo procesar la conversación: {exc}") from exc

    @strawberry.mutation
    async def analyze_document(self, document_url: str) -> OCRResult:
        try:
            client = MistralOCRClient()
            response = await client.extract_text(document_url)
            text = response.get("text", "")
            confidence = response.get("confidence")
            return OCRResult(text=text, confidence=confidence, raw=json.dumps(response))
        except (RuntimeError, httpx.HTTPError) as exc:
            logger.error("Error en OCR Mistral: {}", exc)
            raise ValueError(f"No se pudo procesar el documento: {exc}") from exc

    # --- Mutaciones del orquestador proactivo ---

    @strawberry.mutation
    async def audit_budget(self, user_id: str, info: Info) -> BudgetAuditResult:
        """Auditoría proactiva de presupuestos."""
        token = info.context.get("request").headers.get("authorization")
        orchestrator = AgentOrchestrator(user_id=user_id, token=token)
        result = await orchestrator.run_budget_audit()
        return BudgetAuditResult(
            status=result["status"],
            analysis=result.get("analysis"),
            budgets_reviewed=result.get("budgets_reviewed"),
            message=result.get("message"),
        )

    @strawberry.mutation
    async def process_document(self, user_id: str, input: ProcessDocumentInput, info: Info) -> ProcessDocumentResult:
        """Procesa un documento con OCR y registra la transacción."""
        token = info.context.get("request").headers.get("authorization")
        orchestrator = AgentOrchestrator(user_id=user_id, token=token)
        result = await orchestrator.process_document_and_register(input.document_url, input.account_id)
        return ProcessDocumentResult(
            status=result["status"],
            transaction_id=result.get("transaction", {}).get("id"),
            ocr_text=result.get("ocr_text"),
            message=result.get("message"),
        )

    @strawberry.mutation
    async def generate_savings_plan(self, user_id: str, input: SavingsPlanInput, info: Info) -> SavingsPlanResult:
        """Genera un plan de ahorro personalizado."""
        token = info.context.get("request").headers.get("authorization")
        orchestrator = AgentOrchestrator(user_id=user_id, token=token)
        result = await orchestrator.generate_savings_plan(input.target_amount, input.months)
        return SavingsPlanResult(
            status=result["status"], plan=result.get("plan"), target=result.get("target"), months=result.get("months")
        )


schema = Schema(query=Query, mutation=Mutation, enable_federation_2=True)


def get_graphql_router() -> GraphQLRouter:
    settings = get_settings()
    return GraphQLRouter(schema, graphiql=settings.graphiql_enabled)

