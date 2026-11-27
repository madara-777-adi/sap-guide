"""Show what the search returns for a question: document, section, score, heading.

    python -m scripts.show_retrieval "How do I make a delivery from an STO?"
"""
import sys

from app.retrieve import search

question = " ".join(sys.argv[1:]).strip()
if not question:
    raise SystemExit('Usage: python -m scripts.show_retrieval "your question"')

for rank, r in enumerate(search(question, k=8), start=1):
    lines = r["content"].splitlines()
    heading = lines[1] if len(lines) > 1 else ""
    print(f"{rank}. {r['doc'][:3]} section {r['page']} chunk {r['chunk']}  {r['similarity']:.3f}  {heading[:70]}")