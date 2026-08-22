# RAG Engine - Phase 21

This is the **RAG Engine** component of ChatLaw — a multilingual legal-information assistant.

The RAG Engine provides grounded legal information retrieval and document-based reasoning. In Phase 21, it supports integrated retrieval from the Case Workspace's stored document corpus.

## Ownership boundary

The RAG Engine is an independent service communicating only through an **HTTP API contract** (see `docs/api/`).

```
Next.js  ── HTTP API ──►  RAG Engine  ──►  PostgreSQL + pgvector
```

## Key Modules

- `api/`       — FastAPI implementation of RAG endpoints
- `ingestion/` — Document processing pipeline
- `retrieval/` — Contextual vector search and reranking
- `generation/`— Context-aware legal answer generation

## Status

**Implemented: Phases 1–21.**

Retrieval/Embedding ingestion is triggered via `scripts/`. It is never run as an side effect of user interaction.

## Responsibilities

The RAG Engine owns all retrieval-augmented generation logic:

- **Ingestion** — load, parse, clean, structure, and chunk legal documents
- **Embeddings** — encode chunks and queries into vectors
- **Retrieval** — vector, keyword, exact-citation, and hybrid retrieval
- **Reranking** — reorder candidate results for relevance
- **Context construction** — assemble retrieval results into a prompt context
- **Generation** — Gemini-backed legal response generation
- **Verification** — grounding and citation verification
- **Evaluation** — RAG quality measurement

## Directory layout

| Path | Intended responsibility |
| --- | --- |
| `data/processed/` | Processed source documents (never `Law_files/` itself) |
| `data/chunks/` | Generated legal-aware chunks |
| `data/metadata/` | Document and chunk metadata |
| `data/evaluation/` | RAG evaluation artifacts |
| `ingestion/loaders/` | Load raw files from `Law_files/` |
| `ingestion/parsers/` | Parse legal document structure |
| `ingestion/cleaners/` | Clean / normalize text |
| `ingestion/structure/` | Reconstruct Act → Chapter → Section → Subsection → Clause hierarchy |
| `ingestion/chunking/` | Legal-aware chunking |
| `embeddings/` | Embedding model adapters |
| `retrieval/` | Vector / keyword / citation / hybrid retrieval |
| `reranking/` | Candidate reranking |
| `context/` | Context construction for prompts |
| `generation/` | Gemini legal generation |
| `verification/` | Grounding verification |
| `evaluation/` | RAG evaluation harness |
| `api/` | HTTP API server exposing the RAG contract |
| `config/` | Engine configuration |
| `tests/` | Engine tests |

## Source material

`Law_files/` is the immutable, read-only original corpus. The engine must
**read** from `Law_files/` during ingestion and **write** generated artifacts
only into `data/`. Never write into `Law_files/`.

## Environment

See `.env.example`. Keys (e.g. `GEMINI_API_KEY`, `DATABASE_URL`) must never be
committed. Shared database access uses the schema defined in `database/`.

## RAG-03 embedding and database ingestion

RAG-03 reads the JSONL chunks in `data/chunks/`, validates them, generates
embeddings through a provider adapter, validates exact compatibility with the
existing PostgreSQL `vector(768)` column, and can upsert into `legal_documents`
and `legal_chunks`. It does not modify the Prisma schema or run migrations.

Required configuration:

```text
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=<exact configured model name>
GEMINI_EMBEDDING_MODEL=<same exact model name>
GEMINI_API_KEY=<secret>
EMBEDDING_DIMENSION=768
EMBEDDING_BATCH_SIZE=32
GEMINI_REQUEST_TIMEOUT_SECONDS=60
DATABASE_CONNECT_TIMEOUT_SECONDS=30
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/chatlaw
```

Configuration details:

- **Provider:** `gemini` only; this is the only provider implemented by RAG-03.
- **Model:** the exact value supplied in `EMBEDDING_MODEL`, repeated in
	`GEMINI_EMBEDDING_MODEL`. No model name is selected or invented by the code.
- **API base URL:** not applicable/configurable. The `google-genai` adapter uses
	the SDK's default Gemini API endpoint.
- **Expected dimension:** exactly `768`, matching the existing
	`legal_chunks.embedding vector(768)` column. The validator fails on any
	other dimension and never pads, truncates, or reshapes vectors.
- **Batch size:** `EMBEDDING_BATCH_SIZE`, default `32`.
- **Gemini request timeout:** `GEMINI_REQUEST_TIMEOUT_SECONDS`, default `60` seconds.
- **Database connection timeout:** `DATABASE_CONNECT_TIMEOUT_SECONDS`, default `30` seconds.
- **Retries:** the current ingestion orchestrator retries each failed batch up
	to 3 times after the initial attempt, with delays of 1, 2, and 4 seconds
	(exponential backoff). Retry count is currently code-defined, not an
	environment variable.
- **Database:** `DATABASE_URL` must point to the existing PostgreSQL/pgvector
	database. Configuration validation checks its presence and URL shape but
	does not connect to the database.

The model/provider must return exactly 768 finite numeric values. Vectors are
never padded, truncated, or reshaped. The Python deterministic `chunk_id` is
used as the `legal_chunks.id` primary key. The Python document ID and richer
hierarchy metadata are preserved in JSONB; document rows use a deterministic
ID derived from source document ID and source SHA-256. Re-running unchanged
input is therefore idempotent, while changed content updates the existing
document/chunk identity and embedding.

Safe validation-only command (default behavior; no API or database writes):

```text
python scripts/validate_embedding_config.py
```

The chunk dry-run remains available and validates chunk files without making
API or database writes:

```text
python scripts/embed_chunks.py --input data/chunks --dry-run
```

Explicit real ingestion command (developer-run only):

```text
python scripts/embed_chunks.py --input data/chunks --execute
```

## RAG-05 semantic retrieval

Retrieval embeds the original query with the same configured Gemini provider
and 768-dimensional contract, then performs parameterized pgvector cosine
search against the existing `legal_chunks` table. It returns source content,
legal hierarchy, metadata, and a similarity score. The search CLI creates the
optional HNSW cosine index if it is absent; it does not modify chunk rows.

```text
python scripts/search.py "What is the punishment for theft?" --top-k 8 --min-similarity 0.70
```

Use `--json` for structured `RetrievalResponse` output. When no row meets the
threshold, the response sets `no_relevant_context` to `true` and contains no
fabricated context. RAG-06 answer generation is intentionally not included.

For a controlled first diagnostic, process exactly one selected chunk and
measure embedding request/response plus database connection/insert timing:

```text
python scripts/embed_chunks.py --input data/chunks --document BNS2023 --batch-size 1 --one-chunk-timing --execute
```

Every Gemini request has a finite timeout. Batch retries are bounded to the
initial attempt plus three retries with 1/2/4 second backoff. The diagnostic
command is the only recommended first execution; do not start the full corpus
until its timing output is reviewed.

Reports are written to `data/metadata/embedding_report.json` and
`data/metadata/embedding_report.txt`. The real command requires manually
installed optional provider/database packages and explicit environment values.

## API contract

The engine exposes the endpoints documented in `docs/api/`. The key endpoint is
`POST /query`, accepting a user query, language, and optional conversation id,
and returning a grounded answer with citations and sources.
