from app.prompts import NOT_FOUND
from scripts.eval_answers import grade

Q = {"id": 1, "question": "How do I post an invoice that has a PO?", "answerable": True, "expected_pages": [1]}
GOOD = "Answer: Use MIRO.\n\nSource: (notes.pdf, page 1)"


def test_good_answer_passes_all_checks():
    assert all(grade(Q, {"answer": GOOD, "sources": []}).values())


def test_wrong_refusal_is_caught():
    assert grade(Q, {"answer": NOT_FOUND, "sources": []})["not_refused"] is False


def test_wrong_page_citation_is_caught():
    answer = "Answer: Use MIRO.\n\nSource: (notes.pdf, page 4)"
    assert grade(Q, {"answer": answer, "sources": []})["cites_page"] is False


def test_unanswerable_must_refuse_exactly():
    q = {"id": 14, "question": "credit memo?", "answerable": False, "expected_pages": []}
    assert grade(q, {"answer": NOT_FOUND, "sources": []}) == {"correct_refusal": True}
    assert grade(q, {"answer": "Answer: use FB65.", "sources": []}) == {"correct_refusal": False}