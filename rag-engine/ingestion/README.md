# Ingestion

Intended to hold the document ingestion pipeline that reads immutable source
material from `Law_files/` and writes processed artifacts into `data/`.

**Not implemented yet** — manual development pending.

## Sub-directories

| Path | Intended responsibility |
| --- | --- |
| `loaders/` | Load raw files from `Law_files/` |
| `parsers/` | Parse legal document structure |
| `cleaners/` | Clean / normalize text |
| `structure/` | Reconstruct Act → Chapter → Section → Subsection → Clause hierarchy |
| `chunking/` | Legal-aware chunking |
