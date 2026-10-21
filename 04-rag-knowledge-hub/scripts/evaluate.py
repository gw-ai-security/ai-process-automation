"""Reproducible synthetic retrieval benchmark, not production model evaluation."""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = os.getenv("RAG_URL", "http://127.0.0.1:8040").rstrip("/")
KEY = os.getenv("RAG_API_KEY", "")
HEADERS = {"X-API-Key": KEY, "Content-Type": "application/json"}


def post(path, value):
    req = urllib.request.Request(API + path, data=json.dumps(value).encode(),
                                 headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def main():
    if len(KEY) < 16:
        sys.exit("Set RAG_API_KEY before running the benchmark.")
    dataset = json.loads((Path(__file__).resolve().parents[1] / "samples/runbooks.json").read_text())
    for doc in dataset:
        result = post("/documents", doc)
        print("Index:", doc["doc_id"], result["status"], result["chunks"])
    cases = [
        ("Who is notified for a critical incident?", "incident-response"),
        ("What happens after a failed deployment health check?", "release-rollback"),
        ("Who must approve an access request?", "access-request"),
        ("What is the melting temperature of titanium?", None),
    ]
    correct = 0
    for question, expected in cases:
        result = post("/ask", {"question": question, "top_k": 3, "min_score": 0.20})
        top = result["sources"][0]["source_id"].split(":")[0] if result["sources"] else None
        passed = (top == expected) and (result["status"] == ("abstained" if expected is None else "answered"))
        print("PASS" if passed else "FAIL", "|", question, "| top:", top, "| expected:", expected)
        correct += passed
    print(f"Synthetic suite: {correct}/{len(cases)} passed")
    return 0 if correct == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
