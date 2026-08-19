# ChatLaw Web Application

The Next.js web/PWA application for ChatLaw — a multilingual legal-information
assistant for Indian citizens.

## Scope

This application owns the **user-facing** experience:

- Chat interface
- PWA
- Voice interface
- Multilingual interface
- Legal-resource interface
- Court interface

It does **not** implement RAG logic. It communicates with the RAG Engine
(`rag-engine/`) over the HTTP API contract documented in `docs/api/`.

## Stack

- Next.js App Router + TypeScript
- Tailwind CSS + ESLint
- Prisma client (generated from `database/`) + PostgreSQL + pgvector
- Zod (validation)

## Layout

| Path | Purpose |
| --- | --- |
| `app/` | App Router pages and layouts |
| `components/` | React components (chat, layout, ui) |
| `lib/` | Server-side helpers (db client, validation, etc.) |
| `public/` | Static assets |
| `types/` | Shared TypeScript types |

## Run locally

1. Copy `web/.env.example` to `web/.env` and fill in values.
2. Install dependencies (from the repo root or this directory).
3. Start the shared database:
   ```bash
   docker compose -f docker/postgres/compose.yml up -d
   ```
4. Apply migrations (from `database/`):
   ```bash
   cd ../database
   npm run db:init
   npm run db:migrate
   ```
5. Start the dev server (from `web/`):
   ```bash
   npm run dev
   ```

The `/chat` route is intentionally UI-only. AI, RAG, voice, multilingual
behavior, authentication, and persistence are not implemented yet.

## Environment

See `.env.example`. `DATABASE_URL` points to the shared database. Never commit
real keys.
