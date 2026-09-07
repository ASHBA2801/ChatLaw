#!/usr/bin/env python3
"""ChatLaw Chunk Inspection Utility (Phase RAG-02).

Allows inspecting generated JSONL chunk files, exploring statutory context hierarchy,
continuation splits, character distributions, and specific chunk content.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure rag-engine is on sys.path
script_dir = Path(__file__).resolve().parent
rag_engine_dir = script_dir.parent
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))

from ingestion.chunking.models import LegalChunk


def load_chunks_from_jsonl(file_path: Path) -> List[LegalChunk]:
    """Loads all LegalChunk objects from a JSONL file."""
    chunks = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(LegalChunk.model_validate_json(line))
    return chunks


def display_chunk_detail(chunk: LegalChunk, show_full_content: bool = True):
    """Prints a detailed formatted view of a single LegalChunk."""
    print("\n" + "=" * 70)
    print(f"CHUNK ID:         {chunk.chunk_id}")
    print("=" * 70)
    print(f"Document ID:      {chunk.document_id}")
    print(f"Document Title:   {chunk.document_title or 'N/A'}")
    print(f"Document SHA256:  {chunk.document_sha256[:16]}...")
    print(f"Chunk Hash:       {chunk.chunk_hash}")
    print(f"Chunk Type:       {chunk.chunk_type.value.upper()}")
    print(f"Context Path:     {chunk.context_path}")
    if chunk.context_prefix:
        print(f"Context Prefix:   {chunk.context_prefix}")
    print(f"Hierarchy:")
    print(f"  - Part:         {chunk.part or 'N/A'}")
    print(f"  - Chapter:      {chunk.chapter or 'N/A'}")
    print(f"  - Section:      {chunk.section or 'N/A'}")
    print(f"  - Subsection:   {chunk.subsection or 'N/A'}")
    print(f"  - Clause:       {chunk.clause or 'N/A'}")
    print(f"  - Schedule:     {chunk.schedule or 'N/A'}")
    print(f"Page Span:        Pages {chunk.page_start} -> {chunk.page_end}")
    print(f"Chunk Index:      {chunk.chunk_index} (Part {chunk.chunk_part} of {chunk.total_parts})")
    print(f"Is Continuation:  {chunk.is_continuation}")
    if chunk.parent_chunk_id:
        print(f"Parent Chunk ID:  {chunk.parent_chunk_id}")
    print(f"Length:           {chunk.character_count:,} chars | {chunk.word_count:,} words | {chunk.line_count} lines")
    print("-" * 70)
    print("CONTENT:")
    print("-" * 70)
    if show_full_content:
        print(chunk.content)
    else:
        preview = chunk.content[:400] + ("..." if len(chunk.content) > 400 else "")
        print(preview)
    print("=" * 70 + "\n")


def inspect_chunks(
    document_name: str,
    chunk_id: Optional[str] = None,
    limit: int = 10,
    chunks_dir: Optional[Path] = None,
    full: bool = False,
):
    """Finds and displays chunks matching user criteria."""
    base_dir = chunks_dir or (rag_engine_dir / "data" / "chunks")
    
    # Try exact match or stem match
    target_file = None
    candidate_file = base_dir / f"{document_name}.jsonl"
    if candidate_file.exists():
        target_file = candidate_file
    else:
        for f in base_dir.glob("*.jsonl"):
            if document_name.lower() in f.stem.lower():
                target_file = f
                break

    if not target_file or not target_file.exists():
        print(f"Error: Could not find chunks JSONL file for document '{document_name}' in {base_dir}", file=sys.stderr)
        sys.exit(1)

    chunks = load_chunks_from_jsonl(target_file)
    print(f"Loaded {len(chunks)} chunks from {target_file.name}")

    if chunk_id:
        matched = [c for c in chunks if c.chunk_id.lower() == chunk_id.lower() or chunk_id.lower() in c.chunk_id.lower()]
        if not matched:
            print(f"No chunk found matching ID '{chunk_id}'", file=sys.stderr)
            sys.exit(1)
        for c in matched:
            display_chunk_detail(c, show_full_content=True)
        return

    # Summary mode
    print(f"\nDisplaying first {min(limit, len(chunks))} chunks:\n")
    for idx, c in enumerate(chunks[:limit]):
        preview = c.content.replace('\n', ' ')[:90]
        print(f"[{idx:03d}] {c.chunk_id:<45} | {c.chunk_type.value:<12} | P.{c.page_start}-{c.page_end} | {c.character_count:>5}c | {preview}...")

    print(f"\nUse --chunk <chunk_id> to inspect complete chunk content.")


def main():
    parser = argparse.ArgumentParser(
        description="ChatLaw Legal Chunk Inspection Tool (Phase RAG-02)."
    )
    parser.add_argument(
        "--document", "-d",
        type=str,
        required=True,
        help="Name or ID of document to inspect (e.g. BNS2023, BSA, Bharatiya_Nagarik_Suraksha_Sanhita_2023)"
    )
    parser.add_argument(
        "--chunk", "-c",
        type=str,
        default=None,
        help="Specific Chunk ID or substring to inspect in full detail"
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=15,
        help="Number of chunks to list in summary mode (default: 15)"
    )
    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=None,
        help="Custom chunks directory path (default: rag-engine/data/chunks)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show full content in summary listing"
    )

    args = parser.parse_args()

    inspect_chunks(
        document_name=args.document,
        chunk_id=args.chunk,
        limit=args.limit,
        chunks_dir=args.chunks_dir,
        full=args.full,
    )


if __name__ == "__main__":
    main()
