# AI Workflow Automation Engine

Webhook-driven workflow automation engine for summarization, routing and automation impact tracking.

## Problem

Operational teams receive unstructured intake across meetings, support channels, and handoff notes. Manual triage is slow and inconsistent, causing delayed routing and unclear ROI.

## Solution

This MVP implements one end-to-end operational intake workflow:

- FastAPI ingestion and retrieval APIs
- Structured LLM extraction (summary, action items, priority, route)
- PostgreSQL persistence for inputs, outputs, events, errors, and metrics
- n8n branching workflow with mock Jira and mock Slack integrations
- KPI summary endpoint with estimated automation impact

## Business Value

- Faster triage and routing consistency
- auditable workflow records for debugging and compliance
- measurable, illustrative automation impact (`saved_minutes`)

## MVP Scope

- `POST /intake`
- `GET /health`
- `GET /workflow/{id}`
- `GET /metrics/summary`
- `POST /mock/jira`
- `POST /mock/slack`
- n8n export: `n8n/workflows/operational-intake-mvp.json`

## Explicit Non-Goals

- frontend dashboard
- auth and user accounts
- multi-agent runtime
- real production Jira/Slack integrations
- multi-provider AI switching

## Architecture

- API: `app/main.py`, `app/api/`
- Processing: `app/services/workflow_service.py`
- LLM adapter: `app/services/llm_service.py` (`LLM_MODE=mock|openai`)
- Routing: `app/services/routing_service.py`
- KPI/ROI: `app/services/roi_service.py`
- Persistence: `app/db/queries.py`, `sql/001_init.sql`
- Orchestration: `n8n/workflows/operational-intake-mvp.json`

## Run (Docker Compose)

1. Create env file:

```bash
cp .env.example .env
```

2. Start services:

```bash
docker compose up --build
```

3. Endpoints:

- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- n8n: `http://localhost:5678`

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `LLM_MODE`: `mock` (default) or `openai`
- `LLM_BASE_URL`: OpenAI-compatible base URL
- `LLM_API_KEY`: required when `LLM_MODE=openai`
- `LLM_MODEL`: model name for OpenAI-compatible calls
- `MANUAL_BASELINE_MINUTES`: baseline manual handling duration
- `AUTOMATED_MINUTES`: estimated automated handling duration

## Example Intake Request

```bash
curl -X POST http://localhost:8000/intake \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "support_text",
    "source_system": "helpdesk",
    "content": "Urgent customer incident with repeated outage symptoms.",
    "submitted_by": "support.agent@example.com",
    "tags": ["incident", "customer"],
    "priority": "high"
  }'
```

## Tests

```bash
pytest
```

## Known Limits

- mock mode uses deterministic classification heuristics
- ROI is an illustrative estimate, not a validated financial claim
- n8n workflow is MVP-level and uses mock targets


## Review updates (October 2026)

The missing `.env.example` was restored. Keep `LLM_MODE=mock` for a deterministic offline demonstration; real OpenAI-compatible calls require an API key and are not covered by mock-only tests. Docker Compose now binds published ports to `127.0.0.1`. Authentication, real integrations and measured savings are outside this MVP.

Verification:

```bash
pip install -r requirements.txt
python -m pytest -q
cp .env.example .env
docker compose config -q
```

See the [portfolio engineering review](../docs/REVIEW_2026-10-21.md) for verified tests and remaining risks.
