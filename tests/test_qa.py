from app.prompts import NOT_FOUND
from app.qa import answer_question
from app.safety import SUPERVISOR_NOTE

CHUNKS = [
    {"doc": "n.pdf", "page": 5, "content": "x", "similarity": 0.7},
    {"doc": "n.pdf", "page": 5, "content": "y", "similarity": 0.6},
    {"doc": "n.pdf", "page": 1, "content": "z", "similarity": 0.5},
]


def fake_search(question, k):
    return CHUNKS


def test_sources_are_unique_pages_in_rank_order():
    result = answer_question("q", search_fn=fake_search, answer_fn=lambda q, c: "Answer: ok")
    assert result["sources"] == [{"doc": "n.pdf", "page": 5}, {"doc": "n.pdf", "page": 1}]


def test_not_found_has_no_sources():
    result = answer_question("credit memo?", search_fn=fake_search, answer_fn=lambda q, c: NOT_FOUND)
    assert result == {"answer": NOT_FOUND, "sources": []}


def test_reversal_gets_supervisor_note_even_if_model_forgot():
    result = answer_question("Can I reverse it?", search_fn=fake_search, answer_fn=lambda q, c: "Answer: no.")
    assert SUPERVISOR_NOTE in result["answer"]


def test_search_is_asked_for_three_chunks():
    seen = {}

    def spy(question, k):
        seen["k"] = k
        return CHUNKS

    answer_question("q", search_fn=spy, answer_fn=lambda q, c: "ok")
    assert seen["k"] == 3