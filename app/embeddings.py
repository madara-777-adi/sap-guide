from functools import lru_cache

from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384  # must match vector(384) in db/schema.sql


@lru_cache
def get_model() -> TextEmbedding:
    return TextEmbedding(MODEL_NAME)  # loaded once, reused


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [vector.tolist() for vector in get_model().embed(texts)]


def to_vector_literal(vector: list[float]) -> str:
    """Format a vector as the text Postgres accepts for a pgvector column."""
    return "[" + ",".join(f"{x:.6f}" for x in vector) + "]"