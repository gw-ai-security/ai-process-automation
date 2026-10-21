import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
import psycopg
import logging
from fastapi import FastAPI, Header, HTTPException, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Integration Hub Processor", version="0.2.0")


def get_db_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    return db_url


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def mask_email(email: str) -> str:
    if "@" not in email:
        return "****"
    local, domain = email.split("@", 1)
    prefix = local[:1] if local else ""
    return f"{prefix}***@{domain}"


def hash_email(email: str) -> str:
    salt = os.getenv("EMAIL_HASH_SALT", "")
    normalized = email.strip().lower()
    return hashlib.sha256(f"{normalized}{salt}".encode()).hexdigest()


def sanitize_payload(payload: Dict[str, Any], email_hash: Optional[str]) -> Dict[str, Any]:
    # Allowlist only: user-provided name, note and nested fields may contain PII.
    email = payload.get("email")
    return {"email_masked": mask_email(email) if isinstance(email, str) and email else None,
            "email_hash": email_hash}


def get_mock_crm_url() -> str:
    return os.getenv("MOCK_CRM_URL", "http://mock-crm:9001/leads/upsert")


def verify_signature(body_bytes: bytes, timestamp_header: Optional[str], signature_header: Optional[str]) -> None:
    secret = os.getenv("WEBHOOK_HMAC_SECRET")
    if not secret:
        raise RuntimeError("WEBHOOK_HMAC_SECRET is not configured")
    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=401, detail="Missing X-Timestamp or X-Signature header")

    try:
        timestamp = int(timestamp_header)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-Timestamp must be an integer")

    skew = int(os.getenv("WEBHOOK_MAX_SKEW_SECONDS", "300"))
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if abs(now_ts - timestamp) > skew:
        raise HTTPException(status_code=409, detail=f"Timestamp skew exceeds {skew} seconds")

    try:
        body_text = body_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Request body must be UTF-8 encoded")

    signing_string = f"{timestamp}.{body_text}"
    expected = "sha256=" + hmac.new(secret.encode(), signing_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")


async def send_to_mock_crm(payload: Dict[str, Any], run_id: uuid.UUID, source: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            get_mock_crm_url(),
            json={"run_id": str(run_id), "source": source, "payload": payload},
        )
        response.raise_for_status()
        return response.json()


@app.get("/health")
def health():
    payload = {"check": "health", "at": now_utc()}

    with psycopg.connect(get_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into audit_events (run_id, event_type, actor, payload)
                values (%s, %s, %s, %s::jsonb)
                """,
                (None, "health_check", "system", json.dumps(payload)),
            )

    return {"status": "ok"}


@app.post("/webhook/lead")
async def webhook_lead(
    request: Request,
    x_idempotency_key: Optional[str] = Header(default=None),
    x_source: Optional[str] = Header(default="unknown"),
    x_fail_after_accept: Optional[str] = Header(default=None),
    x_timestamp: Optional[str] = Header(default=None, alias="X-Timestamp"),
    x_signature: Optional[str] = Header(default=None, alias="X-Signature"),
):
    """
    Minimal intake endpoint:
    - requires X-Idempotency-Key
    - validates HMAC signature + timestamp skew
    - persists runs + audit + CRM
    - DLQ: on failure after accept (simulated via X-Fail-After-Accept: 1)
    """
    if not x_idempotency_key:
        raise HTTPException(status_code=400, detail="Missing X-Idempotency-Key header")

    body_bytes = await request.body()
    verify_signature(body_bytes, x_timestamp, x_signature)

    try:
        body = json.loads(body_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON payload")

    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Expected JSON object")
    email = body.get("email", "")
    if email and not isinstance(email, str):
        raise HTTPException(status_code=422, detail="Email must be a string")
    email_hash = hash_email(email) if email else None
    sanitized_body = sanitize_payload(body, email_hash)

    run_id = uuid.uuid4()
    safe_headers = {
        "x-idempotency-key": x_idempotency_key,
        "x-source": x_source,
        "x-fail-after-accept": x_fail_after_accept,
        "x-timestamp": x_timestamp,
        "x-signature": x_signature,
    }

    try:
        with psycopg.connect(get_db_url()) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "select run_id, status from runs where idempotency_key = %s",
                    (x_idempotency_key,),
                )
                existing = cur.fetchone()
                if existing:
                    existing_run_id, status = existing
                    return {
                        "status": "duplicate",
                        "run_id": str(existing_run_id),
                        "existing_status": status,
                    }

                cur.execute(
                    """
                    insert into runs (run_id, idempotency_key, source, status, email_hash, email_masked)
                    values (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        x_idempotency_key,
                        x_source,
                        "accepted",
                        email_hash,
                        sanitized_body.get("email_masked"),
                    ),
                )

                cur.execute(
                    """
                    insert into audit_events (run_id, event_type, actor, payload)
                    values (%s, %s, %s, %s::jsonb)
                    """,
                    (
                        run_id,
                        "lead_received",
                        "webhook",
                        json.dumps({"at": now_utc(), "source": x_source, "body": sanitized_body}),
                    ),
                )

        crm_result = await send_to_mock_crm(body, run_id, x_source)

        with psycopg.connect(get_db_url()) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into audit_events (run_id, event_type, actor, payload)
                    values (%s, %s, %s, %s::jsonb)
                    """,
                    (
                        run_id,
                        "crm_upserted",
                        "processor",
                        json.dumps({
                            "at": now_utc(),
                            "response": crm_result,
                        }),
                    ),
                )

        if x_fail_after_accept == "1":
            raise RuntimeError("forced_failure_after_accept")

        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("update runs set status = 'processed' where run_id = %s", (run_id,))
                cur.execute("""
                    insert into kpi_daily (day, received_count, processed_count)
                    values (current_date, 1, 1)
                    on conflict (day) do update set
                      received_count = kpi_daily.received_count + 1,
                      processed_count = kpi_daily.processed_count + 1
                """)
        return {"status": "processed", "run_id": str(run_id)}

    except Exception as e:
        logger.error("Processing failed: %s", type(e).__name__)
        try:
            with psycopg.connect(get_db_url()) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    dlq_payload = {
                        "at": now_utc(),
                        "headers": safe_headers,
                        "body": sanitized_body,
                    }

                    cur.execute(
                        """
                        insert into dlq (run_id, reason, payload, status)
                        values (%s, %s, %s::jsonb, %s)
                        """,
                        (run_id, str(e), json.dumps(dlq_payload), "open"),
                    )

                    cur.execute(
                        """
                        insert into audit_events (run_id, event_type, actor, payload)
                        values (%s, %s, %s, %s::jsonb)
                        """,
                        (
                            run_id,
                            "dlq_created",
                            "processor",
                            json.dumps({"at": now_utc(), "reason": str(e)}),
                        ),
                    )

                    cur.execute("update runs set status = 'failed' where run_id = %s", (run_id,))
                    cur.execute("""
                        insert into kpi_daily (day, received_count, failed_count)
                        values (current_date, 1, 1)
                        on conflict (day) do update set
                          received_count = kpi_daily.received_count + 1,
                          failed_count = kpi_daily.failed_count + 1
                    """)
        except Exception:
            pass

        raise HTTPException(status_code=500, detail="Processing failed; written to DLQ")
