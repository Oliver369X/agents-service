"""Orquestador del agente proactivo: coordina consultas, análisis y notificaciones."""
from __future__ import annotations

from typing import Any, Dict, List

from loguru import logger

from ..services.gateway_client import GatewayClient
from ..services.gemini_client import GeminiClient
from ..services.mistral_client import MistralOCRClient
from ..services.notification_client import NotificationClient


class AgentOrchestrator:
    """Orquestador central del agente financiero proactivo."""

    def __init__(self, user_id: str, token: str | None = None) -> None:
        self.user_id = user_id
        self.gateway = GatewayClient(user_id=user_id, token=token)
        self.gemini = GeminiClient()
        self.mistral = MistralOCRClient()
        self.notifier = NotificationClient()

    async def run_budget_audit(self) -> Dict[str, Any]:
        """
        Auditoría proactiva de presupuestos:
        1. Consulta presupuestos y transacciones recientes.
        2. Analiza con Gemini si hay desviaciones.
        3. Genera recomendaciones.
        4. Envía notificación si detecta alertas.
        """
        logger.info("Iniciando auditoría de presupuesto para usuario {}", self.user_id)

        # 1. Obtener datos
        budgets = await self.gateway.get_user_budgets(self.user_id)
        transactions = await self.gateway.get_recent_transactions(self.user_id, limit=20)

        if not budgets:
            return {"status": "no_budgets", "message": "Usuario sin presupuestos configurados."}

        # 2. Preparar contexto para Gemini
        context = self._build_budget_context(budgets, transactions)
        prompt = f"""
Eres un asesor financiero. Analiza el siguiente contexto y genera recomendaciones concretas:

{context}

Responde en formato JSON con:
- "alerts": lista de alertas detectadas (si hay)
- "recommendations": lista de recomendaciones prácticas
- "summary": resumen breve
"""

        # 3. Llamar a Gemini
        gemini_response = await self.gemini.chat([{"role": "user", "text": prompt}])
        analysis = self._extract_gemini_text(gemini_response)

        # 4. Enviar notificación si hay alertas
        if "alerta" in analysis.lower() or "excedido" in analysis.lower():
            await self.notifier.send_notification(
                user_id=self.user_id,
                title="Alerta de Presupuesto",
                message=analysis[:200],
                notification_type="WARNING",
            )

        logger.info("Auditoría completada para {}", self.user_id)
        return {"status": "completed", "analysis": analysis, "budgets_reviewed": len(budgets)}

    async def process_document_and_register(self, document_url: str, account_id: str) -> Dict[str, Any]:
        """
        Procesa un documento (factura, recibo) con OCR y registra la transacción:
        1. Extrae texto con Mistral OCR.
        2. Analiza con Gemini para identificar monto, categoría, descripción.
        3. Registra transacción en core-service.
        4. Notifica al usuario.
        """
        logger.info("Procesando documento {} para usuario {}", document_url, self.user_id)

        # 1. OCR
        ocr_result = await self.mistral.extract_text(document_url)
        extracted_text = ocr_result.get("text", "")

        if not extracted_text:
            return {"status": "error", "message": "No se pudo extraer texto del documento."}

        # 2. Análisis con Gemini
        prompt = f"""
Eres un asistente financiero. Analiza el siguiente texto de un documento y extrae:
- Monto (número)
- Categoría (ej: "Alimentación", "Transporte", "Salud")
- Descripción breve

Texto:
{extracted_text}

Responde en formato JSON:
{{"amount": <número>, "category": "<categoría>", "description": "<descripción>"}}
"""
        gemini_response = await self.gemini.chat([{"role": "user", "text": prompt}])
        parsed = self._parse_transaction_from_gemini(gemini_response)

        if not parsed:
            return {"status": "error", "message": "No se pudo interpretar el documento."}

        # 3. Registrar transacción
        transaction = await self.gateway.register_transaction(
            account_id=account_id,
            amount=parsed["amount"],
            transaction_type="EXPENSE",
            category=parsed["category"],
            description=parsed["description"],
        )

        # 4. Notificar
        await self.notifier.send_notification(
            user_id=self.user_id,
            title="Transacción Registrada",
            message=f"Se registró un gasto de {parsed['amount']} en {parsed['category']}.",
            notification_type="INFO",
        )

        logger.info("Documento procesado y transacción {} creada", transaction.get("id"))
        return {"status": "success", "transaction": transaction, "ocr_text": extracted_text}

    async def generate_savings_plan(self, target_amount: float, months: int) -> Dict[str, Any]:
        """
        Genera un plan de ahorro personalizado:
        1. Consulta ingresos/gastos históricos.
        2. Usa Gemini para proponer un plan mensual.
        3. Crea una meta en core-service.
        4. Notifica al usuario.
        """
        logger.info("Generando plan de ahorro para {} en {} meses", target_amount, months)

        # 1. Datos históricos
        accounts = await self.gateway.get_user_accounts(self.user_id)
        transactions = await self.gateway.get_recent_transactions(self.user_id, limit=30)

        total_balance = sum(float(acc.get("balance", 0)) for acc in accounts)
        avg_expense = self._calculate_avg_expense(transactions)

        # 2. Prompt para Gemini
        prompt = f"""
Eres un asesor financiero. El usuario quiere ahorrar {target_amount} en {months} meses.
Balance actual: {total_balance}
Gasto promedio mensual: {avg_expense}

Genera un plan de ahorro mensual realista en formato JSON:
{{"monthly_savings": <monto>, "recommendations": ["<consejo1>", "<consejo2>"], "feasibility": "<análisis>"}}
"""
        gemini_response = await self.gemini.chat([{"role": "user", "text": prompt}])
        plan = self._extract_gemini_text(gemini_response)

        # 3. Crear meta (simplificado; ajustar según esquema real)
        # Aquí asumiríamos una mutación createGoal en core-service
        # goal = await self.gateway.create_goal(...)

        # 4. Notificar
        await self.notifier.send_notification(
            user_id=self.user_id,
            title="Plan de Ahorro Generado",
            message=f"Tu plan para ahorrar {target_amount} está listo. Revisa los detalles.",
            notification_type="INFO",
        )

        return {"status": "success", "plan": plan, "target": target_amount, "months": months}

    # --- Helpers ---

    def _build_budget_context(self, budgets: List[Dict], transactions: List[Dict]) -> str:
        lines = ["Presupuestos actuales:"]
        for b in budgets:
            lines.append(f"- {b['category']}: límite {b['limitAmount']} ({b['periodStart']} a {b['periodEnd']})")
        lines.append("\nTransacciones recientes:")
        for t in transactions[:10]:
            lines.append(f"- {t.get('date')}: {t.get('amount')} en {t.get('category')} ({t.get('description')})")
        return "\n".join(lines)

    def _extract_gemini_text(self, response: Dict[str, Any]) -> str:
        candidates = response.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return " ".join(p.get("text", "") for p in parts).strip()

    def _parse_transaction_from_gemini(self, response: Dict[str, Any]) -> Dict[str, Any] | None:
        import json

        text = self._extract_gemini_text(response)
        try:
            # Intentar parsear JSON embebido
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        return None

    def _calculate_avg_expense(self, transactions: List[Dict]) -> float:
        expenses = [float(t.get("amount", 0)) for t in transactions if t.get("amount", 0) < 0]
        return abs(sum(expenses) / len(expenses)) if expenses else 0.0

    # --- Flujos avanzados con ML ---

    async def smart_categorize_transaction(self, transaction_text: str, account_id: str, amount: float) -> Dict[str, Any]:
        """
        Categoriza inteligentemente una transacción usando ML y la registra:
        1. Clasifica con ML-service.
        2. Si la confianza es alta (>0.7), registra automáticamente.
        3. Si es baja, pide confirmación a Gemini.
        4. Registra y notifica.
        """
        logger.info("Categorizando transacción con ML para usuario {}", self.user_id)

        # 1. Clasificar con ML
        classification = await self.gateway.classify_transaction(transaction_text)
        predicted_category = classification.get("predictedCategory", "Otros")
        confidence = classification.get("confidence", 0.0)

        # 2. Decisión basada en confianza
        if confidence < 0.7:
            # Baja confianza: consultar a Gemini
            prompt = f"""
Analiza esta transacción y sugiere la mejor categoría:
Texto: {transaction_text}
Monto: {amount}
ML sugiere: {predicted_category} (confianza: {confidence:.2f})

Responde solo con el nombre de la categoría más apropiada.
"""
            gemini_response = await self.gemini.chat([{"role": "user", "text": prompt}])
            final_category = self._extract_gemini_text(gemini_response).strip()
        else:
            final_category = predicted_category

        # 3. Registrar transacción
        transaction = await self.gateway.register_transaction(
            account_id=account_id,
            amount=amount,
            transaction_type="EXPENSE" if amount < 0 else "INCOME",
            category=final_category,
            description=transaction_text,
        )

        # 4. Notificar
        await self.notifier.send_notification(
            user_id=self.user_id,
            title="Transacción Categorizada",
            message=f"Se registró {abs(amount)} en {final_category} (confianza ML: {confidence:.0%}).",
            notification_type="INFO",
        )

        return {
            "status": "success",
            "transaction": transaction,
            "category": final_category,
            "ml_confidence": confidence,
            "method": "ml" if confidence >= 0.7 else "gemini_assisted",
        }

    async def generate_financial_insights(self) -> Dict[str, Any]:
        """
        Genera insights financieros completos combinando ML y Gemini:
        1. Analiza patrones de gasto (DL).
        2. Genera pronóstico de 3 meses (ML).
        3. Consulta presupuestos y metas actuales.
        4. Sintetiza todo con Gemini para recomendaciones personalizadas.
        5. Notifica al usuario con el reporte.
        """
        logger.info("Generando insights financieros para usuario {}", self.user_id)

        # 1. Análisis de patrones (últimos 90 días)
        from datetime import datetime, timedelta

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        patterns = await self.gateway.analyze_spending_patterns(start_date, end_date)

        # 2. Pronóstico de 3 meses
        forecast = await self.gateway.generate_forecast(months=3)

        # 3. Datos actuales
        budgets = await self.gateway.get_user_budgets(self.user_id)
        goals = await self.gateway.get_user_goals(self.user_id)
        accounts = await self.gateway.get_user_accounts(self.user_id)

        # 4. Construir contexto para Gemini
        context = f"""
Análisis financiero del usuario:

PATRONES DE GASTO (últimos 90 días):
{self._format_patterns(patterns)}

PRONÓSTICO (próximos 3 meses):
{self._format_forecast(forecast)}

PRESUPUESTOS ACTUALES:
{self._format_budgets(budgets)}

METAS FINANCIERAS:
{self._format_goals(goals)}

BALANCE ACTUAL:
{self._format_accounts(accounts)}

Genera un reporte ejecutivo con:
1. Resumen de salud financiera (0-100)
2. Top 3 insights clave
3. Top 3 recomendaciones accionables
4. Alertas urgentes (si las hay)

Formato JSON:
{{
  "health_score": <número>,
  "insights": ["<insight1>", "<insight2>", "<insight3>"],
  "recommendations": ["<rec1>", "<rec2>", "<rec3>"],
  "alerts": ["<alerta1>", ...]
}}
"""

        # 5. Análisis con Gemini
        gemini_response = await self.gemini.chat([{"role": "user", "text": context}])
        analysis = self._extract_gemini_text(gemini_response)

        # 6. Notificar
        await self.notifier.send_notification(
            user_id=self.user_id,
            title="Reporte Financiero Mensual",
            message="Tu análisis financiero personalizado está listo. Revisa los insights y recomendaciones.",
            notification_type="INFO",
        )

        return {
            "status": "success",
            "patterns": patterns,
            "forecast": forecast,
            "analysis": analysis,
            "generated_at": datetime.now().isoformat(),
        }

    async def proactive_spending_alert(self) -> Dict[str, Any]:
        """
        Monitoreo proactivo de gastos:
        1. Obtiene predicciones ML de categorías frecuentes.
        2. Compara con presupuestos.
        3. Detecta anomalías con patrones DL.
        4. Genera alertas personalizadas con Gemini.
        5. Notifica si hay riesgos.
        """
        logger.info("Ejecutando monitoreo proactivo para usuario {}", self.user_id)

        # 1. Predicciones recientes
        predictions = await self.gateway.get_predictions(limit=20)

        # 2. Presupuestos
        budgets = await self.gateway.get_user_budgets(self.user_id)

        # 3. Patrones (últimos 30 días)
        from datetime import datetime, timedelta

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        patterns = await self.gateway.analyze_spending_patterns(start_date, end_date)

        # 4. Detectar anomalías
        alerts = []
        for pattern in patterns:
            if pattern.get("patternType") == "anomaly":
                alerts.append(pattern)

        # 5. Si hay alertas, analizar con Gemini
        if alerts or len(predictions) > 15:
            prompt = f"""
Análisis de riesgo financiero:

PATRONES ANÓMALOS:
{self._format_patterns(alerts)}

ACTIVIDAD RECIENTE:
{len(predictions)} transacciones en los últimos días.

PRESUPUESTOS:
{self._format_budgets(budgets)}

¿Hay riesgos? Genera un mensaje de alerta breve y accionable (máx 200 caracteres).
Si no hay riesgo, responde "OK".
"""
            gemini_response = await self.gemini.chat([{"role": "user", "text": prompt}])
            alert_message = self._extract_gemini_text(gemini_response).strip()

            if alert_message != "OK":
                await self.notifier.send_notification(
                    user_id=self.user_id,
                    title="Alerta de Gasto",
                    message=alert_message,
                    notification_type="WARNING",
                )
                return {"status": "alert_sent", "message": alert_message, "anomalies": len(alerts)}

        return {"status": "no_alerts", "anomalies_detected": len(alerts)}

    # --- Helpers para formateo ---

    def _format_patterns(self, patterns: List[Dict]) -> str:
        if not patterns:
            return "No hay patrones detectados."
        lines = []
        for p in patterns[:5]:
            lines.append(
                f"- {p.get('patternType', 'N/A')}: {p.get('description', 'N/A')} "
                f"(frecuencia: {p.get('frequency', 'N/A')}, promedio: {p.get('averageAmount', 0)})"
            )
        return "\n".join(lines)

    def _format_forecast(self, forecast: List[Dict]) -> str:
        if not forecast:
            return "No hay pronóstico disponible."
        lines = []
        for f in forecast[:3]:
            lines.append(
                f"- {f.get('forecastMonth')}/{f.get('forecastYear')}: "
                f"{f.get('predictedAmount', 0)} (tendencia: {f.get('trend', 'N/A')})"
            )
        return "\n".join(lines)

    def _format_budgets(self, budgets: List[Dict]) -> str:
        if not budgets:
            return "Sin presupuestos configurados."
        lines = []
        for b in budgets[:5]:
            lines.append(f"- {b.get('category')}: {b.get('limitAmount')} ({b.get('periodStart')} a {b.get('periodEnd')})")
        return "\n".join(lines)

    def _format_goals(self, goals: List[Dict]) -> str:
        if not goals:
            return "Sin metas configuradas."
        lines = []
        for g in goals[:5]:
            progress = (float(g.get("currentAmount", 0)) / float(g.get("targetAmount", 1))) * 100
            lines.append(f"- {g.get('name')}: {progress:.0f}% completado (meta: {g.get('targetAmount')})")
        return "\n".join(lines)

    def _format_accounts(self, accounts: List[Dict]) -> str:
        if not accounts:
            return "Sin cuentas."
        total = sum(float(a.get("balance", 0)) for a in accounts)
        return f"Balance total: {total} en {len(accounts)} cuenta(s)."

