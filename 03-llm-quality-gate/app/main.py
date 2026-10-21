"""Deterministic pre-dispatch gate for AI-generated operational summaries.

No input text or model output is persisted; only digest, status and reason codes.
This is a demo policy gate, not a comprehensive AI safety or DLP solution.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="LLM Output Quality Gate", version="1.0.0")

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
SECRET = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|(?:api[_-]?key|bearer token)\s*[:=]\s*\S{8,})", re.I)
INJECTION = re.compile(r"\b(?:ignore (?:all )?(?:previous|prior) instructions|reveal (?:the )?system prompt|send (?:all )?(?:secrets|credentials))\b", re.I)


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_key(x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None) -> None:
    configured = os.getenv("GATE_API_KEY", "")
    if len(configured) < 16:
        raise HTTPException(503, "Server API key is not configured")
    if not x_api_key or not hmac.compare_digest(x_api_key, configured):
        raise HTTPException(401, "Unauthorized")


@contextmanager
def database():
    path = Path(os.getenv("GATE_DB_PATH", "/data/quality_gate.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=10000")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS decisions (
              event_id TEXT PRIMARY KEY,
              prompt_version TEXT NOT NULL,
              output_sha256 TEXT NOT NULL,
              initial_decision TEXT NOT NULL,
              status TEXT NOT NULL,
              reasons TEXT NOT NULL,
              created_at TEXT NOT NULL,
              dispatched_at TEXT
            );
            CREATE TABLE IF NOT EXISTS audit (
              audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
              event_id TEXT NOT NULL,
              operation TEXT NOT NULL,
              occurred_at TEXT NOT NULL
            );
        """)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class ModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    summary: str = Field(min_length=10, max_length=2000)
    action_items: list[Annotated[str, Field(min_length=1, max_length=250)]] = Field(min_length=1, max_length=5)
    priority: Literal["low", "medium", "high"]
    route_to: Literal["sales", "ops", "support", "product"]
    confidence: float = Field(ge=0, le=1)


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    event_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
    prompt_version: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$")
    output: ModelOutput


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["approve", "reject"]


def decide(output: ModelOutput) -> tuple[str, list[str]]:
    threshold = float(os.getenv("GATE_MIN_CONFIDENCE", "0.8"))
    if not 0 <= threshold <= 1:
        raise HTTPException(503, "Invalid confidence threshold")
    text = "\n".join([output.summary, *output.action_items])
    reasons = []
    if EMAIL.search(text) or SECRET.search(text):
        reasons.append("potential_sensitive_data")
    if INJECTION.search(text):
        reasons.append("suspicious_instruction")
    if output.confidence < threshold:
        reasons.append("low_self_reported_confidence")
    return ("review" if reasons else "allow"), reasons


def view(row: sqlite3.Row) -> dict:
    return {
        "event_id": row["event_id"],
        "prompt_version": row["prompt_version"],
        "decision": row["initial_decision"],
        "status": row["status"],
        "reasons": json.loads(row["reasons"]),
        "dispatched": row["dispatched_at"] is not None,
    }


@app.get("/health")
def health():
    with database() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"status": "ok"}


@app.post("/evaluate", dependencies=[Depends(require_key)])
def evaluate(request: EvaluateRequest):
    serialized = json.dumps(request.output.model_dump(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    decision, reasons = decide(request.output)
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute("SELECT * FROM decisions WHERE event_id=?", (request.event_id,)).fetchone()
        if existing:
            if existing["output_sha256"] != digest or existing["prompt_version"] != request.prompt_version:
                raise HTTPException(409, "Event ID already used for different output")
            return view(existing)
        conn.execute(
            "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
            (request.event_id, request.prompt_version, digest, decision, decision, json.dumps(reasons), timestamp()),
        )
        conn.execute("INSERT INTO audit (event_id, operation, occurred_at) VALUES (?, ?, ?)",
                     (request.event_id, "evaluated", timestamp()))
        return view(conn.execute("SELECT * FROM decisions WHERE event_id=?", (request.event_id,)).fetchone())


@app.get("/decisions/{event_id}", dependencies=[Depends(require_key)])
def get_decision(event_id: str):
    with database() as conn:
        row = conn.execute("SELECT * FROM decisions WHERE event_id=?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Event not found")
        return view(row)


@app.post("/reviews/{event_id}", dependencies=[Depends(require_key)])
def review(event_id: str, body: ReviewRequest):
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM decisions WHERE event_id=?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Event not found")
        if row["status"] != "review":
            raise HTTPException(409, "Event is not awaiting review")
        new_status = "approved" if body.action == "approve" else "rejected"
        conn.execute("UPDATE decisions SET status=? WHERE event_id=?", (new_status, event_id))
        conn.execute("INSERT INTO audit (event_id, operation, occurred_at) VALUES (?, ?, ?)",
                     (event_id, new_status, timestamp()))
        return view(conn.execute("SELECT * FROM decisions WHERE event_id=?", (event_id,)).fetchone())


@app.post("/dispatch/{event_id}", dependencies=[Depends(require_key)])
def mock_dispatch(event_id: str):
    """Only records that the mock action would be performed; no external API call."""
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM decisions WHERE event_id=?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Event not found")
        if row["status"] not in ("allow", "approved"):
            raise HTTPException(409, "Dispatch blocked pending approval or rejected")
        if row["dispatched_at"]:
            return {"event_id": event_id, "status": "duplicate", "target": "mock-only"}
        conn.execute("UPDATE decisions SET dispatched_at=? WHERE event_id=?", (timestamp(), event_id))
        conn.execute("INSERT INTO audit (event_id, operation, occurred_at) VALUES (?, ?, ?)",
                     (event_id, "mock_dispatched", timestamp()))
        return {"event_id": event_id, "status": "dispatched", "target": "mock-only"}


@app.get("/metrics", dependencies=[Depends(require_key)])
def metrics():
    with database() as conn:
        total = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        review_count = conn.execute("SELECT COUNT(*) FROM decisions WHERE initial_decision='review'").fetchone()[0]
        dispatched = conn.execute("SELECT COUNT(*) FROM decisions WHERE dispatched_at IS NOT NULL").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM decisions WHERE status='rejected'").fetchone()[0]
        waiting = conn.execute("SELECT COUNT(*) FROM decisions WHERE status='review'").fetchone()[0]
        return {
            "evaluations": total,
            "flagged_for_review": review_count,
            "pending_review": waiting,
            "rejected": rejected,
            "mock_dispatched": dispatched,
            "review_rate": round(review_count / total, 4) if total else 0.0,
        }
