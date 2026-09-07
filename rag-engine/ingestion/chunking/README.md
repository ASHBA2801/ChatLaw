# Chunking Module (Phase RAG-02)

This module is reserved for **Phase RAG-02: Legal-Aware Chunking**.

## Interface Contract

Chunking consumes the structured `DocumentData` JSON produced by Phase RAG-01 (`data/processed/*.json`).

### Input Data
- `document_id`: Unique identifier
- `pages`: Ordered list of `PageData` objects containing:
  - `page_number`
  - `raw_text`
  - `cleaned_text`
  - `detected_structure`: List of `StructuralUnit` entities (`ACT_TITLE`, `PART`, `CHAPTER`, `SECTION`, `SUBSECTION`, `CLAUSE`, `PROVISO`, `EXPLANATION`, `ILLUSTRATION`, etc.)

### Target Chunking Principles
1. **Never split statutory sections across chunks** unless a single section exceeds maximum token context.
2. **Preserve legal context hierarchy**: prepend `[Act] > [Chapter] > [Section]` metadata headers to each chunk.
3. **Keep Explanations, Illustrations, and Provisos** attached to their parent Section.
4. **Generate clean chunk IDs and chunk-level metadata** written to `data/chunks/`.
