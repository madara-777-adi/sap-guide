from app.md_text import find_t_code, split_markdown

DOC = """# Process: Move stock, T-codes below

Intro line.

## Step 1: Create the order, T-code ME21N
1. Open ME21N.
2. Save.

## Step 2: Empty section

## Step 3: Pick the delivery
Press save.
"""


def test_sections_are_numbered_and_empty_ones_skipped():
    rows = split_markdown(DOC)
    assert [r[0] for r in rows] == [1, 2, 3]  # overview, step 1, step 3


def test_every_chunk_carries_title_and_heading():
    for _, _, content, _ in split_markdown(DOC):
        assert content.startswith("Process: Move stock")
    assert "Step 3: Pick the delivery" in split_markdown(DOC)[2][2]


def test_t_code_is_found_from_heading():
    rows = split_markdown(DOC)
    assert rows[1][3] == "ME21N"
    assert rows[2][3] is None


def test_find_t_code_ignores_plain_words():
    assert find_t_code("Open the screen") is None
    assert find_t_code("T-code: VL02N Module: MM") == "VL02N"


def test_long_section_is_split_and_keeps_heading():
    body = "\n".join(f"{i}. Do thing number {i} carefully." for i in range(80))
    rows = split_markdown(f"# T\n\n## Long\n{body}\n")
    assert len(rows) > 1
    assert all(r[2].startswith("T\nLong") for r in rows)