# Database - Phase 21

Shared PostgreSQL + pgvector infrastructure for ChatLaw, supporting the Phase 21 Case Workspace.

This database is used by **both** the RAG Engine (`rag-engine/`) and the Next.js application (`web/`). The schema is defined **once** here and never duplicated.

## Phase 21 Schema Updates

The database now manages:
- **Case Workspaces** (cases, timeline events, important dates)
- **Document Management** (case-associated documents, metadata, and status)
- **User Authentication** (NextAuth sessions and identity)

## Stack

- PostgreSQL with the **pgvector** extension
- Prisma 7 (driver adapters: `@prisma/adapter-pg` + `pg`)
- Local DB runs in Docker (`docker/postgres/compose.yml`), host port **5433**

## Commands

```bash
npm run db:migrate  # Run pending migrations
npm run db:generate # Generate Prisma client
npm run db:studio   # Inspect data
```
| `scripts/db/` | DB init / reset / check / vector-search test scripts |
| `lib/vector-search.ts` | pgvector search primitive (raw SQL) |
| `seeds/` | Seed scripts (empty until needed) |

## Schema

5 tables mapped to snake_case via `@@map`:

- `legal_documents`
- `legal_chunks`
- `legal_sources`
- `conversations`
- `messages`
- `users`, `accounts`, `sessions`, `verification_tokens` (Auth.js)
- `user_documents`, `user_document_versions` (user-owned generated drafts)
- `cases`, `case_documents`, `case_timeline_events`, `case_important_dates` (Phase 21)
- `conversations.userId` (optional owner binding for case ask)

`legal_chunks.embedding` is a pgvector `vector(768)` column, exposed via
Prisma's `Unsupported` type. Vector operations go through raw SQL in
`lib/vector-search.ts` (`semanticSearch`).

## Generated client

The Prisma client is generated into `web/lib/generated/prisma` (the Next.js
app imports it via `@/lib/generated/prisma/client`). Run `prisma generate`
from this directory to regenerate it.

## Environment

Copy `.env.example` to `.env` and set `DATABASE_URL`. Never commit real
credentials.

## Commands

Run Prisma commands from this directory:

```bash
# from database/
npx prisma generate
npx prisma migrate dev
npx prisma migrate deploy
npx prisma studio
```

Or use the convenience scripts:

```bash
node scripts/db/init.mjs                 # create DB + enable pgvector (idempotent)
node scripts/db/check-connection.mjs     # connection + pgvector check
npx tsx scripts/db/test-vector-search.ts # semanticSearch smoke test
node scripts/db/reset.mjs                # DESTRUCTIVE dev-only reset
```
