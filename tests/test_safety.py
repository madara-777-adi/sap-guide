from app.prompts import NOT_FOUND
from app.safety import SUPERVISOR_NOTE, add_safety_note


def test_reversal_question_gets_the_note():
    out = add_safety_note("Can I reverse a posted document?", "Answer: only after approval.")
    assert out.endswith(SUPERVISOR_NOTE)


def test_note_added_when_only_the_answer_is_risky():
    out = add_safety_note("What should I do?", "Answer: cancel the order first.")
    assert SUPERVISOR_NOTE in out


def test_note_is_not_duplicated():
    answer = f"Answer: no.\n{SUPERVISOR_NOTE}"
    assert add_safety_note("reverse?", answer).count(SUPERVISOR_NOTE) == 1


def test_not_found_is_left_alone():
    assert add_safety_note("How do I delete a vendor?", NOT_FOUND) == NOT_FOUND


def test_harmless_answer_is_left_alone():
    answer = "Answer: Use MIRO."
    assert add_safety_note("How do I post an invoice?", answer) == answer