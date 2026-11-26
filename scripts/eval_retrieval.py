"""Score retrieval against eval/questions.jsonl. No LLM involved.

    python -m scripts.eval_retrieval
"""
import json
from pathlib import Path

from app.retrieve import search

QUESTIONS = Path("eval/questions.jsonl")
# Instruction the BGE authors recommend putting in front of short search queries.
# We don't just trust it: the script scores with and without.
BGE_PREFIX = "Represent this sentence for searching relevant passages: "


def load_questions() -> list[dict]:
    lines = QUESTIONS.read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def run(questions: list[dict], prefix: str, label: str) -> None:
    hit1 = hit3 = answerable = 0
    top_answerable: list[float] = []
    top_unanswerable: list[float] = []
    misses = []

    for q in questions:
        results = search(q["question"], k=5, query_prefix=prefix)
        pages = [r["page"] for r in results]
        top = results[0]["similarity"] if results else 0.0
        print(f"  #{q['id']:>2} {'answerable  ' if q['answerable'] else 'UNANSWERABLE'} top={top:.3f} page={results[0]['page'] if results else '-'}  {q['question'][:50]}")

        if not q["answerable"]:
            top_unanswerable.append(top)
            continue

        answerable += 1
        top_answerable.append(top)
        expected = set(q["expected_pages"])
        hit1 += bool(expected & set(pages[:1]))
        hit3 += bool(expected & set(pages[:3]))
        if not expected & set(pages[:1]):
            misses.append((q["id"], q["question"], sorted(expected), pages[:3]))

    print(f"\n=== {label} ===")
    print(f"Answerable questions: {answerable}")
    print(f"Right page ranked first:    {hit1}/{answerable}")
    print(f"Right page in top 3:        {hit3}/{answerable}")
    print(f"Top similarity, answerable:   min {min(top_answerable):.3f}  avg {sum(top_answerable)/len(top_answerable):.3f}")
    if top_unanswerable:
        print(f"Top similarity, unanswerable: max {max(top_unanswerable):.3f}  avg {sum(top_unanswerable)/len(top_unanswerable):.3f}")
    for qid, text, expected, got in misses:
        print(f"  MISS #{qid}: {text!r} expected {expected}, got {got}")


def main() -> None:
    questions = load_questions()
    run(questions, prefix="", label="no prefix")
    run(questions, prefix=BGE_PREFIX, label="with BGE query prefix")


if __name__ == "__main__":
    main()