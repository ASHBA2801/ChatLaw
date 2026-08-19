# ChatLaw Architecture

ChatLaw is a multilingual legal-information assistant for Indian citizens. The
system is split into independent components that communicate over a defined API
boundary.

## High-level topology

```
                      ┌────────────────────────────┐
                      │     Next.js (web/)         │
                      │  UI · PWA · voice ·        │
                      │  multilingual · court/     │
                      │  resource interfaces       │
                      └───────────┬────────────────┘
                                  │  HTTP API (RAG contract)
                                  ▼
                      ┌────────────────────────────┐
                      │     RAG Engine (rag-engine/│
                      │  ingestion · retrieval ·   │
                      │  generation · grounding    │
                      └───────────┬────────────────┘
                                  │  raw SQL / ORM
                                  ▼
                      ┌────────────────────────────┐
                      │   PostgreSQL + pgvector    │
                      │   (database/)              │
                      └────────────────────────────┘
```

## Component responsibilities

### 1. Next.js application (`web/`)

- User-facing UI: chat, PWA, voice interface, multilingual interface
- Legal-resource interface and court interface
- Client state, routing, and rendering
- **Never** implements RAG logic. It calls the RAG Engine over HTTP.
- Owns a `.env` for web-facing configuration.

### 2. RAG Engine (`rag-engine/`)

- Python-based, manually developed (out of scope for the automated assistant).
- Ingestion, parsing, legal-aware chunking, embeddings, retrieval (vector /
  keyword / exact citation / hybrid), reranking, context construction, Gemini
  generation, grounding verification, and RAG evaluation.
- Communicates with the Next.js app only through the HTTP API contract in
  `docs/api/`.
- Reads from `Law_files/` (immutable) and the shared PostgreSQL database.

### 3. Database (`database/`)

- **Single shared** PostgreSQL database with the pgvector extension.
- Prisma schema defines the shared tables: `legal_documents`, `legal_chunks`,
  `legal_sources`, `conversations`, `messages`.
- Used by **both** the RAG Engine and the Next.js app. The schema is defined
  **once** — never duplicated.
- Owns migrations and seed scripts.

### 4. Legal data (`legal-data/`)

- Verified, structured legal resources (sources, forms, courts, metadata) that
  are **not** the original documents.
- Complements (never duplicates) the immutable `Law_files/` corpus.

### 5. API boundary

The boundary between `web/` and `rag-engine/` is a strict HTTP contract. The
web app must not reach into the engine's internals and the engine must not
reach into the app's internals. See `docs/api/` for the full contract.

### 6. `Law_files/` immutability

`Law_files/` is the **original, read-only** corpus of Indian law documents. It
is treated as immutable source material:

- Never delete, rename, move, modify, or reformat its files.
- Never write generated files into it.
- Never add temporary files into it.
- The RAG Engine reads from it; all generated output goes to `rag-engine/data/`.

## Directory map

```
ChatLaw/
├── web/          Next.js application
├── rag-engine/   Python RAG Engine (manual development)
├── database/     Shared Prisma + PostgreSQL schema, migrations, seeds
├── legal-data/   Verified structured legal resources
├── docs/         architecture, rag, api, legal-data documentation
├── docker/       container definitions (postgres, redis)
├── scripts/      development + deployment scripts
├── Law_files/    IMMUTABLE original corpus (do not touch)
└── docker-compose.yml
```

## Cross-cutting concerns

- **Single source of truth for the schema**: `database/prisma/schema.prisma`.
- **Secrets**: each component keeps its own `.env` (git-ignored). Only
  `.env.example` files are committed.
- **Data flow**: `Law_files/` → RAG Engine ingestion → `rag-engine/data/` →
  shared PostgreSQL → RAG Engine retrieval → HTTP response → Next.js UI.
