# SAP Guide

A private RAG chat assistant that answers SAP procedure questions from your own documents, cites the document and page, and says "not found" instead of guessing.

> Built as a read-only advisor for day-to-day SAP work. It never connects to a live SAP system.

<!-- TODO: add a 20-30 second demo GIF here (login -> ask a question -> cited answer -> a "not found" case) -->

## The problem

SAP procedures live in long PDFs full of screenshots. Finding "what do I check before saving this step?" means scrolling through pages while the work waits. A wrong step in SAP can post, reverse or delete real data, so a confident wrong answer is worse than no answer.

## What it does

- Answers only from the loaded documents, in short, simple English.
- Cites the source document and page for every answer.
- Replies "not found in the documents" when the context doesn't cover the question, rather than guessing.
- Adds a "check with your supervisor first" warning on steps that post, reverse or delete data.
- Single-user login (bcrypt password, signed 24-hour session cookie).

## How it works

```
 PDFs / Markdown procedures
          |
   extract -> chunk (one step = one chunk) -> embed (bge-small-en-v1.5, local)
          |
   Neon Postgres + pgvector  (exact search, no index at this corpus size)
          |
 question -> embed -> top-3 chunks -> Groq LLM (gpt-oss-120b, fallback gpt-oss-20b)
          |
   answer + citations, or "not found"
```

Ingestion runs offline (from a dev environment) and writes to the database. The deployed app only answers questions, so no PDF or OCR processing runs on the server.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| API | Python, FastAPI | Strong document and AI libraries |
| Database | Neon Postgres + pgvector | Real SQL and vector search in one place |
| Embeddings | `bge-small-en-v1.5` via fastembed (384 dims) | Text stays local, no rate limits, small |
| LLM | Groq: `openai/gpt-oss-120b`, fallback `gpt-oss-20b` | OpenAI-compatible format, swappable |
| Auth | bcrypt (cost 12) + signed cookie (itsdangerous) | One user, no users table needed |
| Quality | pytest, ruff, custom eval harness | Measure, don't guess |

Every choice, with the alternative considered and the reason, is in [DECISIONS.md](DECISIONS.md).

## Evaluation

"Working" means passing a test set, not sounding good. The `eval/` folder holds the questions (each with the correct source page) and the scripts that score them.

Results on the **fictional sample documents** (the only data in this public repo):

| Check | Result |
|---|---|
| Retrieval, 11 answerable questions: correct chunk at rank 1 | 10 / 11 |
| Retrieval: correct chunk in top 3 | 11 / 11 |
| Answers (gpt-oss-120b): fact, page citation, format, supervisor note | 11 / 11 |
| Answers (gpt-oss-20b): fact, page citation, refusal checks | 11 / 11 (format 9 / 11) |
| Correct refusals on unanswerable questions | 4 / 4 on 20b; 3 / 4 on 120b (the miss was an API timeout) |

<!-- TODO: replace with numbers from the larger held-out set once it exists -->

**Limitations, stated up front:** the sample corpus is tiny (5 chunks), the questions were written by the author of the documents, and keyword-based checks are only a proxy for answer quality. A held-out question set written by someone else is the next step. See decisions 15, 19, 20 and 22.

## Run it locally

Prerequisites: Python 3.11+, a Neon Postgres database with the `pgvector` extension, and a Groq API key.

```bash
git clone https://github.com/madara-777-adi/sap-guide.git
cd sap-guide
pip install -r requirements.txt
cp .env.example .env     # then fill in the values
```

Environment variables (see `.env.example` for the full list):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Neon direct connection string |
| `APP_USERNAME` | The single login username |
| `APP_PASSWORD_HASH` | bcrypt hash of the password |
| `SESSION_SECRET` | Signs the session cookie |

<!-- TODO: add GROQ key variable name and the exact commands for: create schema (db/schema.sql), ingest sample_docs, start the server, run the eval -->

```bash
# Tests and lint
pip install -r requirements-dev.txt
pytest
ruff check .
```

## Privacy and safety

- Real procedure documents are git-ignored (`docs/`) and are never committed. Only fictional samples are in this repo.
- Secrets live in environment variables, never in Git.
- Real documents are only sent to hosted services with explicit approval from the person responsible for them.
- The tool is advisory and read-only: it cannot change anything in SAP.

## Not built (on purpose)

Live SAP connection, multiple users and sign-up, stored chat history, model fine-tuning, and a bot-management platform. These are listed as deliberate non-goals in DECISIONS.md.

## Project layout

```
app/           FastAPI app: auth, retrieval, answer generation
db/            Schema
eval/          Test questions and scoring scripts
sample_docs/   Fictional procedure documents
scripts/       Ingestion and utility scripts
tests/         Pytest suite
DECISIONS.md   Numbered design decisions with reasons
```

## Roadmap

- Held-out question set and a larger unanswerable set (near-miss questions)
- Unsupported-claim check: does every statement in an answer appear in the retrieved chunks?
- Hybrid search (Postgres full-text + vectors) for exact T-codes and SAP jargon
- Public demo on fictional documents
