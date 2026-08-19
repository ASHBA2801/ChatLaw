# ChatLaw

ChatLaw is a multilingual legal-information assistant for Indian citizens.

The project has two major engineering components:

1. **RAG Engine** (`rag-engine/`) — a Python retrieval-augmented generation
   engine (ingestion, retrieval, generation, grounding). **Manually developed
   and not implemented yet** — this directory is structure + documentation only.
2. **Web application** (`web/`) — a Next.js web/PWA application (UI, voice,
   multilingual, legal-resource and court interfaces).

The two components are **independent** and communicate only over an HTTP API
contract (see `docs/api/`).

## Repository layout

```
ChatLaw/
├── Law_files/       IMMUTABLE original law-document corpus (do not touch)
├── rag-engine/      Python RAG Engine (structure only; manual development)
├── web/             Next.js web/PWA application
├── database/        Shared PostgreSQL + pgvector schema, migrations, seeds
├── legal-data/      Verified structured legal resources (forms, courts, ...)
├── docs/            architecture, rag, api, legal-data documentation
├── docker/          container definitions (postgres, redis)
├── scripts/         development + deployment scripts
└── docker-compose.yml
```

## Architecture

```
Next.js (web/) ── HTTP API ──► RAG Engine (rag-engine/) ──► PostgreSQL + pgvector (database/)
```

- **`web/`** owns the user-facing experience and calls the RAG Engine over HTTP.
- **`rag-engine/`** owns all RAG logic (manually developed).
- **`database/`** is the **single shared** PostgreSQL + pgvector schema used by
  both the RAG Engine and the web app.
- **`legal-data/`** holds curated structured legal resources (not the original
  documents).
- **`Law_files/`** is the immutable original corpus — never modify it.

See `docs/architecture/` for details.

## Source documents

`Law_files/` is the original law-document dataset. It is **read-only** and must
never receive generated or processed files. Future ingestion reads from it and
writes to `rag-engine/data/`.

## Stack

- **Web**: Next.js App Router + TypeScript, Tailwind CSS, ESLint, Zod
- **Database**: PostgreSQL + Prisma + pgvector
- **RAG Engine**: Python (manual development, pending)

## Getting started

### 1. Install dependencies

```bash
npm install
```

### 2. Start the shared database

```bash
docker compose -f docker/postgres/compose.yml up -d
```

### 3. Initialize + migrate the database

```bash
npm run db:init      # create DB + enable pgvector (idempotent)
npm run db:migrate   # apply schema migrations (dev)
```

### 4. Run the web app

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The `/chat` route is intentionally UI-only. AI, RAG, voice, multilingual
behavior, authentication, and persistence are not implemented yet.

## Environment

Each component keeps its own git-ignored `.env`:

- `web/.env.example`
- `database/.env.example`
- `rag-engine/.env.example`

Never commit real API keys.

## Database

The shared database uses **PostgreSQL + Prisma + pgvector**.

- Schema: `database/prisma/schema.prisma` (5 tables: `legal_documents`,
  `legal_chunks`, `legal_sources`, `conversations`, `messages`).
- Legal documents preserve their hierarchy (`Act → Chapter → Section →
  Subsection → Clause`) via hierarchical columns on `legal_chunks`.
- Embeddings are stored in a pgvector `vector(768)` column. Vector operations
  go through the abstraction in `database/lib/vector-search.ts`
  (`semanticSearch`), decoupled from Prisma's typed client.
- The Prisma client is generated into `web/lib/generated/prisma` (consumed by
  the web app via `@/lib/generated/prisma/client`).

See `database/README.md` for details.

## Documentation

- `docs/architecture/` — component responsibilities and boundaries
- `docs/rag/` — RAG Engine design
- `docs/api/` — RAG API contract
- `docs/legal-data/` — legal-data guide

## Learn more

- [Next.js Documentation](https://nextjs.org/docs)
- [Prisma Documentation](https://www.prisma.io/docs)
- [pgvector](https://github.com/pgvector/pgvector)
