"""Score retrieval on the real documents, with and without the BGE query prefix. No LLM involved.

    python -m scripts.eval_real eval/real_questions.jsonl
"""
import json
import sys
from pathlib import Path

from app.retrieve import search

BGE_PREFIX = "Represent this sentence for searching relevant passages: "
K = 8


def is_hit(expected: list[list], results: list[dict], n: int) -> bool:
    wanted = {(doc, section) for doc, section in expected}
    return any((r["doc"], r["page"]) in wanted for r in results[:n])


def first_hit_rank(expected: list[list], results: list[dict]) -> int | None:
    wanted = {(doc, section) for doc, section in expected}
    for rank, r in enumerate(results, start=1):
        if (r["doc"], r["page"]) in wanted:
            return rank
    return None


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "eval/real_questions.jsonl")
    questions = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    answerable = [q for q in questions if q["answerable"]]
    modes = {"plain": "", "prefix": BGE_PREFIX}

    ranks: dict[str, list[int | None]] = {name: [] for name in modes}
    for q in answerable:
        shown = []
        for name, prefix in modes.items():
            rank = first_hit_rank(q["expected"], search(q["question"], k=K, query_prefix=prefix))
            ranks[name].append(rank)
            shown.append(f"{name}={rank if rank else '-'}")
        print(f"#{q['id']:>2} {'  '.join(shown):<22} {q['question'][:52]}")

    total = len(answerable)
    print(f"\nRank of the first correct chunk, {total} answerable questions (rank counts chunks)")
    for name, values in ranks.items():
        within = {n: sum(1 for r in values if r is not None and r <= n) for n in (1, 3, 5)}
        missing = sum(1 for r in values if r is None)
        print(f"  {name:7} top1 {within[1]}/{total}   top3 {within[3]}/{total}   "
              f"top5 {within[5]}/{total}   not in top {K}: {missing}")


if __name__ == "__main__":
    main()