"""Mock Agent para desarrollo sin API keys externas."""
import random
from typing import Any, Dict, List


class MockAgent:
    """Agente simulado que responde sin necesidad de APIs externas."""

    def __init__(self):
        self.responses = [
            "Entiendo tu consulta. Basándome en tus datos financieros, te recomiendo revisar tus gastos en la categoría de entretenimiento.",
            "Excelente pregunta. Para mejorar tus finanzas, considera establecer un presupuesto mensual y seguirlo de cerca.",
            "He analizado tu situación. Tu balance actual es positivo, pero podrías ahorrar más reduciendo gastos innecesarios.",
            "Según tus patrones de gasto, te sugiero crear una meta de ahorro automática del 10% de tus ingresos mensuales.",
            "Perfecto. Veo que has sido consistente con tus presupuestos. Continúa así y alcanzarás tus metas financieras.",
            "Interesante. Para optimizar tus finanzas, te recomiendo usar la función de categorización automática de gastos.",
            "Basándome en tu historial, tu mayor gasto es en alimentación. Considera preparar más comidas en casa para ahorrar.",
            "Excelente progreso. Has reducido tus gastos un 15% este mes comparado con el anterior. ¡Sigue así!",
        ]

        self.financial_tips = [
            "💡 Tip: Revisa tus suscripciones mensuales, muchas veces pagamos por servicios que no usamos.",
            "📊 Consejo: Establece un fondo de emergencia equivalente a 3-6 meses de gastos.",
            "💰 Recomendación: Automatiza tus ahorros para que se descuenten automáticamente cada mes.",
            "🎯 Meta: Intenta ahorrar al menos el 20% de tus ingresos mensuales.",
        ]

    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Simula una respuesta del agente."""
        last_message = messages[-1]["text"] if messages else ""
        
        # Generar respuesta basada en palabras clave
        response_text = self._generate_response(last_message)
        
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": response_text}
                        ]
                    }
                }
            ]
        }

    def _generate_response(self, message: str) -> str:
        """Genera una respuesta contextual basada en el mensaje."""
        message_lower = message.lower()
        
        # Respuestas contextuales
        if any(word in message_lower for word in ['hola', 'buenos', 'saludos']):
            return "¡Hola! 👋 Soy tu asistente financiero FinWise. Estoy aquí para ayudarte a gestionar mejor tu dinero. ¿En qué puedo ayudarte hoy?"
        
        if any(word in message_lower for word in ['ahorro', 'ahorrar', 'guardar']):
            return "Para mejorar tus ahorros, te recomiendo: 1) Establece una meta clara, 2) Automatiza transferencias mensuales, 3) Reduce gastos innecesarios. ¿Quieres que genere un plan de ahorro personalizado?"
        
        if any(word in message_lower for word in ['gasto', 'gastos', 'gastando']):
            return "He revisado tus gastos recientes. Las categorías con mayor impacto son: Alimentación y Entretenimiento. Te sugiero establecer presupuestos para estas categorías y usar la función de alertas automáticas."
        
        if any(word in message_lower for word in ['presupuesto', 'budget']):
            return "Los presupuestos son clave para el control financiero. Te recomiendo: 1) Crear presupuestos por categoría, 2) Revisarlos semanalmente, 3) Ajustarlos según tus necesidades. ¿Quieres que ejecute una auditoría de tus presupuestos actuales?"
        
        if any(word in message_lower for word in ['meta', 'objetivo', 'goal']):
            return "Establecer metas financieras es excelente. Para metas efectivas: 1) Hazlas específicas y medibles, 2) Establece plazos realistas, 3) Divide metas grandes en pasos pequeños. ¿Qué meta tienes en mente?"
        
        if any(word in message_lower for word in ['inversión', 'invertir', 'investment']):
            return "Para inversiones, considera: 1) Tu perfil de riesgo, 2) Diversificación, 3) Horizonte temporal. Recuerda que toda inversión conlleva riesgos. Consulta con un asesor financiero profesional."
        
        if any(word in message_lower for word in ['deuda', 'deber', 'préstamo']):
            return "Para manejar deudas efectivamente: 1) Lista todas tus deudas, 2) Prioriza las de mayor interés, 3) Considera consolidación si es viable. ¿Necesitas ayuda para crear un plan de pago?"
        
        if any(word in message_lower for word in ['ingreso', 'ingresos', 'salario']):
            return "Para optimizar tus ingresos: 1) Registra todas las fuentes, 2) Busca oportunidades de ingresos adicionales, 3) Invierte en tu desarrollo profesional. El crecimiento de ingresos es tan importante como controlar gastos."
        
        # Respuesta genérica con tip aleatorio
        response = random.choice(self.responses)
        tip = random.choice(self.financial_tips)
        return f"{response}\n\n{tip}"

    async def analyze_budget(self, user_id: str) -> Dict[str, Any]:
        """Simula análisis de presupuestos."""
        return {
            "status": "SUCCESS",
            "analysis": f"He revisado tus presupuestos. Tienes 3 presupuestos activos. El de 'Alimentación' está al 85% de su límite. Te recomiendo ajustar tus gastos en esta categoría para no exceder el presupuesto.",
            "budgets_reviewed": 3,
            "message": "Auditoría completada. Revisa las recomendaciones arriba."
        }

    async def generate_savings_plan(self, target: float, months: int) -> Dict[str, Any]:
        """Simula generación de plan de ahorro."""
        monthly = target / months if months > 0 else 0
        
        plan = f"""
📊 Plan de Ahorro Personalizado

🎯 Meta: ${target:,.2f} USD
⏰ Plazo: {months} meses
💰 Ahorro mensual requerido: ${monthly:,.2f} USD

📋 Estrategia recomendada:

1. Ahorro Automático:
   - Configura transferencia automática de ${monthly:,.2f} al inicio de cada mes
   - Usa una cuenta de ahorros separada

2. Reducción de Gastos:
   - Identifica gastos no esenciales (${monthly * 0.3:,.2f} USD)
   - Reduce salidas a restaurantes (${monthly * 0.2:,.2f} USD)
   - Optimiza suscripciones (${monthly * 0.1:,.2f} USD)

3. Incremento de Ingresos:
   - Busca ingresos adicionales (freelance, ventas)
   - Objetivo: ${monthly * 0.4:,.2f} USD extra/mes

4. Monitoreo:
   - Revisa tu progreso semanalmente
   - Ajusta el plan según necesites
   - Usa las alertas automáticas de FinWise

🎉 Con disciplina y este plan, alcanzarás tu meta en {months} meses!
"""
        
        return {
            "status": "SUCCESS",
            "plan": plan.strip(),
            "target": target,
            "months": months
        }

    async def extract_text_from_receipt(self, image_url: str) -> Dict[str, Any]:
        """Simula extracción OCR de un recibo."""
        return {
            "text": "SUPERMERCADO LA FAVORITA\nFecha: 09/11/2025\nTotal: $45.50\nIVA: $5.46\nProductos: Frutas, Verduras, Lácteos",
            "confidence": 0.95,
            "amount": 45.50,
            "merchant": "Supermercado La Favorita",
            "date": "2025-11-09"
        }

