# Legal Data Guide

This document explains `legal-data/` and how it relates to the rest of the
project.

## What `legal-data/` is

`legal-data/` holds **verified, structured legal resources** that support the
application but are **not** the original source documents. For example:

- **`sources/`** — curated references to authoritative legal sources (official
  gazette links, legislative bodies).
- **`forms/`** — standard legal forms (writs, complaints, etc.).
- **`courts/`** — court directories and jurisdiction metadata.
- **`metadata/`** — structured metadata about laws and documents.

These are meant to be curated, validated, and maintained as structured
resources.

## How it differs from `Law_files/`

| | `Law_files/` | `legal-data/` |
| --- | --- | --- |
| Role | Original corpus (immutable) | Curated structured resources |
| Mutability | **Read-only** — never modify | Can be curated / added to |
| Ownership | Source of truth for documents | Support / reference data |
| Population | Do **not** copy here | Populated manually as needed |

## Rules

1. Never copy the entire `Law_files/` dataset into `legal-data/`.
2. Never write generated RAG artifacts into `legal-data/`.
3. Treat `legal-data/` as curated, reviewed content — not raw output.
