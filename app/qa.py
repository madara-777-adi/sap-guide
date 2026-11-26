from app.answer import generate_answer
from app.prompts import NOT_FOUND
from app.retrieve import search
from app.safety import add_safety_note

TOP_K = 3


def answer_question(question: str, search_fn=search, answer_fn=generate_answer) -> dict:
    chunks = search_fn(question, k=TOP_K)
    answer = add_safety_note(question, answer_fn(question, chunks))

    sources = []
    if answer.strip() != NOT_FOUND:
        seen = set()
        for chunk in chunks:
            key = (chunk["doc"], chunk["page"])
            if key not in seen:
                seen.add(key)
                sources.append({"doc": chunk["doc"], "page": chunk["page"]})
    return {"answer": answer, "sources": sources}