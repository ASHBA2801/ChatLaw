# ChatLaw Web Application - Phase 22

The Next.js web application for ChatLaw: an AI-powered legal assistant for
ordinary Indian users, with regional-language chat, document drafts, personal
case workspaces, and statute research.

## Product surfaces

| Route | Purpose |
| --- | --- |
| `/` | Landing |
| `/chat` | Conversational legal assistant (interview + grounded answers) |
| `/documents` | AI draft generator workspace |
| `/cases` | Personal case workspaces (your matters) |
| `/research` | Statute/source search over the corpus |
| `/account` | Profile and language preference |

## Stack

- Next.js App Router + TypeScript
- Tailwind CSS + ESLint
- Prisma client (generated from `database/`) + PostgreSQL + pgvector
- Zod (validation)

## Language

Chat supports English plus the 22 Eighth Schedule languages. Preference is stored
in `localStorage` (`chatlaw-language`) and, when signed in, `User.preferredLanguage`.
Clarifications and answers use the selected language in a single generation call.
Official Act/section names stay in authoritative form.

## Run locally

1. Copy `web/.env.example` to `web/.env` and fill in values.
2. Install dependencies.
3. Start Postgres and apply migrations (including `preferredLanguage`).
4. Start the RAG engine and `npm run dev` from `web/`.

## Notes

- `/chat?caseId=…` remains the case-scoped assistant.
- Voice uses the browser Web Speech API; availability varies by language/browser.
- Informational assistance only — not a substitute for professional legal advice.
