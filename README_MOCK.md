# 🤖 Agente Mock - Desarrollo sin API Keys

## ¿Qué es el Agente Mock?

El **MockAgent** es un agente simulado que permite usar todas las funcionalidades de `agents-service` **sin necesidad de API keys externas** (Gemini, Mistral).

## ✨ Ventajas

- ✅ **Desarrollo local** sin costos de APIs
- ✅ **Testing** sin dependencias externas
- ✅ **Demos** sin configuración compleja
- ✅ **CI/CD** sin secrets
- ✅ **Respuestas instantáneas** sin latencia de red

## 🚀 Uso

### Activación Automática

El agente mock se activa automáticamente cuando:

1. `GEMINI_API_KEY` está vacía o no configurada
2. Hay un error al llamar a Gemini (401, 403, 500, etc.)

No necesitas hacer nada especial, el servicio detecta la situación y usa el mock.

### Configuración

En `agents-service/.env`:

```env
# Dejar vacío para usar mock
GEMINI_API_KEY=
MISTRAL_OCR_API_KEY=

# O comentar
# GEMINI_API_KEY=tu-key-aqui
# MISTRAL_OCR_API_KEY=tu-key-aqui
```

## 📋 Funcionalidades del Mock

### 1. Chat Conversacional

**Respuestas contextuales** basadas en palabras clave:

| Palabras clave | Respuesta |
|----------------|-----------|
| hola, buenos días | Saludo personalizado |
| ahorro, ahorrar | Consejos de ahorro |
| gasto, gastos | Análisis de gastos |
| presupuesto | Recomendaciones de presupuestos |
| meta, objetivo | Guía para establecer metas |
| inversión | Consejos de inversión |
| deuda, préstamo | Estrategias para deudas |
| ingreso, salario | Optimización de ingresos |

**Ejemplo**:

```graphql
mutation {
  chat(messages: [
    { role: "user", content: "Hola, ¿cómo puedo ahorrar más?" }
  ]) {
    messages {
      role
      content
    }
  }
}
```

**Respuesta**:
```json
{
  "messages": [
    {
      "role": "model",
      "content": "Para mejorar tus ahorros, te recomiendo: 1) Establece una meta clara, 2) Automatiza transferencias mensuales, 3) Reduce gastos innecesarios. ¿Quieres que genere un plan de ahorro personalizado?\n\n💡 Tip: Revisa tus suscripciones mensuales, muchas veces pagamos por servicios que no usamos."
    }
  ]
}
```

### 2. Auditoría de Presupuestos

```graphql
mutation {
  auditBudget(userId: "user-123") {
    status
    analysis
    budgetsReviewed
    message
  }
}
```

**Respuesta simulada**:
```json
{
  "status": "SUCCESS",
  "analysis": "He revisado tus presupuestos. Tienes 3 presupuestos activos. El de 'Alimentación' está al 85% de su límite...",
  "budgetsReviewed": 3,
  "message": "Auditoría completada."
}
```

### 3. Plan de Ahorro

```graphql
mutation {
  generateSavingsPlan(
    userId: "user-123"
    input: { targetAmount: 5000, months: 12 }
  ) {
    status
    plan
    target
    months
  }
}
```

**Respuesta simulada**:
```json
{
  "status": "SUCCESS",
  "plan": "📊 Plan de Ahorro Personalizado\n\n🎯 Meta: $5,000.00 USD\n⏰ Plazo: 12 meses\n💰 Ahorro mensual requerido: $416.67 USD\n\n...",
  "target": 5000,
  "months": 12
}
```

### 4. OCR de Recibos

```graphql
mutation {
  analyzeDocument(documentUrl: "https://example.com/receipt.jpg") {
    text
    confidence
  }
}
```

**Respuesta simulada**:
```json
{
  "text": "SUPERMERCADO LA FAVORITA\nFecha: 09/11/2025\nTotal: $45.50\nIVA: $5.46\nProductos: Frutas, Verduras, Lácteos",
  "confidence": 0.95
}
```

## 🔄 Cambiar a Gemini Real

Cuando quieras usar Gemini real:

1. Obtén una API key en: https://makersuite.google.com/app/apikey

2. Actualiza `agents-service/.env`:
```env
GEMINI_API_KEY=tu-api-key-real-aqui
```

3. Reinicia el servicio:
```bash
docker-compose -f docker-compose.dev.yml restart agents
```

El servicio detectará la key y usará Gemini automáticamente.

## 🧪 Testing

El mock es perfecto para tests:

```python
# tests/test_mock_agent.py
import pytest
from app.services.mock_agent import MockAgent

@pytest.mark.asyncio
async def test_chat():
    mock = MockAgent()
    response = await mock.chat([{"text": "Hola", "role": "user"}])
    assert "candidates" in response
    assert len(response["candidates"]) > 0

@pytest.mark.asyncio
async def test_budget_audit():
    mock = MockAgent()
    result = await mock.analyze_budget("user-123")
    assert result["status"] == "SUCCESS"
    assert "analysis" in result
```

## 📊 Comparación

| Característica | Gemini Real | Mock Agent |
|----------------|-------------|------------|
| Requiere API key | ✅ Sí | ❌ No |
| Costo | 💰 Sí | 🆓 Gratis |
| Latencia | ~1-2s | <100ms |
| Respuestas | IA avanzada | Contextuales |
| Offline | ❌ No | ✅ Sí |
| Testing | ⚠️ Complejo | ✅ Simple |

## 🎯 Recomendación

- **Desarrollo**: Usa Mock Agent
- **Testing**: Usa Mock Agent
- **Staging**: Usa Gemini real
- **Producción**: Usa Gemini real

## 📝 Notas

- El mock genera respuestas coherentes y útiles
- Las respuestas son deterministas pero variadas
- Incluye tips financieros reales
- Perfecto para UX testing sin costos
- Fallback automático si Gemini falla

---

**Con el Mock Agent, FinWise funciona completamente sin APIs externas** ✅

