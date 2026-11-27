"""Run the eval questions through the real answer pipeline with ONE model, paced for Groq's limits.

    python -m scripts.eval_answers --provider groq-120b
    python -m scripts.eval_answers --provider groq-20b

Checks are cheap proxies. Read the saved answers yourself too.
"""
import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

from openai import RateLimitError

from app.answer import PROVIDERS, call_provider, generate_answer
from app.prompts import NOT_FOUND
from app.qa import answer_question
from app.safety import RISKY, SUPERVISOR_NOTE
from scripts.eval_retrieval import load_questions

# At least one of these words should appear in a correct answer. Keyed by question id,
# so they only make sense if eval/questions.jsonl still has the original ids.
MUST_INCLUDE_ANY = {
    1: ["MIRO"],
    2: ["goods receipt", "warehouse"],
    3: ["FB60"],
    4: ["approval slip"],
    5: ["approval slip", "Finance Supervisor"],
    6: ["ME21N"],
    7: ["Purchase Manager"],
    8: ["MIGO"],
    9: ["Warehouse Lead"],
    10: ["25th"],
    11: ["Finance Supervisor"],
}
PAGE_RE = re.compile(r"page\s*(\d+)", re.IGNORECASE)
RESULTS_DIR = Path("eval/results")


def grade(question: dict, result: dict) -> dict:
    answer = result["answer"]
    refused = answer.strip() == NOT_FOUND
    if not question["answerable"]:
        return {"correct_refusal": refused}

    lowered = answer.lower()
    keywords = MUST_INCLUDE_ANY.get(question["id"])
    pages = {int(n) for n in PAGE_RE.findall(answer)}
    checks = {
        "not_refused": not refused,
        "has_fact": None if keywords is None else any(k.lower() in lowered for k in keywords),
        "cites_page": bool(pages & set(question["expected_pages"])),
        "format_ok": lowered.lstrip().startswith("answer:") and "source:" in lowered,
    }
    if RISKY.search(question["question"]):
        checks["supervisor_note"] = SUPERVISOR_NOTE.lower() in lowered
    return checks


def make_complete(provider, max_retries: int = 2):
    """Call one specific model, waiting out rate limits instead of falling back."""

    def complete(messages: list[dict]) -> str:
        for attempt in range(max_retries + 1):
            try:
                return call_provider(provider, messages)
            except RateLimitError as exc:
                if attempt == max_retries:
                    raise
                try:
                    wait = float(exc.response.headers.get("retry-after", 30))
                except (TypeError, ValueError):
                    wait = 30.0
                print(f"   rate limited, waiting {min(wait, 90):.0f}s")
                time.sleep(min(wait, 90) + 1)

    return complete


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    parser.add_argument("--sleep", type=float, default=30.0, help="seconds between questions")
    args = parser.parse_args()

    questions = load_questions()
    complete = make_complete(PROVIDERS[args.provider])
    print(f"{len(questions)} questions, model {PROVIDERS[args.provider].model}, "
          f"{args.sleep:.0f}s between calls\n")

    rows, totals, errors = [], {}, 0
    for i, q in enumerate(questions):
        started = time.monotonic()
        try:
            result = answer_question(
                q["question"],
                answer_fn=lambda question, chunks: generate_answer(question, chunks, complete=complete),
            )
        except Exception as exc:  # noqa: BLE001 - record any failure and keep going
            result = {"answer": f"ERROR: {type(exc).__name__}", "sources": []}
            errors += 1
        seconds = time.monotonic() - started

        checks = grade(q, result)
        failed = [name for name, ok in checks.items() if ok is False]
        for name, ok in checks.items():
            if ok is None:
                continue
            totals.setdefault(name, [0, 0])
            totals[name][0] += bool(ok)
            totals[name][1] += 1

        status = "ok  " if not failed else "FAIL"
        print(f"#{q['id']:>2} {status} {seconds:4.1f}s  {q['question'][:48]}  {failed or ''}")
        rows.append({"id": q["id"], "question": q["question"], "seconds": round(seconds, 1),
                     "answer": result["answer"], "sources": result["sources"], "checks": checks})
        if i < len(questions) - 1:
            time.sleep(args.sleep)

    print("\nSummary")
    for name, (passed, total) in totals.items():
        print(f"  {name:16} {passed}/{total}")
    print(f"  errors           {errors}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{args.provider}_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    print(f"\nFull answers saved to {out}")


if __name__ == "__main__":
    main()