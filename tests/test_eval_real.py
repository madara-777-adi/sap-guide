from scripts.eval_real import first_hit_rank, is_hit

RESULTS = [
    {"doc": "a.md", "page": 3},
    {"doc": "b.md", "page": 2},
    {"doc": "a.md", "page": 9},
]


def test_hit_needs_matching_doc_and_section():
    assert is_hit([["a.md", 3]], RESULTS, 1)
    assert not is_hit([["b.md", 3]], RESULTS, 3)  # right section number, wrong document
    assert is_hit([["a.md", 9]], RESULTS, 3)
    assert not is_hit([["a.md", 9]], RESULTS, 2)


def test_first_hit_rank():
    assert first_hit_rank([["a.md", 9]], RESULTS) == 3
    assert first_hit_rank([["b.md", 2]], RESULTS) == 2
    assert first_hit_rank([["c.md", 1]], RESULTS) is None