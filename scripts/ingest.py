"""Ingest one PDF or Markdown file: split, embed, store in Neon.

Dry run (no embedding, no database), to inspect what would be stored:
    python -m scripts.ingest docs/file.md --source-type sop --dry-run
Real run:
    python -m scripts.ingest docs/file.md --source-type sop --module MM
For Markdown files, "page" in the database means the section number.
"""
import argparse
import hashlib
from pathlib import Path

from app.chunking import chunk_text
from app.db import get_conn
from app.embeddings import EMBEDDING_DIM, MODEL_NAME, embed_texts, to_vector_literal
from app.md_text import split_markdown
from app.pdf_text import extract_pages

SOURCE_TYPES = ("sop", "own_note", "manual", "public_doc", "sample")
SCANNED_PAGE_THRESHOLD = 50  # fewer characters than this: probably a scan or a screenshot


def build_pdf_rows(pages: list[tuple[int, str]]) -> list[tuple[int, int, str, str | None]]:
    rows = []
    for page_no, text in pages:
        for index, chunk in enumerate(chunk_text(text)):
            rows.append((page_no, index, chunk, None))
    return rows


def store(name, content_hash, module, source_type, page_count, rows, vectors) -> None:
    with get_conn() as conn:  # commits on success, rolls back on error
        existing = conn.execute(
            "SELECT id FROM documents WHERE content_hash = %s", (content_hash,)
        ).fetchone()
        if existing:
            print("This exact file is already ingested. Delete the document first to re-ingest.")
            return
        doc_id = conn.execute(
            """INSERT INTO documents (name, content_hash, module, source_type, embedding_model, page_count)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (name, content_hash, module, source_type, MODEL_NAME, page_count),
        ).fetchone()[0]
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO chunks (document_id, page, chunk_index, t_code, content, embedding)
                   VALUES (%s, %s, %s, %s, %s, %s::vector)""",
                [
                    (doc_id, page, index, t_code, text, to_vector_literal(vec))
                    for (page, index, text, t_code), vec in zip(rows, vectors)
                ],
            )
    print(f"Stored document id {doc_id} with {len(rows)} chunks.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--source-type", required=True, choices=SOURCE_TYPES)
    parser.add_argument("--module", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    suffix = args.path.suffix.lower()
    if not args.path.is_file() or suffix not in (".pdf", ".md"):
        raise SystemExit("Give a path to an existing .pdf or .md file.")

    content_hash = hashlib.sha256(args.path.read_bytes()).hexdigest()

    if suffix == ".md":
        text = args.path.read_text(encoding="utf-8")
        if "[CHECK" in text:
            raise SystemExit("File still has [CHECK ...] markers. Verify those steps and remove them.")
        rows = split_markdown(text)
        page_count = max((r[0] for r in rows), default=0)
        print(f"{args.path.name}: {page_count} sections, {len(rows)} chunks")
    else:
        pages = extract_pages(args.path)
        rows = build_pdf_rows(pages)
        page_count = len(pages)
        thin = [n for n, t in pages if len(t.strip()) < SCANNED_PAGE_THRESHOLD]
        print(f"{args.path.name}: {page_count} pages, {len(rows)} chunks")
        if thin:
            print(f"Pages with almost no text (scans or screenshots, OCR not built yet): {thin}")

    if not rows:
        raise SystemExit("No text found. Nothing to ingest.")

    if args.dry_run:
        for page, index, text, t_code in rows[:3]:
            print(f"\n--- section/page {page}, chunk {index}, t_code={t_code} ({len(text)} chars) ---\n{text}")
        return

    if args.source_type not in ("sample", "public_doc"):
        print("This text will be stored in a cloud database (Neon) and sent to Groq with questions.")
        if input("Is this file cleaned of sensitive data and approved? (y/N) ").lower() != "y":
            raise SystemExit("Stopped.")

    vectors = embed_texts([text for _, _, text, _ in rows])
    assert len(vectors[0]) == EMBEDDING_DIM, "Embedding size doesn't match the table"
    store(args.path.name, content_hash, args.module, args.source_type, page_count, rows, vectors)


if __name__ == "__main__":
    main()