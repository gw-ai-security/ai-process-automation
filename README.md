# AI Process Automation Portfolio

Implemented automation and integration projects focused on **APIs, webhooks, workflow orchestration, persistence, auditability, reliability patterns and bounded AI-assisted processing**.

> **10-second summary:** the strongest modules are a signed webhook integration hub and a workflow automation MVP. Both are local portfolio systems with explicit failure handling and scope boundaries; mocked external systems and illustrative ROI estimates are not presented as production evidence.

## Recruiter Snapshot

| Module | What it demonstrates | Core technologies | Status |
|---|---|---|---|
| [`01-rest-api-integration-hub/`](01-rest-api-integration-hub/) | Signed webhook intake, transformation, idempotency, replay protection, mock system integration, audit and DLQ-style handling | FastAPI, PostgreSQL, Docker Compose, n8n, HMAC | **Implemented local portfolio project** |
| [`02-ai-workflow-automation-engine/`](02-ai-workflow-automation-engine/) | Operational intake, structured AI-assisted extraction, routing, persistence and workflow metrics | FastAPI, PostgreSQL, n8n, Docker Compose, LLM adapter | **Implemented MVP** |
| [`00-rest-api-basics/`](00-rest-api-basics/) | Earlier REST/API exercises | Python / HTTP basics | Learning sandbox |

## 01 — REST API Integration Hub

A local integration hub for signed webhook intake and downstream automation.

```text
Signed webhook
      ↓
FastAPI validation
      ↓
HMAC / timestamp checks
      ↓
Idempotency + replay protection
      ↓
Transformation
      ↓
PostgreSQL / audit / DLQ-style handling
      ↓
n8n orchestration
      ↓
Mock CRM + mock Jira/Confluence targets
```

### Implemented evidence

- FastAPI webhook/API layer
- HMAC-signed requests using timestamp and signature headers
- payload validation and transformation
- idempotency and replay-protection logic
- audit logging
- Dead Letter Queue / error-path handling
- KPI aggregation
- n8n orchestration
- Docker Compose local environment
- smoke tests for happy and error paths

**Boundary:** downstream business systems are simulated. The project demonstrates integration mechanics and safeguards, not a real enterprise deployment.

→ **[Open project](01-rest-api-integration-hub/README.md)**

---

## 02 — AI Workflow Automation Engine

A webhook-driven MVP that turns unstructured operational intake into structured workflow state.

```text
Operational intake
      ↓
FastAPI
      ↓
Structured extraction
      ↓
Routing logic
      ↓
PostgreSQL persistence
      ↓
n8n branching
      ↓
Mock Jira / Mock Slack targets
```

### Implemented evidence

- `POST /intake`
- `GET /health`
- `GET /workflow/{id}`
- `GET /metrics/summary`
- mock Jira and Slack endpoints
- structured extraction of summary, action items, priority and route
- deterministic mock mode plus OpenAI-compatible adapter mode
- persisted workflow state, outputs, events, errors and metrics
- n8n workflow export
- pytest-based test execution

**Boundary:** the automation-impact metric uses configurable manual/automated time assumptions. It is an illustrative model, not validated business ROI.

→ **[Open project](02-ai-workflow-automation-engine/README.md)**

## Technical Stack by System Role

| Role | Evidence |
|---|---|
| **Connect / Intake** | REST APIs and webhooks |
| **Buffer / Workflow state** | persisted workflow/event records; no dedicated message broker is claimed in these modules |
| **Processing** | validation, transformation, routing and bounded AI extraction |
| **Storage** | PostgreSQL |
| **Orchestration** | n8n |
| **Security** | HMAC verification, timestamps, replay protection, idempotency |
| **Reliability** | validation, explicit error paths, DLQ-style handling, smoke tests |
| **Auditability** | audit logs plus persisted workflow/event state |
| **AI boundary** | adapter-based structured extraction; AI is workflow assistance, not autonomous authority |
| **Infrastructure** | Docker Compose |

## Engineering Lessons and Failure Modes

The useful engineering work in these projects is not simply calling an API or an LLM.

- **Webhook authenticity must be checked before business processing.** Signature validation and timestamp handling belong at the trust boundary.
- **Retries create duplicate risk.** Idempotency and replay protection are necessary when the same event may arrive more than once.
- **Failure needs a destination.** Validation or downstream errors should remain inspectable instead of disappearing into logs only.
- **Workflow state must be persisted.** A successful HTTP response is not enough to explain what happened later.
- **External integration should be separated from internal logic.** Mock adapters make the portfolio implementation reproducible while keeping the boundary explicit.
- **Probabilistic AI output needs deterministic surrounding contracts.** Structured extraction is bounded by routing and persistence logic rather than being treated as a complete autonomous workflow.
- **Estimated time savings are assumptions until measured in a real process.** The repository keeps that distinction explicit.

## Scope and Limitations

This repository does **not** claim:

- production authentication or enterprise IAM
- real Jira, Slack, CRM or Confluence deployment
- enterprise hosting or production observability
- multi-agent autonomy
- validated financial ROI
- production operational ownership

## Suggested Review Path

1. [`01-rest-api-integration-hub/`](01-rest-api-integration-hub/) — strongest evidence for integration security, reliability and failure handling
2. [`02-ai-workflow-automation-engine/`](02-ai-workflow-automation-engine/) — structured AI-assisted workflow state and persistence
3. [`00-rest-api-basics/`](00-rest-api-basics/) — earlier exercises only

## TL;DR

This repository demonstrates how I approach automation as an engineering system: **trust boundary → validation → idempotency/replay handling → transformation → persistence → orchestration → explicit failure paths → auditability**. AI is added only inside that controlled workflow rather than used as a substitute for system design.
