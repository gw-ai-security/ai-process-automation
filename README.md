# AI Process Automation — Engineering Portfolio

**Three bounded projects demonstrating integration engineering, AI-assisted workflow automation and pre-dispatch quality controls.** All use synthetic data and local or mocked business systems. No enterprise production deployment or measured commercial ROI is claimed.

## Recruiter overview

| Project | Business problem | Delivered engineering evidence | Stack |
| --- | --- | --- | --- |
| **[01 · REST API Integration Hub](01-rest-api-integration-hub/README.md)** | Duplicate, unsafe and untraceable lead integrations | HMAC-signed lead API, timestamp check, run idempotency, mock CRM, audit metadata, failure/DLQ records and KPI counters | Python, FastAPI, PostgreSQL, Docker Compose, n8n export |
| **[02 · AI Workflow Automation Engine](02-ai-workflow-automation-engine/README.md)** | Manual classification and routing of unstructured operational requests | Structured extraction, priority routing, mock Jira/Slack, persisted workflow state, metrics and deterministic offline LLM mock | Python, FastAPI, PostgreSQL, n8n, OpenAI-compatible adapter |
| **[03 · LLM Output Quality Gate](03-llm-quality-gate/README.md)** | AI-generated actions reaching business tools without a decision gate | Strict output contract, sensitive-content flags, threshold, human approve/reject flow, fail-closed mock dispatch, idempotency and audit | Python, FastAPI, SQLite, pytest, Docker Compose, n8n export |

[**Engineering review, test evidence and remaining limitations**](docs/REVIEW_2026-10-21.md) · [**Market evidence and project choice**](docs/MARKET_EVIDENCE_2026-10.md)

### Recommended 5-minute code review

1. [Project 03 API](03-llm-quality-gate/app/main.py) and [tests](03-llm-quality-gate/tests/test_api.py) — deterministic gates *before* simulated business effects.
2. [Project 01 processor](01-rest-api-integration-hub/processor/app/main.py) — HMAC validation, sanitisation, run state and DLQ patterns.
3. [Project 02 LLM adapter](02-ai-workflow-automation-engine/app/services/llm_service.py) — mock/model boundary, extraction and routing.

## Architecture: separation of concerns

```text
01  Signed intake -> validation -> mock CRM -> audit / DLQ / KPI
02  Operational text -> extraction -> routing -> mock actions / KPI
03  Structured model output -> gate -> allow OR human review -> mock dispatch
```

These modules are **standalone**, not a single distributed production pipeline. The Project 03 schema deliberately matches fields used by Project 02, but wiring them together is not claimed.

## Local validation

Run each project's test suite independently (Python 3.12 recommended):

```bash
cd 01-rest-api-integration-hub
pip install -r processor/requirements.txt pytest
python -m pytest -q

cd ../02-ai-workflow-automation-engine
pip install -r requirements.txt
python -m pytest -q

cd ../03-llm-quality-gate
pip install -r requirements.txt
python -m pytest -q
```

GitHub Actions [portfolio tests](.github/workflows/ci.yml) runs each module plus JSON/Python/shell checks and Docker Compose **syntax validation** on push/PR. A passing unit suite or syntax check does not prove that a live n8n instance, Docker image or external integration ran.

For individual Docker demos, start from the project directory: copy `.env.example` to `.env`, replace secret placeholders, then run `docker compose up --build`. Projects 01/02 both use ports 5678 and 8000 and should not be started simultaneously without changing ports. Project 03 defaults to 5679 and 8030. See individual READMEs for prerequisites.

## Scope, safety and honesty

- **Real:** code, database and workflow definitions, unit tests, deterministic branch decisions and mock integrations.
- **Simulated:** CRM/Jira/Slack downstream calls, business dispatch and LLM outputs in default mock mode.
- **Not demonstrated:** real business KPIs/ROI, penetration testing, audited enterprise IAM, complete LLM security, model quality benchmarks or production rollout.
- **Important:** Project 01 n8n bridge requires a configured Header Auth credential before activation; Project 03 n8n nodes require the separately configured Header Auth credential. Never commit `.env` secrets.

License: [LICENSE](LICENSE).
