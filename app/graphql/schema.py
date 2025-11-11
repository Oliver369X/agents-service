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
from ..services.mock_agent import MockAgent
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
            settings = get_settings()
            
            # Si no hay API key, usar agente mock
            if not settings.gemini_api_key:
                logger.warning("GEMINI_API_KEY no configurada, usando agente mock")
                mock = MockAgent()
                payload = [{"text": m.content, "role": m.role} for m in messages]
                response = await mock.chat(payload)
                candidates = response.get("candidates", [])
                formatted: List[GeminiMessage] = []
                for candidate in candidates:
                    parts = candidate.get("content", {}).get("parts", [])
                    content = " ".join(part.get("text", "") for part in parts)
                    formatted.append(GeminiMessage(role="model", content=content.strip()))
                return ChatResponse(messages=formatted, raw=json.dumps(response))
            
            # Usar Gemini real
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
            logger.error("Error en chat: {}", exc)
            # Fallback a mock en caso de error
            logger.warning("Fallback a agente mock debido a error")
            mock = MockAgent()
            payload = [{"text": m.content, "role": m.role} for m in messages]
            response = await mock.chat(payload)
            candidates = response.get("candidates", [])
            formatted: List[GeminiMessage] = []
            for candidate in candidates:
                parts = candidate.get("content", {}).get("parts", [])
                content = " ".join(part.get("text", "") for part in parts)
                formatted.append(GeminiMessage(role="model", content=content.strip()))
            return ChatResponse(messages=formatted, raw=json.dumps(response))

    @strawberry.mutation
    async def analyze_document(self, document_url: str) -> OCRResult:
        try:
            settings = get_settings()
            
            # Si no hay API key, usar mock
            if not settings.mistral_ocr_api_key:
                logger.warning("MISTRAL_OCR_API_KEY no configurada, usando mock")
                mock = MockAgent()
                response = await mock.extract_text_from_receipt(document_url)
                return OCRResult(
                    text=response.get("text", ""),
                    confidence=response.get("confidence"),
                    raw=json.dumps(response)
                )
            
            # Usar Mistral real
            client = MistralOCRClient()
            response = await client.extract_text(document_url)
            text = response.get("text", "")
            confidence = response.get("confidence")
            return OCRResult(text=text, confidence=confidence, raw=json.dumps(response))
        except (RuntimeError, httpx.HTTPError) as exc:
            logger.error("Error en OCR: {}", exc)
            # Fallback a mock
            logger.warning("Fallback a OCR mock debido a error")
            mock = MockAgent()
            response = await mock.extract_text_from_receipt(document_url)
            return OCRResult(
                text=response.get("text", ""),
                confidence=response.get("confidence"),
                raw=json.dumps(response)
            )

    # --- Mutaciones del orquestador proactivo ---

    @strawberry.mutation
    async def audit_budget(self, user_id: str, info: Info) -> BudgetAuditResult:
        """Auditoría proactiva de presupuestos."""
        try:
            token = info.context.get("request").headers.get("authorization")
            orchestrator = AgentOrchestrator(user_id=user_id, token=token)
            result = await orchestrator.run_budget_audit()
            return BudgetAuditResult(
                status=result["status"],
                analysis=result.get("analysis"),
                budgets_reviewed=result.get("budgets_reviewed"),
                message=result.get("message"),
            )
        except Exception as exc:
            logger.error("Error en audit_budget: {}", exc)
            # Fallback a mock
            mock = MockAgent()
            result = await mock.analyze_budget(user_id)
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
        try:
            token = info.context.get("request").headers.get("authorization")
            orchestrator = AgentOrchestrator(user_id=user_id, token=token)
            result = await orchestrator.generate_savings_plan(input.target_amount, input.months)
            return SavingsPlanResult(
                status=result["status"], plan=result.get("plan"), target=result.get("target"), months=result.get("months")
            )
        except Exception as exc:
            logger.error("Error en generate_savings_plan: {}", exc)
            # Fallback a mock
            mock = MockAgent()
            result = await mock.generate_savings_plan(input.target_amount, input.months)
            return SavingsPlanResult(
                status=result["status"], plan=result.get("plan"), target=result.get("target"), months=result.get("months")
            )


schema = Schema(query=Query, mutation=Mutation, enable_federation_2=True)


def get_graphql_router() -> GraphQLRouter:
    settings = get_settings()
    return GraphQLRouter(schema, graphiql=settings.graphiql_enabled)

