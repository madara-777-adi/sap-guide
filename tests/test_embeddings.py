from pathlib import Path

from app.embeddings import EMBEDDING_DIM, to_vector_literal


def test_vector_literal_format():
    assert to_vector_literal([0.5, -1.0, 0.25]) == "[0.500000,-1.000000,0.250000]"


def test_embedding_dim_matches_schema_file():
    schema = (Path(__file__).parent.parent / "db" / "schema.sql").read_text()
    assert f"vector({EMBEDDING_DIM})" in schema