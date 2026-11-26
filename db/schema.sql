CREATE TABLE documents (
  id              SERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  content_hash    TEXT NOT NULL UNIQUE,
  module          TEXT,
  source_type     TEXT NOT NULL
                  CHECK (source_type IN ('sop', 'own_note', 'manual', 'public_doc', 'sample')),
  embedding_model TEXT NOT NULL,
  page_count      INT,
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
  id           SERIAL PRIMARY KEY,
  document_id  INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page         INT NOT NULL,
  chunk_index  INT NOT NULL,
  t_code       TEXT,
  content      TEXT NOT NULL,
  embedding    vector(384) NOT NULL,
  UNIQUE (document_id, page, chunk_index)
);

CREATE INDEX chunks_document_idx ON chunks (document_id);