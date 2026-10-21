# 04 — Evidence-First RAG Knowledge Hub

**Business problem:** operational staff spend time searching runbooks and technical documentation. A response without a traceable source can be as harmful as no response.

**Solution:** index synthetic operational documents, split them into chunks, compute vectors, retrieve ranked evidence from PostgreSQL/pgvector and return an explicit source citation or abstain when retrieval is too weak.

The core value is a reproducible *retrieval engineering* demonstration. This is not a general production document assistant.

## Recruiter snapshot

| Skill signal | Evidence |
| --- | --- |
| Ingestion and data engineering | `POST /documents`, fixed-size overlapping chunker, SHA-256 change tracking and reindexing |
| Embedding interfaces | Local deterministic 256-d lexical hash baseline, optional OpenAI-compatible 256-d semantic embedding endpoint |
| Vector database and SQL | PostgreSQL, pgvector `vector(256)`, cosine distance operator `<=>`, transaction-safe replacement |
| Retrieval & grounding | `POST /ask`, similarity threshold, ranked source IDs, explicit insufficient-evidence result |
| Measurable evaluation | Synthetic 4-case benchmark with expected document IDs and required abstention |
| Automation & QA | Two n8n workflow JSON exports, pytest and Docker/CI smoke |

## Architecture

```text
Document JSON -> FastAPI -> word chunking -> embedding adapter -> PostgreSQL/pgvector
Question JSON -> FastAPI -> same embedding adapter -> ranked pgvector retrieval
                                                    -> threshold?
                                                  /               \
                                              evidence           weak/no match
                                                 |                    |
                                    extractive cited quote          abstain
                                                 |
                                    optional hosted LLM answer
```

**Important terminology:** `EMBEDDING_MODE=hash` uses token hashing, a **lexical**, deterministic baseline, not learned semantic representations. A synonym query may fail; hash collisions may create spurious matches. `EMBEDDING_MODE=openai` calls an external OpenAI-compatible embeddings endpoint. It is implemented behind an adapter but no paid-provider availability, cost or accuracy is assumed. `ANSWER_MODE=extractive` quotes the strongest retrieved chunk, not an LLM-generated synthesis. `ANSWER_MODE=openai` optionally produces a generated answer from retrieved excerpts; citations then show supplied context, *not independent proof of factuality*. The modes are deliberately isolated for a small demo.

## Run with Docker

Requirements: Docker Desktop / Docker Engine + Compose.

```bash
cd 04-rag-knowledge-hub
cp .env.example .env
# Replace POSTGRES_PASSWORD (also in DATABASE_URL) and RAG_API_KEY.
docker compose up -d --build db api n8n
curl http://127.0.0.1:8040/health
```

Set `RAG_API_KEY` in the shell to the same secret as in `.env` (PowerShell: `$env:RAG_API_KEY = "..."`). Execute the synthetic benchmark from this directory:

```bash
python scripts/evaluate.py
```

Expected: three questions return a corresponding source runbook; one unrelated question returns `abstained`. The benchmark **only measures four synthetic cases**, not overall retrieval precision or business ROI. Repeat ingestion returns `unchanged` for an unchanged document and does not duplicate chunks.

### API routes

| Route | Purpose |
| --- | --- |
| `GET /health` | PostgreSQL readiness |
| `POST /documents` | Index one document or atomically replace its chunks |
| `POST /ask` | Retrieve relevant chunks and return grounded evidence or abstain |
| `GET /metrics` | Documents, chunks, answer counts and observed average latency |

All routes except `/health` use `X-API-Key`. Example:

```bash
curl -X POST http://127.0.0.1:8040/ask \
  -H "X-API-Key: $RAG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Who must approve an access request?","top_k":3,"min_score":0.2}'
```

The reply includes `status`, `answer`, `sources` (`source_id`, `title`, `excerpt`, `score`) and `answer_mode`. A source ID such as `access-request:0` resolves to document ID plus chunk ordinal. Ranking scores are cosine similarities, **not calibrated confidence probabilities**.

## n8n demonstration

n8n UI: http://127.0.0.1:5680. Import both workflows in `n8n/workflows/`:
- `rag-ingest.json` — webhook `knowledge-ingest` → API `/documents`.
- `rag-ask.json` — webhook `knowledge-ask` → API `/ask`.

On each incoming **Webhook** node, configure **Header Auth** with a separate inbound secret before activation. On the HTTP Request node of **each** workflow, create and assign an **HTTP Header Auth** credential with header name `X-API-Key` and your secret value. The imports are intentionally inactive. Activate only in the local demo after credentials are assigned. n8n also stores execution input in its own database by default; do not send private data.

## Tests

```bash
pip install -r requirements.txt
python -m pytest -q
docker compose config -q
```

In CI, unit tests cover chunking, lexical vector behavior, Pydantic contracts, auth, evidence filtering, abstention, hosted-API adapter mocks, and workflow JSON contracts. A separate Docker smoke test validates real Postgres/pgvector ingestion, retrieval, reindex idempotency, benchmarks, and n8n workflow import.

## Security, engineering limitations and next steps

- **Synthetic documents only.** Raw document text and chunks are stored in PostgreSQL without encryption-at-rest controls in this demo. Avoid personal records, commercial secrets or confidential runbooks.
- Shared API key is lab authentication; no per-user permissions, tenant isolation, file parsing, source ACL checks, delete endpoint, retention policy or document authenticity guarantees.
- Embedding-provider requests transmit text to that provider; understand processing and data-residency requirements before enabling hosted mode.
- The query audit captures only counts and latency, never raw query text. SQL parameters are bound, and ingestion is transactional.
- Hashing + cosine is **not semantic search**. Stopwords, synonyms, multilingual content and out-of-vocabulary queries can cause failed matches. No calibrated confidence, trained reranker, or large-scale latency benchmark.
- The default extractive answer cannot invent unseen content but can still be irrelevant or incomplete. An optional LLM response may hallucinate even when citations are supplied.
- Small data: exact vector nearest-neighbor search; no ANN/HNSW index is needed at this scale. Version-tagged embeddings prevent cross-model comparisons.
- No real n8n webhook end-to-end run is claimed solely from successful CLI import.

**Reason for inclusion:** public Austrian AI engineering adverts explicitly mention chunking, embeddings, vector databases, RAG, citation handling, and automated evaluation. See [market evidence](../docs/MARKET_EVIDENCE_2026-10.md). Previous Projects 01–03 cover integrations, intelligent workflow handling and quality gates; this module isolates knowledge retrieval.
