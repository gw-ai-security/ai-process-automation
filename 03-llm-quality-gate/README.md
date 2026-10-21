# 03 — LLM Output Quality Gate

**Business problem:** a classification/LLM workflow can generate bad instructions, sensitive output, or low-confidence routing. Sending every output directly to a ticketing or CRM API creates avoidable exception workload and risk.

**Solution:** a bounded, deterministic REST service evaluates **structured model output**, allows or flags it for review, and refuses a simulated business dispatch until the event is allowed or explicitly approved. It does not call an LLM: it evaluates the *output* of a preceding AI workflow.

| Control | Implementation | Evidence |
| --- | --- | --- |
| Input contract | Pydantic schema; strict fields and bounded text/action lengths | Invalid output → 422 |
| Rule gate | Selected email/token phrases, suspicious instructions, self-reported confidence threshold | Flag → `review` |
| Human oversight | Explicit `approve`/`reject` endpoint | Blocked dispatch → 409 until approval |
| Idempotency | Event ID + SHA-256 digest; SQLite transaction | Duplicate → same decision; conflicting ID → 409 |
| Audit & KPI | Metadata-only SQLite records, counters and review rate | `GET /metrics` |
| n8n orchestration | Importable Webhook → Evaluate → IF → Mock dispatch / review required | Exported JSON, credentials configured manually |

## Quickstart: Python (no Docker, no LLM credits)

Requires Python 3.12+. In a terminal from `03-llm-quality-gate/`:

```bash
python -m venv .venv
source .venv/bin/activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
export GATE_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export GATE_DB_PATH=./data/quality_gate.db
uvicorn app.main:app --host 127.0.0.1 --port 8030
```

PowerShell alternative to `export`:

```powershell
$env:GATE_API_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:GATE_DB_PATH = "./data/quality_gate.db"
```

In a second terminal, set the *same* `GATE_API_KEY`:

```bash
curl -s http://127.0.0.1:8030/health
curl -s -X POST http://127.0.0.1:8030/evaluate \
  -H "X-API-Key: $GATE_API_KEY" -H "Content-Type: application/json" \
  --data-binary @samples/allow.json
curl -s -X POST http://127.0.0.1:8030/dispatch/sample-allow-001 \
  -H "X-API-Key: $GATE_API_KEY"
curl -s http://127.0.0.1:8030/metrics -H "X-API-Key: $GATE_API_KEY"
```

Expected status: `allow` → `dispatched`; metrics: 1 evaluation, 1 mock dispatch. Dispatch **only writes a SQLite flag**. It never contacts actual Jira/Slack/CRM services.

For the human-review scenario change the sample's `event_id` to `sample-review-001` and `confidence` to `0.5`. Dispatch returns 409. Approve it with `POST /reviews/sample-review-001` and body `{"action":"approve"}`, then retry the dispatch. Rejection (`{"action":"reject"}`) permanently blocks it.

## Docker + n8n (optional)

```bash
cp .env.example .env
# Replace GATE_API_KEY=change-me with a random 32+ character value
docker compose up --build -d
```

API docs: http://127.0.0.1:8030/docs · n8n UI: http://127.0.0.1:5679

Import [quality-gate.json](n8n/workflows/quality-gate.json) into n8n. Create an **HTTP Header Auth** credential: name `X-API-Key`, value from `.env`. Assign that credential to **Evaluate quality** and **Mock dispatch**. The workflow remains inactive until configured. Send `samples/allow.json` to `POST /webhook/quality-gate` after activation, or to `/webhook-test/quality-gate` while listening in test mode.

## API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Public liveness; does not expose business records |
| POST | `/evaluate` | Evaluate strict AI output, hash metadata, return status |
| GET | `/decisions/{event_id}` | Metadata-only decision record |
| POST | `/reviews/{event_id}` | Approve or reject pending review |
| POST | `/dispatch/{event_id}` | Record *one* permitted mock action |
| GET | `/metrics` | Counts and review rate |

All endpoints except `/health` use `X-API-Key` (lab-level shared secret). Input matches fields from Project 02: `summary`, `action_items`, `priority`, `route_to`, `confidence`; caller additionally provides `event_id` and `prompt_version`. Project 02's optional `reasoning_short` is deliberately excluded. Runtime cross-project integration is not included.

## Tests and limitations

```bash
python -m pytest -q
```

**9 locally passed tests** cover auth, schema, event collisions, redaction, confidence, injection phrase checks, review state transitions, fail-closed/duplicate dispatch, metrics and n8n JSON structure. Docker startup and n8n *runtime* execution have not been locally validated by these tests.

Only selected email/key patterns and suspicious phrases are identified; this is **not** an exhaustive PII, prompt-injection or content-policy filter. Self-reported confidence is not a calibrated probability. Review uses a shared API key, not reviewer-specific RBAC. Raw inputs and model outputs are not written to the API's SQLite database, but n8n may retain execution input. Use synthetic data only. No reduction in actual incidents or ROI is claimed.

**Business KPI:** `review_rate = flagged_for_review / evaluations` (0 if no events). `mock_dispatched` counts database entries, not completed business actions. Accuracy and saved hours require external real-world measurement.

**Market motivation:** [VIG: ML & LLM Ops](https://group.vig/karriere/bewerben/stellenangebot/?handle=163) lists testing, guardrails, monitoring and human feedback. [hello again: (Junior) Revenue Automation Engineer](https://at.linkedin.com/jobs/view/junior-revenue-automation-engineer-d-w-m-at-hello-again-4416146084) lists n8n, Python, APIs, SQL and LLM workflows. This project implements a small, testable subset.
