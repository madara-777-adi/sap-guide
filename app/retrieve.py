from app.db import get_conn
from app.embeddings import embed_texts, to_vector_literal


def search(question: str, k: int = 5, query_prefix: str = "") -> list[dict]:
    """Return the k chunks closest in meaning to the question, best first.

    similarity = 1 - cosine distance, so 1.0 is identical and lower is less related.
    """
    vector = to_vector_literal(embed_texts([query_prefix + question])[0])
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT d.name, c.page, c.chunk_index, c.content,
                      1 - (c.embedding <=> %s::vector) AS similarity
               FROM chunks c
               JOIN documents d ON d.id = c.document_id
               ORDER BY c.embedding <=> %s::vector
               LIMIT %s""",
            (vector, vector, k),
        ).fetchall()
    return [
        {"doc": name, "page": page, "chunk": chunk, "content": content, "similarity": float(sim)}
        for name, page, chunk, content, sim in rows
    ]