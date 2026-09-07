# API Documentation

Defines the boundary between the **Next.js application** (`web/`) and the
**RAG Engine** (`rag-engine/`).

> **Status:** Contract documentation only. The RAG Engine is **not implemented
> yet**, and no fake/mock response that could be mistaken for a real RAG system
> is shipped. Any development-only mock, if introduced later, must be clearly
> isolated and labeled as a mock.

## Contents

- [RAG API contract](./rag-api.md) — search, chat, conversations, and document generation on the RAG engine.
- [Document generator](./document-generator.md) — user-owned drafts, versions, and export.

## Guiding rules

1. `web/` and `rag-engine/` communicate **only** over HTTP.
2. No RAG implementation is embedded inside `web/`.
3. The web app sends a query, language, and conversation id; the engine returns
   a grounded answer, confidence, citations, and sources.
4. Contract docs describe the intended contract and may evolve before the
   engine is implemented.
