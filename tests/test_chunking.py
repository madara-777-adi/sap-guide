import pytest

from app.chunking import chunk_text


def test_empty_text_gives_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_text_is_one_chunk():
    assert chunk_text("Post the invoice in MIRO.") == ["Post the invoice in MIRO."]


def test_chunks_never_exceed_size():
    text = " ".join(f"word{i}" for i in range(500))
    assert all(len(c) <= 200 for c in chunk_text(text, size=200, overlap=30))


def test_consecutive_chunks_overlap():
    text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(text, size=200, overlap=50)
    assert len(chunks) > 2
    assert chunks[1][:20] in chunks[0]


def test_no_word_is_lost():
    words = [f"word{i}" for i in range(300)]
    chunks = chunk_text(" ".join(words), size=150, overlap=30)
    assert set(words) <= set(" ".join(chunks).split())


def test_tiny_sizes_still_terminate():
    assert chunk_text("a b " * 50, size=10, overlap=9)


def test_bad_parameters_are_rejected():
    with pytest.raises(ValueError):
        chunk_text("text", size=100, overlap=100)
    with pytest.raises(ValueError):
        chunk_text("text", size=0, overlap=0)
def test_chunks_start_at_word_boundaries():
    words = [f"word{i}" for i in range(300)]
    chunks = chunk_text(" ".join(words), size=150, overlap=40)
    word_set = set(words)
    assert all(c.split()[0] in word_set for c in chunks)