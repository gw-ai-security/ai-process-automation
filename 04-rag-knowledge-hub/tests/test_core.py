import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RAG_API_KEY", "a-long-test-api-key-not-production")
    monkeypatch.setenv("EMBEDDING_MODE", "hash")
    monkeypatch.setenv("ANSWER_MODE", "extractive")
    return TestClient(main.app)


def headers():
    return {"X-API-Key": "a-long-test-api-key-not-production"}


def example_document():
    return {"doc_id": "runbook-001", "title": "Sample Runbook", "text":
            "Critical incident escalation must notify the on-call engineer immediately."}


def test_chunking_coverage_and_overlap():
    text = " ".join(f"word{i}" for i in range(20))
    chunks = main.chunk_text(text, max_words=8, overlap=2)
    assert len(chunks) == 3
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]
    assert chunks[-1].split()[-1] == "word19"
    with pytest.raises(ValueError):
        main.chunk_text(text, 8, 8)


def test_hash_vectors_are_stable_normalized_and_lexical():
    a = main.hash_embedding("incident incident escalation on call")
    b = main.hash_embedding("incident incident escalation on call")
    c = main.hash_embedding("deployment release rollback")
    assert a == b
    assert len(a) == main.DIMENSIONS
    assert abs(math.sqrt(sum(v * v for v in a)) - 1) < 1e-9
    assert sum(x * y for x, y in zip(a, b)) > sum(x * y for x, y in zip(a, c))
    assert main.hash_embedding("the and an") == [0.0] * main.DIMENSIONS


def test_schema_auth_and_key_configuration(client, monkeypatch):
    assert client.post("/documents", json=example_document()).status_code == 401
    invalid = example_document()
    invalid["extra_field"] = "not permitted"
    assert client.post("/documents", json=invalid, headers=headers()).status_code == 422
    monkeypatch.setenv("RAG_API_KEY", "short")
    assert client.post("/documents", json=example_document(), headers=headers()).status_code == 503


def test_ingest_and_question_schema(client, monkeypatch):
    monkeypatch.setattr(main, "save_document", lambda d: {"doc_id": d.doc_id, "status": "indexed", "chunks": 1})
    result = client.post("/documents", json=example_document(), headers=headers())
    assert result.status_code == 200 and result.json()["chunks"] == 1
    assert client.post("/ask", json={"question": "What happens?", "top_k": 8}, headers=headers()).status_code == 422


def test_ask_abstains_when_no_evidence(client, monkeypatch):
    captured = []
    monkeypatch.setattr(main, "retrieve", lambda *args: [])
    monkeypatch.setattr(main, "record_query", lambda *args: captured.append(args))
    data = client.post("/ask", json={"question": "unknown detail"}, headers=headers()).json()
    assert data["status"] == "abstained" and data["sources"] == []
    assert captured[0][0] is False


def test_ask_only_returns_sources_above_threshold(client, monkeypatch):
    source = {"source_id": "abc:0", "title": "Runbook",
              "excerpt": "Notify the on-call engineer.", "score": 0.8}
    low = dict(source, source_id="other:0", score=0.12)
    monkeypatch.setattr(main, "retrieve", lambda *args: [source, low])
    monkeypatch.setattr(main, "record_query", lambda *args: None)
    data = client.post("/ask", json={"question": "Who is notified?"}, headers=headers()).json()
    assert data["status"] == "answered" and len(data["sources"]) == 1
    assert data["answer_mode"] == "extractive"
    assert "[abc:0]" in data["answer"]


def test_sql_vector_validation():
    assert main.sql_vector([0.0] * main.DIMENSIONS).startswith("[")
    with pytest.raises(ValueError):
        main.sql_vector([0.0] * 3)
    with pytest.raises(ValueError):
        main.sql_vector([float("nan")] * main.DIMENSIONS)


def test_embedding_backend_modes_and_errors(monkeypatch):
    monkeypatch.setenv("EMBEDDING_MODE", "openai")
    monkeypatch.setenv("LLM_API_KEY", "fake-test-key")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    def fake_post(url, **kwargs):
        assert url.endswith("/embeddings")
        assert kwargs["json"]["dimensions"] == main.DIMENSIONS
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"data": [{"embedding": [0.5] * main.DIMENSIONS}]})
    monkeypatch.setattr(main.httpx, "post", fake_post)
    assert main.embed("test") == [0.5] * main.DIMENSIONS
    monkeypatch.setattr(main.httpx, "post", lambda *args, **kwargs: SimpleNamespace(
        raise_for_status=lambda: None, json=lambda: {"data": [{"embedding": [0.4]}]}))
    with pytest.raises(main.HTTPException) as error:
        main.embed("test")
    assert error.value.status_code == 502
    monkeypatch.setenv("EMBEDDING_MODE", "unknown")
    with pytest.raises(main.HTTPException):
        main.embedding_signature()


def test_hosted_answer_is_explicitly_optional(monkeypatch):
    monkeypatch.setenv("ANSWER_MODE", "openai")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(main.HTTPException) as e:
        main.render_answer("Question?", [{"source_id": "d:0", "excerpt": "Answer"}])
    assert e.value.status_code == 503


def test_workflow_json_contract():
    base = Path(__file__).resolve().parents[1] / "n8n/workflows"
    for filename in ["rag-ask.json", "rag-ingest.json"]:
        flow = json.loads((base / filename).read_text())
        names = {node["name"] for node in flow["nodes"]}
        assert {"Webhook", "Call knowledge API", "Respond"} <= names
        assert flow["active"] is False
        assert next(node for node in flow["nodes"] if node["name"] == "Webhook")["parameters"]["authentication"] == "headerAuth"
        assert all(node.get("parameters", {}).get("authentication") == "genericCredentialType"
                   for node in flow["nodes"] if node["name"] == "Call knowledge API")
