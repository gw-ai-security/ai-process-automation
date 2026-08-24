# AI Process Automation Portfolio

Portfolio of implemented automation and integration projects focused on **APIs, webhooks, workflow orchestration, persistence, auditability, and bounded AI-assisted processing**.

> **Evidence principle:** this repository documents what is actually implemented. Planned ideas, simulated integrations, and production deployments are treated as different evidence levels.

## Recruiter Snapshot

| Module | What it demonstrates | Core technologies | Status |
|---|---|---|---|
| [`00-rest-api-basics/`](00-rest-api-basics/) | Small REST/API learning exercises | Python / HTTP basics | Learning sandbox |
| [`01-rest-api-integration-hub/`](01-rest-api-integration-hub/) | Signed webhook intake, validation, transformation, mock system integration, audit/DLQ/KPI handling | FastAPI, PostgreSQL, Docker Compose, n8n, HMAC | Implemented local portfolio project |
| [`02-ai-workflow-automation-engine/`](02-ai-workflow-automation-engine/) | Webhook-driven operational intake, structured LLM extraction, routing, persistence and workflow metrics | FastAPI, PostgreSQL, n8n, Docker Compose, LLM adapter | Implemented MVP |

The repository currently contains these three modules. Additional automation ideas are not presented here as completed projects.

---

## 01 — REST API Integration Hub

A local, reproducible integration hub for signed webhook intake and downstream automation.

Implemented evidence includes:

- FastAPI-based webhook/API layer
- HMAC-signed requests using timestamp and signature headers
- payload validation and transformation
- mock CRM upsert flow
- mock Jira/Confluence target handling
- idempotency and replay-protection logic
- audit logging
- Dead Letter Queue / error-path handling
- KPI aggregation
- n8n orchestration
- Docker Compose-based local environment
- smoke-test scripts for happy and error paths

The external systems are simulated. The project demonstrates integration mechanics and operational safeguards without claiming a production third-party deployment.

→ [`01-rest-api-integration-hub/README.md`](01-rest-api-integration-hub/README.md)

---

## 02 — AI Workflow Automation Engine

Webhook-driven MVP for turning unstructured operational intake into structured workflow output.

Implemented flow:

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

Implemented evidence includes:

- `POST /intake`
- `GET /health`
- `GET /workflow/{id}`
- `GET /metrics/summary`
- mock Jira and Slack endpoints
- structured extraction of summary, action items, priority and route
- deterministic mock mode plus OpenAI-compatible adapter mode
- persistence of workflow state, outputs, events, errors and metrics
- n8n workflow export
- illustrative automation-impact metric using configurable manual/automated time assumptions
- pytest-based test execution

Explicit non-goals in the current MVP:

- production authentication or user accounts
- real Jira or Slack integration
- multi-agent runtime
- production-grade financial ROI claims
- enterprise deployment architecture

→ [`02-ai-workflow-automation-engine/README.md`](02-ai-workflow-automation-engine/README.md)

---

## Capability Matrix

| Capability | Evidence |
|---|---|
| REST API design | FastAPI endpoints in integration and workflow modules |
| Webhook processing | signed intake and operational intake workflows |
| Workflow orchestration | n8n |
| Persistence | PostgreSQL |
| Containerized local execution | Docker Compose |
| Security-aware integration | HMAC verification, replay protection, idempotency |
| Reliability patterns | validation, error handling, DLQ-style handling, smoke tests |
| Auditability | structured logs / persisted workflow and event records |
| AI-assisted processing | structured extraction with bounded adapter layer |
| Operational metrics | KPI aggregation and illustrative automation-impact metrics |

## Repository Structure

```text
ai-process-automation/
├── 00-rest-api-basics/                  # learning exercises
├── 01-rest-api-integration-hub/         # implemented integration project
├── 02-ai-workflow-automation-engine/    # implemented automation MVP
└── README.md
```

## Scope and Limitations

This is a portfolio and learning repository, not evidence of a production deployment.

- external business systems are mocked
- no real third-party credentials are included
- local Docker/n8n execution is not equivalent to enterprise hosting
- AI output is used as bounded workflow assistance, not autonomous authority
- ROI/time-saved figures in the workflow MVP are illustrative estimates rather than validated business outcomes

## Suggested Review Path

For a technical review:

1. [`01-rest-api-integration-hub/`](01-rest-api-integration-hub/) — integration security, webhook handling, auditability and error paths
2. [`02-ai-workflow-automation-engine/`](02-ai-workflow-automation-engine/) — structured AI-assisted workflow automation and persistence
3. [`00-rest-api-basics/`](00-rest-api-basics/) — earlier learning exercises

---

**Portfolio principle:** implemented capability, simulated integration, planned architecture and production experience are different evidence levels.
