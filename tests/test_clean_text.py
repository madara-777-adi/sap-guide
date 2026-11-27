from app.answer import clean_model_text, generate_answer
from app.prompts import NOT_FOUND

CHUNKS = [{"doc": "n.md", "page": 1, "content": "x"}]


def test_odd_spaces_and_hyphens_are_normalised():
    assert clean_model_text("Ext\u202fID\u202f1 and Check\u2011in") == "Ext ID 1 and Check-in"


def test_zero_width_space_is_removed():
    assert clean_model_text("Sa\u200bve") == "Save"


def test_normal_text_and_arrows_are_untouched():
    text = "Planning → Check-in – done"
    assert clean_model_text(text) == text


def test_refusal_with_odd_spaces_still_counts_as_refusal():
    odd = NOT_FOUND.replace(" ", "\u202f") + "\nSource: n.md, page 1"
    assert generate_answer("q", CHUNKS, complete=lambda m: odd) == NOT_FOUND