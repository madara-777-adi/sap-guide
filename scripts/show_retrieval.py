"""Show what the search returns for a question: document, section, score, heading.

    python -m scripts.show_retrieval "How do I make a delivery from an STO?"
    python -m scripts.show_retrieval --prefix "How do I make a delivery from an STO?"
"""
import sys

from app.retrieve import search

BGE_PREFIX = "Represent this sentence for searching relevant passages: "

args = sys.argv[1:]
prefix = ""
if args and args[0] == "--prefix":
    prefix, args = BGE_PREFIX, args[1:]
question = " ".join(args).strip()
if not question:
    raise SystemExit('Usage: python -m scripts.show_retrieval [--prefix] "your question"')

for rank, r in enumerate(search(question, k=8, query_prefix=prefix), start=1):
    lines = r["content"].splitlines()
    heading = lines[1] if len(lines) > 1 else ""
    print(f"{rank}. {r['doc'][:3]} section {r['page']} chunk {r['chunk']}  {r['similarity']:.3f}  {heading[:70]}")