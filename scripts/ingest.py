"""Ingest one PDF: extract text per page, chunk, embed, store in Neon.

Dry run (no embedding, no database), to inspect what would be stored:
    python -m scripts.ingest sample_docs/file.pdf --source-type sample --dry-run
Real run:
    python -m scripts.ingest sample_docs/file.pdf --source-type sample --module FI
"""
import argparse
import hashlib
from pathlib import Path

from app.chunking import chunk_text
from app.db import get_conn
from app.embeddings import EMBEDDING_DIM, MODEL_NAME, embed_texts, to_vector_literal
from app.pdf_text import extract_pages

SOURCE_TYPES = ("sop", "own_note", "manual", "public_doc", "sample")
SCANNED_PAGE_THRESHOLD = 50  # fewer characters than this: probably a scan or a screenshot


def build_rows(pages: list[tuple[int, str]]) -> list[tuple[int, int, str]]:
    rows = []
    for page_no, text in pages:
        for index, chunk in enumerate(chunk_text(text)):
            rows.append((page_no, index, chunk))
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
                """INSERT INTO chunks (document_id, page, chunk_index, content, embedding)
                   VALUES (%s, %s, %s, %s, %s::vector)""",
                [
                    (doc_id, page, index, text, to_vector_literal(vec))
                    for (page, index, text), vec in zip(rows, vectors)
                ],
            )
    print(f"Stored document id {doc_id} with {len(rows)} chunks.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--source-type", required=True, choices=SOURCE_TYPES)
    parser.add_argument("--module", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.pdf.is_file() or args.pdf.suffix.lower() != ".pdf":
        raise SystemExit("Give a path to an existing .pdf file.")

    content_hash = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
    pages = extract_pages(args.pdf)
    rows = build_rows(pages)

    thin_pages = [n for n, text in pages if len(text.strip()) < SCANNED_PAGE_THRESHOLD]
    print(f"{args.pdf.name}: {len(pages)} pages, {len(rows)} chunks")
    if thin_pages:
        print(f"Pages with almost no text (scans or screenshots, OCR not built yet): {thin_pages}")
    if not rows:
        raise SystemExit("No text found. Nothing to ingest.")

    if args.dry_run:
        for page, index, text in rows[:3]:
            print(f"\n--- page {page}, chunk {index} ({len(text)} chars) ---\n{text}")
        return

    if args.source_type not in ("sample", "public_doc"):
        print("This text will be stored in a cloud database (Neon).")
        if input("Is this file cleaned of sensitive data and approved? (y/N) ").lower() != "y":
            raise SystemExit("Stopped.")

    vectors = embed_texts([text for _, _, text in rows])
    assert len(vectors[0]) == EMBEDDING_DIM, "Embedding size doesn't match the table"
    store(args.pdf.name, content_hash, args.module, args.source_type, len(pages), rows, vectors)


if __name__ == "__main__":
    main()