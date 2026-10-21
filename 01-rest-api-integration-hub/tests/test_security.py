import hashlib
import hmac
import importlib.util
import time
from pathlib import Path

import pytest
from fastapi import HTTPException

MODULE = Path(__file__).resolve().parents[1] / "processor/app/main.py"
spec = importlib.util.spec_from_file_location("processor_main", MODULE)
processor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processor)


def signed(body, timestamp, secret):
    return "sha256=" + hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()


def test_hmac_valid_and_tampered(monkeypatch):
    monkeypatch.setenv("WEBHOOK_HMAC_SECRET", "unit-test-secret")
    now = str(int(time.time()))
    body = b'{"email":"test@example.com"}'
    sig = signed(body, now, "unit-test-secret")
    processor.verify_signature(body, now, sig)
    with pytest.raises(HTTPException) as err:
        processor.verify_signature(body + b" ", now, sig)
    assert err.value.status_code == 401


def test_hmac_rejects_stale_and_missing(monkeypatch):
    monkeypatch.setenv("WEBHOOK_HMAC_SECRET", "unit-test-secret")
    old = str(int(time.time()) - 4000)
    with pytest.raises(HTTPException) as err:
        processor.verify_signature(b"{}", old, signed(b"{}", old, "unit-test-secret"))
    assert err.value.status_code == 409
    with pytest.raises(HTTPException) as err:
        processor.verify_signature(b"{}", None, None)
    assert err.value.status_code == 401


def test_audit_payload_is_minimal(monkeypatch):
    monkeypatch.setenv("EMAIL_HASH_SALT", "test-salt")
    raw = {"email": "alice@example.com", "note": "Personal phone 1234", "name": "Alice"}
    sanitized = processor.sanitize_payload(raw, processor.hash_email(raw["email"]))
    assert "alice@example.com" not in repr(sanitized)
    assert "Personal phone" not in repr(sanitized)
    assert "Alice" not in repr(sanitized)
    assert len(sanitized["email_hash"]) == 64
