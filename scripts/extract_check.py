import sys

from pypdf import PdfReader

page = PdfReader(sys.argv[1]).pages[0]
for mode in ("plain", "layout"):
    text = page.extract_text(extraction_mode=mode)
    print(f"--- {mode}: {len(text)} chars ---")
    print(repr(text[:300]))