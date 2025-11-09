"""Cliente para consumir el Gateway GraphQL (supergraph) desde el agente."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from ..config import get_settings


class GatewayClient:
    """Cliente para consultar/mutar el supergraph federado."""

    def __init__(self, user_id: Optional[str] = None, token: Optional[str] = None) -> None:
        settings = get_settings()
        self.gateway_url = settings.gateway_url
        self.user_id = user_id
        self.token = token

    @property
    def headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    async def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecuta una query/mutation GraphQL contra el gateway."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.debug("Ejecutando GraphQL en gateway: {}", query[:100])
            response = await client.post(self.gateway_url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                logger.error("Errores GraphQL: {}", data["errors"])
                raise RuntimeError(f"Gateway GraphQL error: {data['errors']}")
            return data.get("data", {})

    async def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene las cuentas del usuario desde core-service."""
        query = """
        query GetAccounts($userId: ID!) {
          accounts(userId: $userId) {
            id
            name
            type
            balance
            currency
          }
        }
        """
        result = await self.execute(query, {"userId": user_id})
        return result.get("accounts", [])

    async def get_user_budgets(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene los presupuestos activos del usuario."""
        query = """
        query GetBudgets($userId: ID!) {
          budgets(userId: $userId) {
            id
            category
            limitAmount
            periodStart
            periodEnd
          }
        }
        """
        result = await self.execute(query, {"userId": user_id})
        return result.get("budgets", [])

    async def get_user_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene las metas financieras del usuario."""
        query = """
        query GetGoals($userId: ID!) {
          goals(userId: $userId) {
            id
            name
            targetAmount
            currentAmount
            deadline
          }
        }
        """
        result = await self.execute(query, {"userId": user_id})
        return result.get("goals", [])

    async def get_recent_transactions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene las transacciones recientes del usuario."""
        query = """
        query GetTransactions($userId: ID!, $limit: Int) {
          transactions(userId: $userId, limit: $limit) {
            id
            accountId
            amount
            category
            description
            date
          }
        }
        """
        result = await self.execute(query, {"userId": user_id, "limit": limit})
        return result.get("transactions", [])

    async def register_transaction(
        self, account_id: str, amount: float, transaction_type: str, category: str, description: str
    ) -> Dict[str, Any]:
        """Registra una nueva transacción en core-service."""
        mutation = """
        mutation RegisterTransaction($input: RegisterTransactionInput!) {
          registerTransaction(input: $input) {
            id
            amount
            category
            description
          }
        }
        """
        input_data = {
            "accountId": account_id,
            "amount": amount,
            "type": transaction_type,
            "category": category,
            "description": description,
        }
        result = await self.execute(mutation, {"input": input_data})
        return result.get("registerTransaction", {})

    async def create_budget(
        self, user_id: str, category: str, limit_amount: float, period_start: str, period_end: str
    ) -> Dict[str, Any]:
        """Crea un nuevo presupuesto."""
        mutation = """
        mutation CreateBudget($input: CreateBudgetInput!) {
          createBudget(input: $input) {
            id
            category
            limitAmount
          }
        }
        """
        input_data = {
            "userId": user_id,
            "category": category,
            "limitAmount": limit_amount,
            "periodStart": period_start,
            "periodEnd": period_end,
        }
        result = await self.execute(mutation, {"input": input_data})
        return result.get("createBudget", {})

    async def update_goal_progress(self, goal_id: str, amount: float) -> Dict[str, Any]:
        """Actualiza el progreso de una meta."""
        mutation = """
        mutation UpdateGoalProgress($input: UpdateGoalProgressInput!) {
          updateGoalProgress(input: $input) {
            id
            currentAmount
          }
        }
        """
        input_data = {"goalId": goal_id, "amount": amount}
        result = await self.execute(mutation, {"input": input_data})
        return result.get("updateGoalProgress", {})

    # --- Integración con ML Service ---

    async def classify_transaction(self, text: str, transaction_id: str | None = None) -> Dict[str, Any]:
        """Clasifica una transacción usando ML."""
        mutation = """
        mutation ClassifyTransaction($input: ClassifyTransactionInput!) {
          classifyTransaction(input: $input) {
            id
            predictedCategory
            confidence
            alternativeCategories {
              category
              confidence
            }
          }
        }
        """
        input_data = {"text": text, "transactionId": transaction_id}
        result = await self.execute(mutation, {"input": input_data})
        return result.get("classifyTransaction", {})

    async def generate_forecast(self, months: int, category_id: str | None = None) -> List[Dict[str, Any]]:
        """Genera pronóstico de gastos con ML."""
        mutation = """
        mutation GenerateForecast($input: GenerateForecastInput!) {
          generateForecast(input: $input) {
            id
            forecastMonth
            forecastYear
            predictedAmount
            confidenceLower
            confidenceUpper
            trend
          }
        }
        """
        input_data = {"months": months, "categoryId": category_id}
        result = await self.execute(mutation, {"input": input_data})
        return result.get("generateForecast", [])

    async def analyze_spending_patterns(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Analiza patrones de gasto con Deep Learning."""
        mutation = """
        mutation AnalyzePatterns($input: AnalyzePatternsInput!) {
          analyzePatterns(input: $input) {
            id
            patternType
            description
            frequency
            averageAmount
            confidence
            recommendations
          }
        }
        """
        input_data = {"startDate": start_date, "endDate": end_date}
        result = await self.execute(mutation, {"input": input_data})
        return result.get("analyzePatterns", [])

    async def get_predictions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene predicciones históricas del usuario."""
        query = """
        query GetPredictions($limit: Int!) {
          predictions(limit: $limit) {
            id
            predictedCategory
            confidence
            inputText
            createdAt
          }
        }
        """
        result = await self.execute(query, {"limit": limit})
        return result.get("predictions", [])

