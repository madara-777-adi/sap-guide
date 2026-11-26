from pathlib import Path

from app.pdf_text import extract_pages

FIXTURE = Path(__file__).parent / "fixtures" / "acme_sap_notes.pdf"


def test_extracts_five_pages_with_expected_content():
    pages = dict(extract_pages(FIXTURE))
    assert len(pages) == 5
    assert "T-code: MIRO" in pages[1]
    assert "T-code: FB60" in pages[2]
    assert "Finance Supervisor" in pages[5]


def test_text_is_not_one_word_per_line():
    for page_no, text in extract_pages(FIXTURE):
        lines = [line for line in text.splitlines() if line.strip()]
        assert lines, f"page {page_no} is empty"
        average = sum(len(line) for line in lines) / len(lines)
        assert average > 15, f"page {page_no} looks like one word per line"