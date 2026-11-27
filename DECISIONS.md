# Decisions

One entry per choice, with the reason. Update the status when something changes.

## Decided

### 1. Build SAP Guide first, bot platform later

Status: decided, 2026-11-26
SAP Guide is a private tool for my own SAP work. A bot-management platform (documents, API keys, model names, several bots per business) is a later project. It waits until SAP Guide works and has been used for real, so I learn what a bot actually needs.

### 2. MVP scope

- One user, one username and password, 24-hour session.
- A simple chat page.
- Answers come only from my documents, in short and simple English, with document and page cited.
- If the documents don't cover it, the bot says so and doesn't guess.
- Steps that post, reverse or delete data carry a "check with your supervisor first" warning.

### 3. Not building now

- Connection to the live SAP system (the tool only advises and is read-only).
- Multiple users, sign-up, password reset, admin screens.
- Stored chat history.
- Model training or fine-tuning.
- Error-explainer mode and showing source page images (maybe later).

### 4. Approach: RAG, not training

The models are already trained. I build the pipeline: extract, chunk, embed, store, retrieve, answer. The quality comes from chunking, retrieval, the prompt and a test set.

### 5. Language and framework: Python, FastAPI

Reason: strong libraries for documents and AI, readable syntax, and I already know FastAPI.

### 6. Browser-only development

GitHub Codespaces for running code (about 60 free hours a month on a 2-core machine), github.dev for edits that don't need to run. Reason: my laptop is broken. I stop the codespace when idle and delete unused ones.

### 7. Database: Neon Postgres with pgvector

Reason: free tier without a card, real SQL, and vector search inside the same database. The direct connection string is stored as the Codespaces secret DATABASE_URL, never in a file in Git. No vector index at first: with a few thousand chunks an exact search is fast enough.

### 8. LLM provider is swappable

Providers use the OpenAI-compatible format, so switching means changing the base URL and model name. Provisional order: Groq first, NVIDIA NIM as fallback, Gemini as an optional third. This is confirmed only after running the same test questions through each model. Free-tier terms change, so I recheck them before relying on any.

### 9. Privacy rules

- Only sample or anonymised documents in free online tools until my supervisor approves real ones.
- Remove names, IDs, vendor and bank details, amounts, document numbers, system ID and client number, then check screenshots, PDF metadata, hidden content and file names.
- Real documents live in docs/, which is git-ignored. Never commit .env, secrets or documents.
- Use real redaction, not black boxes drawn over text.

### 10. Authentication design

- User stored in environment variables (APP_USERNAME, APP_PASSWORD_HASH, SESSION_SECRET), no users table, because there is one user.
- Password hashed with bcrypt, cost 12.
- Session is a signed cookie (itsdangerous) valid for 24 hours: HttpOnly, Secure, SameSite=Lax.
- Wrong username and wrong password give the same generic error.
- Login accepts JSON, not a form.
- Tradeoff: a signed cookie can't be cancelled on the server. Logout only clears the browser cookie. Changing SESSION_SECRET logs out every session. Acceptable for one user.

### 11. Ingestion runs offline

I run ingestion from Codespaces and write results to Neon. The deployed app only answers questions, so OCR and PDF processing never run on the free server.

### 12. Evaluation before retrieval code

I write about 15 real test questions with the correct source page for each before building retrieval. "Working" means passing this set, not sounding good.

### 13. How I work

- I write the code and understand every line before committing.
- I look at the real output at each stage: extracted text, chunks, OCR results.
- Small commits, one idea each. Dependencies are added only with a reason.

## Dependencies

- fastapi, uvicorn[standard]: web framework and server.
- psycopg[binary]: current Postgres driver.
- bcrypt: password hashing.
- itsdangerous: signed, expiring session tokens.
- pytest, httpx: tests (the FastAPI TestClient needs httpx).
- Planned, not yet added: fastembed (embeddings), pypdf or pymupdf (PDF text), pytesseract (OCR, stretch goal).

## OPEN (decide and write the reason)

- Embedding model and vector size. My leaning: local bge-small-en-v1.5 via fastembed (384 dimensions) for privacy and no rate limits, to be tested for memory on Render. Hosted API is the alternative. Decide after the three-sentence similarity experiment.
- Failed-login limit: how many attempts, and for how long a block?
- Database schema (db/schema.sql): tables, columns, duplicate handling, cascade deletes, and whether to include a collections table for the later platform.
- Chunk size and overlap. Start around 800 characters with about 100 overlap, then compare on the test set.
- Which LLM performs best on my test questions.
- Which real documents my supervisor approves.
- Whether OCR for screenshots is needed, after seeing which PDFs are scanned or contain screenshots.

## Later (not now)

- Bot-management platform: bots as configurations (documents, model, key, instructions), several bots per business, per-bot knowledge isolation enforced on the server, encrypted API keys, a fixed provider dropdown instead of free-form URLs to avoid SSRF. SAP Guide could become bot #1.

### 14. Embedding model: bge-small-en-v1.5 via fastembed
Status: decided, provisional until the 15-question test
Vector size 384. Chosen for privacy (text stays local), no rate limits, small size (67 MB).
Experiment: related pair 0.717, unrelated 0.478, "MIRO" vs "invoice verification" 0.522.
Finding: separates meaning from noise, weak on SAP jargon.
Mitigation: put T-code and plain-English name in chunk text, store T-code in its own column,
add keyword search later only if the test questions show misses.
To check: query vs passage embedding, Render memory and cold-start time, model cache location.

### 15. Retrieval: plain query, no BGE prefix; "not found" handled by the prompt
Status: decided, revisit with a larger corpus
Eval (5 chunks, 11 answerable + unanswerable questions): rank-1 10/11, top-3 11/11, same with and without prefix.
Answerable top scores 0.607 to 0.712 avg, unanswerable up to 0.702: ranges overlap, so no single similarity cut-off can decide "not found".
Weak spot: a single rule inside a chunk about other topics (question 10) ranked third.
Limits: tiny corpus, questions written by the document's author.

### 16. NVIDIA Nemotron 3.5 embed/rerank: evaluate later, don't adopt now
Status: deferred
Hosted versions are a Preview API (may change or end). Embed 1B outputs 2048 dims, 8B 4096; table is vector(384).
Switching requires a schema change and full re-embed. Text would also leave our environment.
Plan: after the second fictional document and harder questions exist, compare in a script
(no DB changes), and test the reranker on top-10 results. Adopt only if it wins on our eval.

### 17. LLM provider: Groq only
Status: decided
Primary openai/gpt-oss-120b, fallback openai/gpt-oss-20b (separate per-model limits).
NVIDIA NIM dropped for now (decision 16 covers embed/rerank evaluation later).
Limits verified on own console Limits page (2026-11-26): gpt-oss-120b, gpt-oss-20b and qwen/qwen3.8-27b
each 30 RPM, 1K RPD, 8K TPM, 200K TPD. Qwen is a preview model: experiments only.
allam-2-7b also allowed (30 RPM, 7K RPD, 6K TPM, 500K TPD) but not used: believed Arabic-focused, unverified.

### 18. Gemini: not used for now
Status: deferred
Free tier is free without a card, but content is used to improve Google products,
so it would only ever see sample documents. Groq stays the only provider (decision 17).
Possible later: Gemini as an optional fallback for sample data only, via the OpenAI-compatible endpoint.
Before any real document: read Groq's data-retention/training terms and get supervisor approval.

Lint: ruff. The blanket except in the LLM fallback is intentional (noqa with a reason). FastAPI Depends marked immutable in ruff.toml.

### 19. Answer evaluation, first results (15 questions, fictional notes)
Status: provisional
openai/gpt-oss-120b, two runs: 11/11 answerable pass all checks (fact, page citation, format, supervisor note);
refusals 4/4 and 3/4. The 3/4 was an APITimeoutError (30s limit), not a wrong answer.
Caveats: the two runs overlapped and shared the per-minute token limit; only 5 chunks exist, so the model
sees most of the document every time; keyword checks are proxies; I wrote the questions with the document.
Changes: eval retries timeouts and rate limits; app timeout 30s -> 20s.
Next: a second fictional document and questions written by someone else.

### 20. Answer evaluation: openai/gpt-oss-20b (15 questions, fictional notes)
Status: provisional
11/11 answerable pass fact, page and refusal checks; 4/4 correct refusals; no errors.
format_ok 9/11: citation written inline in brackets instead of a "Source:" line.
Check kept strict on purpose. Prompt tweak: example without brackets, "always end with a Source line".
Order stays groq-120b, groq-20b. Same caveats as decision 19 (tiny corpus, author-written questions).

### 21. Shorter process title in Markdown chunks
Status: decided, retrieval still being tuned
The long title repeated in every chunk blurred the search (top-8 scores within 0.03).
Shortened both titles; "make a delivery" question moved from rank 4 to 2. "Check before saving" still rank 7.
Next: check chunk sizes, test BGE query prefix, then consider merging tiny chunks or adding keyword search.

### 22. Retrieval settings: no query prefix, TOP_K stays 3
Status: decided (25 answerable real questions, retrieval only)
Plain: top1 20, top3 24, top5 24 of 25. Prefix: top1 20, top3 22, top5 25.
Prefix fixed 2 questions and broke 2, so it stays off. TOP_K 5 gives no gain over 3 on plain.
Remaining miss ("check before saving") fixed by wording the step the way I ask it, not by tuning search.
Caveat: questions were written from the documents; re-measure with questions I really type.

### 23. Known miss: "check before saving the STO"
Status: being fixed
Rewording Step 1 did not help. After re-ingest the bot answered about saving the delivery (section 4)
and added a consequence the document does not state. A wrong answer is worse than a refusal.
Fixes: one chunk per step (decision 25), and a prompt rule to refuse when the context is about a different thing.

### 25. Chunking for Markdown: one step = one chunk
Status: provisional, measure with eval_real
BODY_SIZE 1200 so no step is split. Risk: bigger chunks dilute the match.