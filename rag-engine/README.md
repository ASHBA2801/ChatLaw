# RAG Engine

This is the **RAG Engine** component of ChatLaw — a multilingual legal-information
assistant for Indian citizens.

> **Status: STRUCTURE ONLY — implementation is manual and pending.**
>
> This directory currently contains only the intended structure and
> documentation. The RAG logic itself is **deliberately not implemented here**
> and will be developed manually (outside the scope of the automated assistant).

## Ownership boundary

The RAG Engine is a **separate, independent component** from the Next.js web
application. It is never embedded inside `web/`.

The two components communicate only through an **HTTP API contract** (see
`docs/api/`). The eventual runtime topology is:

```
Next.js  ── HTTP API ──►  RAG Engine  ──►  PostgreSQL + pgvector
```

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

## API contract

The engine exposes the endpoints documented in `docs/api/`. The key endpoint is
`POST /query`, accepting a user query, language, and optional conversation id,
and returning a grounded answer with citations and sources.
