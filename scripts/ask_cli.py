"""Ask one question from the terminal:  python -m scripts.ask_cli "How do I post an invoice?" """
import sys

from app.answer import generate_answer
from app.retrieve import search

question = " ".join(sys.argv[1:]).strip()
if not question:
    raise SystemExit('Usage: python -m scripts.ask_cli "your question"')

chunks = search(question, k=3)
print("Retrieved:", [(c["page"], round(c["similarity"], 3)) for c in chunks])
print()
print(generate_answer(question, chunks))