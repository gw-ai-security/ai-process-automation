CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  doc_id text PRIMARY KEY,
  title text NOT NULL,
  sha256 text NOT NULL,
  embedder text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS chunks (
  doc_id text NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  ordinal integer NOT NULL CHECK (ordinal >= 0),
  text text NOT NULL,
  embedding vector(256) NOT NULL,
  PRIMARY KEY (doc_id, ordinal)
);
CREATE TABLE IF NOT EXISTS query_metrics (
  id bigserial PRIMARY KEY,
  created_at timestamptz NOT NULL DEFAULT now(),
  answered boolean NOT NULL,
  source_count integer NOT NULL,
  latency_ms integer NOT NULL,
  mode text NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_doc_id_idx ON chunks(doc_id);
-- Exact vector search is intentional: the synthetic corpus is tiny.
-- An HNSW index would obscure fundamentals without an empirical benefit.
