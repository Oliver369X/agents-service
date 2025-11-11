# Agents Service

Microservicio Python responsable de los agentes conversacionales y flujos asistidos por IA:
- **Gemini 2.5 Pro** para diálogo financiero contextual.
- **Mistral OCR** para extracción de contenido estructurado desde documentos.

Se expone una API GraphQL mediante FastAPI + Strawberry, federable con Apollo Gateway.

## Requisitos
- Python 3.11+
- `pipx` o `virtualenv` para aislar dependencias
- Claves activas de Gemini y Mistral OCR

## Instalación
```bash
cd agents-service
python -m venv .venv
. .venv/Scripts/activate  # PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

## Ejecución
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5020 --reload
```

Variables mínimas (`env.example`):
```
GEMINI_API_KEY=...
MISTRAL_OCR_API_KEY=...
```

## Endpoints

### REST (`/agent`)
- `GET /health` → verificación básica.
- `POST /agent/chat` → proxy directo a Gemini 2.5 Pro. Acepta `messages[]` o un `prompt` simple.
- `POST /agent/ocr` → proxy a Mistral OCR (documentos públicos por URL).
- **Orquestador proactivo:**
  - `POST /agent/audit-budget?user_id=...` → auditoría de presupuestos con notificaciones.
  - `POST /agent/process-document?user_id=...` → OCR + registro automático de transacción.
  - `POST /agent/savings-plan?user_id=...` → plan de ahorro personalizado con IA.
- **Flujos avanzados con ML:**
  - `POST /agent/smart-categorize?user_id=...` → categorización inteligente (ML + Gemini).
  - `POST /agent/financial-insights?user_id=...` → reporte completo (DL + ML + Gemini).
  - `POST /agent/spending-alert?user_id=...` → monitoreo proactivo con detección de anomalías.

Ejemplos rápidos:
```bash
curl -X POST http://localhost:5020/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"¿Cómo armo un plan de ahorro mensual?"}'

curl -X POST "http://localhost:5020/agent/audit-budget?user_id=123" \
  -H "Authorization: Bearer <token>"
```

### GraphQL (`/graphql`)
Expone el subgrafo federado (Apollo Federation v2):

**Queries:**
```graphql
query {
  health {
    status
    version
    integrations
  }
}
```

**Mutaciones del orquestador:**
```graphql
mutation {
  auditBudget(userId: "123") {
    status
    analysis
    budgetsReviewed
  }
  processDocument(userId: "123", input: {documentUrl: "...", accountId: "acc1"}) {
    status
    transactionId
  }
  generateSavingsPlan(userId: "123", input: {targetAmount: 5000, months: 12}) {
    status
    plan
  }
}
```

Consulta la documentación extendida en `docs/agents-service.md` y `docs/agents-service-architecture.md`.

## Pruebas
```bash
pytest -v
```
Incluye cobertura para:
- `GET /health`
- Query `health` y mutaciones `chat` / `analyzeDocument` de GraphQL (stubs locales para no consumir créditos).
- Validación del manejo de niveles de log inválidos.
- Endpoints REST `/agent/chat`, `/agent/ocr`.
- **Orquestador:** `run_budget_audit`, `process_document_and_register` (12 tests, 100% passed).

## Arquitectura del Agente Proactivo

El agente combina **4 capas de inteligencia**:

1. **Machine Learning** (`ml-service`):
   - Clasificación automática de transacciones
   - Pronóstico de gastos futuros
   - Detección de anomalías con Deep Learning

2. **IA Generativa** (Gemini 2.5 Pro):
   - Análisis contextual y recomendaciones personalizadas
   - Síntesis de datos complejos
   - Asistencia en decisiones de baja confianza

3. **Datos Financieros** (`core-service`):
   - Consulta y registro de transacciones
   - Gestión de presupuestos y metas
   - Historial completo del usuario

4. **Notificaciones Proactivas** (`notification-service`):
   - Alertas de gasto en tiempo real
   - Reportes financieros periódicos
   - Avisos de metas y presupuestos

### Flujos Avanzados Disponibles

- **Categorización Inteligente**: ML clasifica → si confianza baja, Gemini valida → registra automáticamente.
- **Insights Financieros**: DL analiza patrones → ML pronostica → Gemini sintetiza → notifica reporte.
- **Alertas Proactivas**: ML detecta anomalías → Gemini evalúa riesgo → notifica si es necesario.

Ver `docs/agents-service-architecture.md` para diagramas de flujo y casos de uso detallados.

## Roadmap
- [x] Orquestador básico con auditoría, OCR y plan de ahorro.
- [x] Integración con gateway y notification-service.
- [ ] Memoria conversacional (Redis/Mongo) para contexto por usuario.
- [ ] Rate limiting y cache para llamadas a IA.
- [ ] Validación de permisos antes de operaciones sensibles.
- [ ] Webhooks y eventos asíncronos (Kafka/RabbitMQ).


