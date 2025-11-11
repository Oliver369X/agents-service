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
            # En la vida real, se usa 'Bearer <token>'
            headers["Authorization"] = f"Bearer {self.token}" if not self.token.startswith("Bearer ") else self.token
        return headers

    async def execute(self, query: str, variables: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Ejecuta una query GraphQL contra el gateway."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Log de debug antes de la llamada
                logger.debug("Ejecutando query GraphQL: {}", query[:200].strip())
                logger.debug("Variables: {}", variables)
                
                response = await client.post(
                    self.base_url, 
                    json=payload, 
                    headers=self.headers
                )
                
                # Log de respuesta para debugging
                logger.debug("Status code: {}", response.status_code)
                
                # Esto lanzará una excepción si el código de estado es un error (4xx o 5xx)
                response.raise_for_status()
                
                # Si no hubo error HTTP, procesar el JSON
                data = response.json()
                
                if "errors" in data:
                    logger.error("GraphQL errors: {}", data["errors"])
                    # Elevar un RuntimeError si hay errores de GraphQL
                    raise RuntimeError(f"GraphQL errors: {data['errors']}")
                
                return data.get("data", {})
                
        except httpx.HTTPError as exc:
            # Captura errores HTTP (incluyendo 400 Bad Request)
            logger.error("Error al conectar con Gateway: {}", exc)
            
            # --- LÓGICA DE DIAGNÓSTICO (mantida y mejorada) ---
            if exc.response is not None:
                logger.error("Response Status Code: {}", exc.response.status_code)
                try:
                    error_data = exc.response.json()
                    logger.error("Gateway Error Details (JSON): {}", error_data)
                    error_message = error_data.get("errors", "Unknown GraphQL Error")
                    # Usar los detalles del JSON en el mensaje de excepción para el llamador
                    raise RuntimeError(f"Error conectando con Gateway (GraphQL): {error_message}") from exc
                except Exception:
                    logger.error("Gateway Error Details (Text): {}", exc.response.text)
                    raise RuntimeError(f"Error conectando con Gateway (Status {exc.response.status_code}): {exc.response.text}") from exc
            else:
                # Caso donde no hay respuesta (ej. Timeout, error de red o DNS)
                raise RuntimeError(f"Error conectando con Gateway: {exc}") from exc
            # --- FIN DE LA LÓGICA DE DIAGNÓSTICO ---

    # --- Métodos de conveniencia ---

    async def get_user_budgets(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene los presupuestos del usuario. Corregido el tipo de variable a String! y los campos."""
        query = """
        query BudgetsByUser($userId: String!) {
            budgetsByUser(userId: $userId) {
                id
                userId
                category
                limitAmount # <-- Añadido según la corrección anterior
                periodStart
                periodEnd
                createdAt
                updatedAt
            }
        }
        """
        logger.debug("Ejecutando query GraphQL: {}", query[:200])
        result = await self.execute(query, {"userId": user_id})
        return result.get("budgetsByUser", [])

    async def get_recent_transactions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene predicciones recientes. Corregido para usar 'limit' y 'offset' sin 'userId'."""
        query = """
        query GetPredictions($limit: Int, $offset: Int) {
            predictions(limit: $limit, offset: $offset) { 
                id
                userId
                transactionId
                inputText
                predictedCategory
                confidence
                modelVersion
                createdAt
            }
        }
        """
        # Se eliminó userId de las variables
        result = await self.execute(
            query, 
            {"limit": limit, "offset": 10}
        ) 
        return result.get("predictions", [])

    async def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene las cuentas del usuario. Corregido el nombre del query a accountsByUser y String!."""
        query = """
        query GetUserAccounts($userId: String!) {
            accountsByUser(userId: $userId) {
                id
                name
                balance
                type
                currency
            }
        }
        """
        result = await self.execute(query, {"userId": user_id})
        return result.get("accountsByUser", []) # <-- Corregido el nombre de la clave de retorno

    async def get_user_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene las metas financieras del usuario. Corregido el tipo de variable a String!."""
        # Se asume que el resolver es 'goals' y el tipo de variable es String! (como budgets y accounts)
        query = """
        query GetUserGoals($userId: String!) {
            goals(userId: $userId) {
                id
                name
                targetAmount
                currentAmount
                targetDate # <-- Corregido de 'deadline' a 'targetDate' (según tu CreateGoal)
                # status <-- El campo 'status' fue eliminado ya que no aparece en tu CreateGoal funcional
            }
        }
        """
        # Se elimina 'status' de la query, y se cambia 'deadline' por 'targetDate'
        result = await self.execute(query, {"userId": user_id})
        return result.get("goals", [])

    async def register_transaction(
        self,
        account_id: str,
        amount: float,
        transaction_type: str,
        description: str,
        category: str | None = None, # <-- 'category' parece opcional en tu 'RegisterTransaction' funcional
    ) -> Dict[str, Any]:
        """Registra una nueva transacción. Corregido el nombre del resolver a 'registerTransaction' y el payload."""
        
        # El campo 'category' fue eliminado del payload de tu consulta funcional 'RegisterTransaction',
        # pero para mantener la funcionalidad de tu código original, lo mantendremos como argumento, 
        # asumiendo que el esquema permite la entrada.
        
        query = """
        mutation RegisterTransaction(
            $input: RegisterTransactionInput!
        ) {
            registerTransaction(
                input: $input
            ) {
                id
                # Se devuelven campos simples, tu consulta funcional solo devuelve el 'account'
                # Para ser más útil, se asumen campos de transacción básicos
                id
                account { id userId name balance }
                # Asumiendo que existen otros campos de la transacción
                # amount
                # type
                # description
            }
        }
        """
        variables = {
            "input": {
                "accountId": account_id,
                "amount": amount,
                "type": transaction_type,
                "description": description,
                # Tu consulta funcional no incluye category ni occurredAt, lo mantendremos para compatibilidad
                "category": category, 
                # Si el campo 'occurredAt' es obligatorio en el esquema, debes añadirlo aquí.
            }
        }
        # Nota: La query de retorno se ha simplificado para coincidir con tu ejemplo.
        result = await self.execute(query, variables)
        return result.get("registerTransaction", {}) # <-- Corregido el nombre de la clave de retorno

    async def classify_transaction(self, text: str, amount: float) -> Dict[str, Any]:
        """Clasifica una transacción usando ML. Corregido para usar ClassifyTransactionInput con 'text' y 'amount'."""
        query = """
        mutation ClassifyTransaction($input: ClassifyTransactionInput!) {
            classifyTransaction(input: $input) {
                id # <-- Añadido según tu respuesta de ejemplo
                userId
                transactionId
                inputText
                predictedCategory
                confidence
                modelVersion
                createdAt
            }
        }
        """
        # Se hace obligatorio 'amount' en la firma del método para reflejar tu payload funcional
        variables = {"input": {"text": text, "amount": amount}} 
        
        result = await self.execute(query, variables)
        return result.get("classifyTransaction", {})

    async def analyze_spending_patterns(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Analiza patrones de gasto. Se mantiene la query original al no haber un ejemplo funcional."""
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
        """Genera pronóstico financiero. Se mantiene la query original al no haber un ejemplo funcional."""
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

    async def get_predictions(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtiene predicciones recientes. Corregido para usar 'limit' y 'offset' sin 'userId'."""
        query = """
        query GetPredictions($limit: Int, $offset: Int) {
            predictions(limit: $limit, offset: $offset) { 
                id
                userId
                transactionId
                inputText
                predictedCategory
                confidence
                modelVersion
                createdAt
            }
        }
        """
        # Se eliminó userId de las variables
        result = await self.execute(
            query, 
            {"limit": limit, "offset": offset}
        ) 
        return result.get("predictions", [])