"""Tipos GraphQL para el orquestador del agente."""
from __future__ import annotations

from typing import Optional

import strawberry


# --- Auditoría de presupuestos ---

@strawberry.type
class BudgetAuditResult:
    status: str
    analysis: Optional[str] = None
    budgets_reviewed: Optional[int] = None
    message: Optional[str] = None


# --- Procesamiento de documentos ---

@strawberry.input
class ProcessDocumentInput:
    document_url: str
    account_id: str


@strawberry.type
class ProcessDocumentResult:
    status: str
    transaction_id: Optional[str] = None
    ocr_text: Optional[str] = None
    message: Optional[str] = None


# --- Plan de ahorros ---

@strawberry.input
class SavingsPlanInput:
    target_amount: float
    months: int


@strawberry.type
class SavingsPlanResult:
    status: str
    plan: Optional[str] = None
    target: Optional[float] = None
    months: Optional[int] = None


# --- Categorización inteligente ---

@strawberry.input
class SmartCategorizeInput:
    transaction_text: str
    account_id: str
    amount: float


@strawberry.type
class SmartCategorizeResult:
    status: str
    transaction_id: Optional[str] = None
    category: Optional[str] = None
    ml_confidence: Optional[float] = None
    method: Optional[str] = None


# --- Insights financieros ---

@strawberry.type
class FinancialInsightsResult:
    status: str
    patterns: Optional[str] = None  # JSON string
    forecast: Optional[str] = None  # JSON string
    analysis: Optional[str] = None
    generated_at: Optional[str] = None


# --- Alertas de gasto ---

@strawberry.type
class SpendingAlertResult:
    status: str
    message: Optional[str] = None
    anomalies: Optional[int] = None