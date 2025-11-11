"""Tipos GraphQL para el orquestador del agente."""
from __future__ import annotations

from typing import List, Optional

import strawberry


@strawberry.type
class BudgetAuditResult:
    status: str
    analysis: Optional[str] = None
    budgets_reviewed: Optional[int] = None
    message: Optional[str] = None


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





