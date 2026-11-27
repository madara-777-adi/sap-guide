"""Run the real-document questions through the real pipeline with ONE model, paced for Groq's limits.

    python -m scripts.eval_real_answers --provider groq-120b
    python -m scripts.eval_real_answers --provider groq-120b --ids 27,28,29

Checks are cheap proxies. Read the saved answers yourself too.
"""
import argparse
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from openai import APITimeoutError, RateLimitError

from app.answer import PROVIDERS, call_provider, generate_answer
from app.prompts import NOT_FOUND
from app.qa import answer_question
from app.safety import RISKY, SUPERVISOR_NOTE

QUESTIONS = Path("eval/real_questions.jsonl")
RESULTS_DIR = Path("eval/results")
PAGE_RE = re.compile(r"page\s*(\d+)", re.IGNORECASE)


def plain(text: str) -> str:
    """Lowercase, and normalise the look-alike spaces and hyphens models like to emit."""
    text = unicodedata.normalize("NFKC", text)
    for dash in "\u2010\u2011\u2012\u2013\u2014\u2212":
        text = text.replace(dash, "-")
    return text.replace("\u2019", "'").lower()


def grade(question: dict, result: dict) -> dict:
    answer = result["answer"]
    refused = answer.strip() == NOT_FOUND
    if not question["answerable"]:
        return {"correct_refusal": refused}
    if refused:
        return {"not_refused": False}

    lowered = plain(answer)
    keywords = question.get("keywords") or []
    expected_sections = {section for _, section in question["expected"]}
    cited = {int(n) for n in PAGE_RE.findall(answer)}
    checks = {
        "not_refused": True,
        "has_fact": any(plain(k) in lowered for k in keywords) if keywords else None,
        "cites_section": bool(cited & expected_sections),
        "format_ok": lowered.lstrip().startswith("answer:") and "source:" in lowered,
    }
    if RISKY.search(question["question"]):
        checks["supervisor_note"] = SUPERVISOR_NOTE.lower() in lowered
    return checks


def retry_wait(exc) -> float:
    """Seconds to wait before retrying a rate limit or a timeout."""
    if isinstance(exc, APITimeoutError):
        return 5.0
    try:
        return min(float(exc.response.headers.get("retry-after", 30)), 90.0)
    except (TypeError, ValueError, AttributeError):
        return 30.0


def make_complete(provider, max_retries: int = 2):
    """Call one specific model, waiting out rate limits and timeouts instead of falling back."""

    def complete(messages: list[dict]) -> str:
        for attempt in range(max_retries + 1):
            try:
                return call_provider(provider, messages)
            except (RateLimitError, APITimeoutError) as exc:
                if attempt == max_retries:
                    raise
                wait = retry_wait(exc)
                print(f"   {type(exc).__name__}, waiting {wait:.0f}s")
                time.sleep(wait + 1)

    return complete


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    parser.add_argument("--sleep", type=float, default=30.0, help="seconds between questions")
    parser.add_argument("--ids", default="", help="comma-separated question ids to run, e.g. 27,28")
    parser.add_argument("--file", type=Path, default=QUESTIONS)
    args = parser.parse_args()

    questions = [json.loads(line) for line in args.file.read_text().splitlines() if line.strip()]
    if args.ids:
        wanted = {int(i) for i in args.ids.split(",")}
        questions = [q for q in questions if q["id"] in wanted]

    provider = PROVIDERS[args.provider]
    complete = make_complete(provider)
    print(f"{len(questions)} questions, model {provider.model}, {args.sleep:.0f}s between calls\n")

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
    out = RESULTS_DIR / f"real_{args.provider}_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    print(f"\nFull answers saved to {out}")


if __name__ == "__main__":
    main()