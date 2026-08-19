# RAG Documentation

Documentation for the **RAG Engine** design and operation.

> **Status:** The RAG Engine is manually developed and **not implemented yet**.
> These documents describe intended responsibility and design; the engine code
> lives in `rag-engine/`.

## Contents

- [RAG Engine overview](./rag-engine.md) — the retrieval-augmented generation
  pipeline and its stages.

## Key principles

- The RAG Engine is independent from the Next.js application.
- It communicates with the app only over the HTTP API contract (`docs/api/`).
- It reads immutable sources from `Law_files/` and writes to `rag-engine/data/`.
- It shares the PostgreSQL + pgvector database defined in `database/`.
