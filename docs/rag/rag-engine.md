# RAG Engine Overview

This document describes the intended design of the ChatLaw RAG Engine. The
engine is **manually developed** and is currently structure-only. It is a
separate, independent Python component located in `rag-engine/`.

## Pipeline stages

```
 Law_files/ (immutable source)
   │
   ▼
 Ingestion
   ├── loaders      read raw files from Law_files/
   ├── parsers      parse legal document structure
   ├── cleaners     clean / normalize text
   ├── structure    reconstruct Act → Chapter → Section → Subsection → Clause
   └── chunking     legal-aware chunking
   ▼
 Embeddings
   ▼
 Retrieval
   ├── vector          pgvector cosine similarity
   ├── keyword         full-text / BM25
   ├── exact citation  Section X, Act Y
   └── hybrid          combine signals
   ▼
 Reranking
   ▼
 Context construction
   ▼
 Generation (Gemini)
   ▼
 Verification (grounding)
   ▼
 Evaluation
```

## Retrieval

The engine combines vector, keyword, and exact-citation retrieval into a hybrid
pipeline, then reranks candidates. It reconstructs hierarchical context from
the chunk coordinates stored in `legal_chunks` so citations can be precise.

## Generation & grounding

Gemini generates a legal answer conditioned on the constructed context. A
grounding-verification stage checks that each claim is supported by retrieved
evidence, producing a `grounded` flag, a confidence level, and citations.

## Evaluation

A dedicated harness measures retrieval quality and end-to-end answer
correctness, using artifacts in `rag-engine/data/evaluation/`.

## Data

- Source corpus: `Law_files/` (immutable, read-only).
- Generated artifacts: `rag-engine/data/` (`processed`, `chunks`, `metadata`,
  `evaluation`).
- Storage: shared PostgreSQL + pgvector database (`database/`).

## Not yet implemented

All of the above logic is intentionally absent. This document only records the
intended design. Implementation is pending manual development.
