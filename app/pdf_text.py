from pathlib import Path

from pypdf import PdfReader


def extract_pages(path: Path) -> list[tuple[int, str]]:
    """Return (page_number, text) for each page.

    Uses pypdf's "layout" mode. The default mode put every word on its own line
    for PDFs exported from Google Docs, which wrecked chunking.
    """
    reader = PdfReader(str(path))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text(extraction_mode="layout") or ""
        text = "\n".join(line.strip() for line in text.splitlines())
        pages.append((number, text))
    return pages