from app.answer import generate_answer, normalize_refusal
from app.prompts import NOT_FOUND

CHUNKS = [{"doc": "n.md", "page": 1, "content": "x"}]


def test_refusal_with_extra_source_line_is_cleaned():
    assert normalize_refusal(NOT_FOUND + "  \nSource: n.md, page 4") == NOT_FOUND


def test_curly_apostrophe_refusal_is_cleaned():
    assert normalize_refusal(NOT_FOUND.replace("'", "\u2019")) == NOT_FOUND


def test_real_answer_is_untouched():
    assert normalize_refusal("Answer: Use ME21N.") == "Answer: Use ME21N."


def test_generate_answer_returns_clean_refusal():
    out = generate_answer("q", CHUNKS, complete=lambda m: NOT_FOUND + "\nSource: n.md, page 1")
    assert out == NOT_FOUND