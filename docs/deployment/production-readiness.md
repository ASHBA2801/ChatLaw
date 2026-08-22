# ChatLaw production preparation

This document describes preparation only. It does not deploy or import data.

## Runtime

Build the web application with `npm run build` and run it with `npm run start`.
Run the RAG service as a persistent container using:

```text
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

The supplied `rag-engine/Dockerfile` uses this command and runs as a non-root
user. Set `RAG_API_URL` and `RAG_API_SECRET` only in the Next.js server
environment. Set the same `RAG_API_SECRET` in the RAG service environment.

## Database migration safety

For production use `npm run db:deploy`. Never use `prisma migrate dev`,
`prisma db push`, `prisma migrate reset`, or the repository reset script against
production.

The database must provide PostgreSQL and the `vector` extension. The schema
requires `vector(768)`. The current retrieval SQL uses cosine distance with
`<=>`. A vector index should be added only after measuring corpus size and
query plans; `retrieval.vector_search.ensure_cosine_index()` is an explicit
operational helper and is not run automatically by the API.

## Corpus import and verification

Use the existing ingestion/upsert pipeline in resumable, document-scoped runs.
The upsert layer identifies documents from source identity/content hashes and
updates chunks idempotently. Before import, validate `EMBEDDING_DIMENSION=768`
and ensure `EMBEDDING_MODEL` matches `GEMINI_EMBEDDING_MODEL`. After each run,
execute `python scripts/check_corpus.py` and compare document, chunk, embedded
chunk, missing embedding, and dimension counts with the source manifest.

Do not regenerate embeddings during deployment. Preserve the existing vectors
and verify document content hashes and vector dimensions after restore/import.

## Backup and restore

Use the selected PostgreSQL provider's managed backup/snapshot facility or its
documented `pg_dump`/`pg_restore` equivalent. Backups must include the
`legal_documents`, `legal_chunks`, `legal_sources`, conversations, messages,
users, accounts, sessions, user-owned generated documents and versions,
Phase 21 case workspace tables (`cases`, `case_documents`,
`case_timeline_events`, `case_important_dates`), and the pgvector
extension/schema state.

Separately back up the on-disk case PDF store rooted at `CASE_STORAGE_ROOT`
(or the default `web/.data/case-documents` path). Database rows alone are not
enough to restore uploaded case files.

Restore into an isolated database, run `npm run db:deploy` only when the
migration state requires it, restore case PDF objects to the same storage key
layout, then run `python scripts/check_corpus.py` and a read-only retrieval
smoke test.

Provider-specific commands must be supplied by the final hosting provider;
they are intentionally not invented here.

## API security

Expensive `/api/*` mutation and retrieval endpoints require a Bearer service
secret. Browser requests use the Next.js `/api/rag/*` server-side proxy, so the
secret is not a `NEXT_PUBLIC_*` variable. `/health` and `/ready` remain public.
The API has configurable in-memory rate limiting and request size checks. For
multiple RAG instances, replace this with a shared gateway/provider limiter.

End-user authentication for the document and case workspaces uses Auth.js with
Google. Set `AUTH_SECRET`, `AUTH_GOOGLE_ID`, and `AUTH_GOOGLE_SECRET` only in the
Next.js server environment. Case and document ownership is evaluated from the
session, never from a client-supplied user ID. Case-scoped conversations store
an optional `userId` and are verified against the owned case before messages
are accepted.