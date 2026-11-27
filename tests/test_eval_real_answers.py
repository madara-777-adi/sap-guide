from app.prompts import NOT_FOUND
from scripts.eval_real_answers import grade

Q = {"id": 1, "question": "How do I make a delivery from an STO?", "answerable": True,
     "expected": [["a.md", 3]], "keywords": ["VL10B"]}
GOOD = "Answer: Use VL10B.\n\nSource: a.md, page 3"


def test_good_answer_passes_all_checks():
    assert all(grade(Q, {"answer": GOOD, "sources": []}).values())


def test_wrong_refusal_is_caught():
    assert grade(Q, {"answer": NOT_FOUND, "sources": []}) == {"not_refused": False}


def test_missing_keyword_is_caught():
    answer = "Answer: Use the delivery screen.\n\nSource: a.md, page 3"
    assert grade(Q, {"answer": answer, "sources": []})["has_fact"] is False


def test_wrong_section_citation_is_caught():
    answer = "Answer: Use VL10B.\n\nSource: a.md, page 9"
    assert grade(Q, {"answer": answer, "sources": []})["cites_section"] is False


def test_unanswerable_must_refuse_exactly():
    q = {"id": 27, "question": "post goods issue?", "answerable": False, "expected": []}
    assert grade(q, {"answer": NOT_FOUND, "sources": []}) == {"correct_refusal": True}
    assert grade(q, {"answer": "Answer: click Post Goods Issue.", "sources": []}) == {"correct_refusal": False}


def test_keyword_matches_despite_look_alike_characters():
    q = {"id": 13, "question": "complete shipment?", "answerable": True,
         "expected": [["a.md", 8]], "keywords": ["Check-in"]}
    answer = "Answer: Click Check\u2011in.\n\nSource: a.md, page 8"
    assert grade(q, {"answer": answer, "sources": []})["has_fact"] is True
    q2 = {**q, "keywords": ["Ext ID"]}
    answer2 = "Answer: Enter Ext\u00a0ID 1.\n\nSource: a.md, page 8"
    assert grade(q2, {"answer": answer2, "sources": []})["has_fact"] is True