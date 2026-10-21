# 01 — REST API Integration Hub

**Business problem:** lead webhooks can be spoofed, duplicated or silently lost. This local demo validates HMAC-signed lead events, writes run/audit metadata, updates a mock CRM and stores failures in a DLQ.

**Stack:** FastAPI, PostgreSQL, Docker Compose, n8n export and HTTP mock services. No real CRM, Jira or Confluence credentials.

## Run

```bash
cp .env.example .env
# Replace the sample database password (also in DATABASE_URL),
# WEBHOOK_HMAC_SECRET, and EMAIL_HASH_SALT with local secret values.
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8000/health
bash scripts/smoke.sh
```

The smoke script sources local `.env`, calls the processor with valid/invalid signatures, stale timestamps, repeated idempotency keys and an invalid payload. This test suite requires Docker for real database and mock CRM behaviour.

**Important n8n setup:** Import `n8n/workflows/01_lead_intake_forward_to_processor.json`. Configure a **Header Auth** credential on its Webhook before activating. The bridge signs requests *after* authenticating the caller. n8n's Code node needs access to the built-in `crypto` module (Compose sets `NODE_FUNCTION_ALLOW_BUILTIN=crypto`). Confirm the n8n version/workflow import locally; this export has not been runtime-tested in the current review.

The primary standalone FastAPI endpoint is `POST /webhook/lead`, requiring `X-Timestamp`, `X-Signature` and `X-Idempotency-Key`. Signed request examples live in `scripts/`. The API's HMAC checks use the exact raw request bytes. **Timestamp freshness + idempotency are not equivalent to an independent persistent HMAC replay cache.**

## Verification and documentation

```bash
pip install -r processor/requirements.txt pytest
python -m pytest -q
```

Unit tests cover HMAC tampering, stale/missing signatures and audit field minimisation. The in-memory mock CRM retains payloads temporarily and is for synthetic leads only. Audit and DLQ metadata are minimized; arbitrary free-text input is no longer copied into those tables. Only a live Compose run can confirm the full API/database/orchestration path.

- [Technical docs and API contracts](docs/README.md)
- [Threat model](docs/threat_model.md)
- [Runbook](docs/03_setup_runbook.md)
- [Portfolio-wide review and residual risks](../docs/REVIEW_2026-10-21.md)

**Status:** implemented local code and tests; production readiness and live n8n compatibility not claimed.
