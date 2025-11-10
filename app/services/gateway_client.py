"""Cliente para comunicarse con el API Gateway."""
from __future__ import annotations

from typing import Any, Dict, List

import httpx
from loguru import logger

from ..config import get_settings


class GatewayClient:
    """Cliente para el API Gateway."""

    def __init__(self, user_id: str, token: str | None = None) -> None:
        self.user_id = user_id
        self.token = token
        settings = get_settings()
        self.base_url = settings.gateway_url
        logger.info("GatewayClient inicializado. URL: {}", self.base_url)

    @property
    def headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token
        return headers

    async def execute(self, query: str, variables: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Ejecuta una query GraphQL contra el gateway."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.debug("Ejecutando query GraphQL: {}", query[:200])
                logger.debug("Variables: {}", variables)
                
                response = await client.post(
                    self.base_url, 
                    json=payload, 
                    headers=self.headers
                )
                
                # Log de respuesta para debugging
                logger.debug("Status code: {}", response.status_code)
                
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error("GraphQL errors: {}", data["errors"])
                    raise RuntimeError(f"GraphQL errors: {data['errors']}")
                
                return data.get("data", {})
                
        except httpx.HTTPError as exc:
            logger.error("Error al conectar con Gateway: {}", exc)
            raise RuntimeError(f"Error conectando con Gateway: {exc}") from exc

    # --- Métodos de conveniencia ---

    async def get_user_budgets(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene los presupuestos del usuario."""
        query = """
        query GetUserBudgets($userId: ID!) {
            budgets(userId: $userId) {
                id
                category
                limitAmount
                currentAmount
                periodStart
                periodEnd
            }
        }
        """
        result = await self.execute(query, {"userId": user_id})
        return result.get("budgets", [])

    async def get_recent_transactions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene transacciones recientes del usuario."""
        query = """
        query GetRecentTransactions($userId: ID!, $limit: Int!) {
            transactions(userId: $userId, limit: $limit, orderBy: {field: "date", direction: DESC}) {
                id
                date
                amount
                category
                description
                type
            }
        }
        """
        result = await self.execute(query, {"userId": user_id, "limit": limit})
        return result.get("transactions", [])

    async def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene las cuentas del usuario."""
        query = """
        query GetUserAccounts($userId: ID!) {
            accounts(userId: $userId) {
                id
                name
                balance
                type
                currency
            }
        }
        """
        result = await self.execute(query, {"userId": user_id})
        return result.get("accounts", [])

    async def get_user_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene las metas financieras del usuario."""
        query = """
        query GetUserGoals($userId: ID!) {
            goals(userId: $userId) {
                id
                name
                targetAmount
                currentAmount
                deadline
                status
            }
        }
        """
        result = await self.execute(query, {"userId": user_id})
        return result.get("goals", [])

    async def register_transaction(
        self,
        account_id: str,
        amount: float,
        transaction_type: str,
        category: str,
        description: str,
    ) -> Dict[str, Any]:
        """Registra una nueva transacción."""
        query = """
        mutation CreateTransaction(
            $accountId: ID!
            $amount: Float!
            $type: TransactionType!
            $category: String!
            $description: String!
        ) {
            createTransaction(
                input: {
                    accountId: $accountId
                    amount: $amount
                    type: $type
                    category: $category
                    description: $description
                }
            ) {
                id
                amount
                category
                description
                type
                date
            }
        }
        """
        variables = {
            "accountId": account_id,
            "amount": amount,
            "type": transaction_type,
            "category": category,
            "description": description,
        }
        result = await self.execute(query, variables)
        return result.get("createTransaction", {})

    async def classify_transaction(self, text: str) -> Dict[str, Any]:
        """Clasifica una transacción usando ML."""
        query = """
        mutation ClassifyTransaction($text: String!) {
            classifyTransaction(text: $text) {
                predictedCategory
                confidence
                suggestedCategories {
                    category
                    confidence
                }
            }
        }
        """
        result = await self.execute(query, {"text": text})
        return result.get("classifyTransaction", {})

    async def analyze_spending_patterns(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Analiza patrones de gasto."""
        query = """
        query AnalyzePatterns($userId: ID!, $startDate: String!, $endDate: String!) {
            analyzeSpendingPatterns(
                userId: $userId
                startDate: $startDate
                endDate: $endDate
            ) {
                patternType
                description
                frequency
                averageAmount
                category
            }
        }
        """
        result = await self.execute(
            query, 
            {
                "userId": self.user_id,
                "startDate": start_date, 
                "endDate": end_date
            }
        )
        return result.get("analyzeSpendingPatterns", [])

    async def generate_forecast(self, months: int = 3) -> List[Dict[str, Any]]:
        """Genera pronóstico financiero."""
        query = """
        query GenerateForecast($userId: ID!, $months: Int!) {
            generateForecast(userId: $userId, months: $months) {
                forecastMonth
                forecastYear
                predictedAmount
                trend
                category
            }
        }
        """
        result = await self.execute(
            query, 
            {"userId": self.user_id, "months": months}
        )
        return result.get("generateForecast", [])

    async def get_predictions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene predicciones recientes."""
        query = """
        query GetPredictions($userId: ID!, $limit: Int!) {
            predictions(userId: $userId, limit: $limit) {
                id
                category
                confidence
                predictedDate
            }
        }
        """
        result = await self.execute(
            query, 
            {"userId": self.user_id, "limit": limit}
        )
        return result.get("predictions", [])