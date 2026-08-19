#!/usr/bin/env python3
"""ChatLaw Legal-Aware Chunking Pipeline Runner (Phase RAG-02).

Reads processed JSON documents from rag-engine/data/processed/*.json,
chunks them according to Indian statutory legal structure, validates chunks,
saves individual JSONL files to rag-engine/data/chunks/*.jsonl, and produces
corpus-level chunking reports in JSON and human-readable text formats.
"""

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from tqdm import tqdm

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

from ingestion.chunking.legal_chunker import LegalChunker
from ingestion.chunking.models import ChunkingReport, ChunkType, LegalChunk
from ingestion.chunking.validator import ChunkValidator
from ingestion.models import DocumentData


def resolve_default_paths(base_dir: Path):
    """Resolves default processed, chunks, and metadata paths."""
    processed_dir = base_dir / "data" / "processed"
    chunks_dir = base_dir / "data" / "chunks"
    metadata_dir = base_dir / "data" / "metadata"
    return processed_dir, chunks_dir, metadata_dir


def format_human_chunking_report(report: ChunkingReport) -> str:
    """Formats the chunking report into a clean human-readable text document."""
    lines = [
        "==================================================================",
        "             CHATLAW LEGAL CHUNKING REPORT (PHASE RAG-02)",
        "==================================================================",
        f"Report Generated:     {report.report_timestamp_iso}",
        f"Processing Duration:  {report.processing_duration_seconds:.2f} seconds",
        "",
        "------------------------------------------------------------------",
        "SUMMARY METRICS",
        "------------------------------------------------------------------",
        f"Documents Processed:      {report.documents_processed}",
        f"Total Chunks Generated:   {report.total_chunks:,}",
        f"Oversized Chunks Split:   {report.oversized_chunks_count}",
        f"Continuation Chunks:      {report.continuation_chunks_count}",
        f"Fallback Chunks:          {report.fallback_chunks_count}",
        "",
        "------------------------------------------------------------------",
        "CHUNK SIZE STATISTICS (CHARACTERS)",
        "------------------------------------------------------------------",
        f"Average Length:           {report.avg_characters_per_chunk:.1f} chars",
        f"Median Length:            {report.median_characters_per_chunk:.1f} chars",
        f"Minimum Length:           {report.min_characters_per_chunk} chars",
        f"Maximum Length:           {report.max_characters_per_chunk:,} chars",
        "",
        "------------------------------------------------------------------",
        "CHUNKS BY STRUCTURAL TYPE",
        "------------------------------------------------------------------",
    ]

    for c_type, count in sorted(report.chunks_by_type.items(), key=lambda x: -x[1]):
        pct = (count / report.total_chunks * 100) if report.total_chunks else 0.0
        lines.append(f"  - {c_type:<20}: {count:>5} ({pct:>5.1f}%)")
    lines.append("")

    lines.append("------------------------------------------------------------------")
    lines.append("CHUNKS PER DOCUMENT")
    lines.append("------------------------------------------------------------------")
    for doc_id, count in sorted(report.chunks_per_document.items()):
        lines.append(f"  * {doc_id:<40}: {count:>5} chunks")
    lines.append("")

    if report.warnings:
        lines.append("------------------------------------------------------------------")
        lines.append("VALIDATION WARNINGS")
        lines.append("------------------------------------------------------------------")
        for warn in report.warnings[:20]:
            lines.append(f"  [!] {warn}")
        if len(report.warnings) > 20:
            lines.append(f"  ... and {len(report.warnings) - 20} more warnings.")
        lines.append("")

    if report.errors:
        lines.append("------------------------------------------------------------------")
        lines.append("VALIDATION ERRORS")
        lines.append("------------------------------------------------------------------")
        for err in report.errors:
            lines.append(f"  [ERROR] {err}")
        lines.append("")

    lines.append("==================================================================")
    lines.append("                       END OF REPORT")
    lines.append("==================================================================")
    return "\n".join(lines)


def run_chunking(
    processed_dir: Path,
    chunks_dir: Path,
    metadata_dir: Path,
    max_chunk_chars: int = 3500,
    force: bool = False,
    verbose: bool = False,
) -> ChunkingReport:
    """Executes legal chunking across all processed JSON documents."""
    start_time = time.time()
    chunks_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(list(processed_dir.glob("*.json")))
    if not json_files:
        print(f"No processed JSON documents found in {processed_dir.resolve()}.", file=sys.stderr)
        return ChunkingReport()

    print(f"\n==================================================")
    print(f"ChatLaw Legal-Aware Chunking Pipeline (Phase RAG-02)")
    print(f"==================================================")
    print(f"Input Directory:    {processed_dir.resolve()}")
    print(f"Chunks Directory:   {chunks_dir.resolve()}")
    print(f"Metadata Directory: {metadata_dir.resolve()}")
    print(f"Max Chunk Chars:    {max_chunk_chars}")
    print(f"==================================================\n")

    chunker = LegalChunker(max_chunk_chars=max_chunk_chars)
    validator = ChunkValidator()

    total_chunks = 0
    chunks_per_doc: Dict[str, int] = {}
    chunks_by_type: Dict[str, int] = {}
    all_char_lengths: List[int] = []
    oversized_count = 0
    continuation_count = 0
    fallback_count = 0
    all_warnings: List[str] = []
    all_errors: List[Dict[str, str]] = []
    documents_summary: List[Dict] = []

    progress = tqdm(json_files, desc="Chunking Legal Documents", unit="doc")

    for doc_path in progress:
        progress.set_postfix({"file": doc_path.stem[:25]})
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_dict = json.load(f)
            doc_data = DocumentData.model_validate(doc_dict)

            # Chunk document
            doc_chunks = chunker.chunk_document(doc_data)

            # Validate generated chunks
            warnings, errors = validator.validate_chunks(doc_chunks)
            all_warnings.extend([f"[{doc_data.document_id}] {w}" for w in warnings])
            all_errors.extend(errors)

            # Write JSONL output
            out_jsonl = chunks_dir / f"{doc_data.document_id}.jsonl"
            with open(out_jsonl, "w", encoding="utf-8") as f:
                for c in doc_chunks:
                    f.write(c.model_dump_json() + "\n")

            # Accumulate statistics
            doc_chunk_count = len(doc_chunks)
            total_chunks += doc_chunk_count
            chunks_per_doc[doc_data.document_id] = doc_chunk_count

            for c in doc_chunks:
                c_type_val = c.chunk_type.value
                chunks_by_type[c_type_val] = chunks_by_type.get(c_type_val, 0) + 1
                all_char_lengths.append(c.character_count)
                if c.is_continuation:
                    continuation_count += 1
                if c.total_parts > 1 and c.chunk_part == 1:
                    oversized_count += 1
                if c.chunk_type == ChunkType.FALLBACK:
                    fallback_count += 1

            documents_summary.append({
                "document_id": doc_data.document_id,
                "document_title": doc_data.detected_act_title,
                "page_count": doc_data.page_count,
                "chunks_generated": doc_chunk_count,
                "jsonl_path": str(out_jsonl.resolve()),
            })

            if verbose:
                print(f"Chunked: {doc_data.document_id} -> {doc_chunk_count} chunks saved to {out_jsonl.name}")

        except Exception as e:
            err_msg = str(e)
            all_errors.append({"document": doc_path.name, "error": err_msg})
            print(f"\n[ERROR] Failed chunking {doc_path.name}: {err_msg}", file=sys.stderr)

    duration = time.time() - start_time
    avg_chars = statistics.mean(all_char_lengths) if all_char_lengths else 0.0
    med_chars = statistics.median(all_char_lengths) if all_char_lengths else 0.0
    min_chars = min(all_char_lengths) if all_char_lengths else 0
    max_chars = max(all_char_lengths) if all_char_lengths else 0

    report = ChunkingReport(
        report_timestamp_iso=datetime.now(timezone.utc).isoformat(),
        documents_processed=len(json_files),
        total_chunks=total_chunks,
        chunks_per_document=chunks_per_doc,
        chunks_by_type=chunks_by_type,
        avg_characters_per_chunk=round(avg_chars, 2),
        median_characters_per_chunk=round(med_chars, 2),
        min_characters_per_chunk=min_chars,
        max_characters_per_chunk=max_chars,
        oversized_chunks_count=oversized_count,
        fallback_chunks_count=fallback_count,
        continuation_chunks_count=continuation_count,
        warnings=all_warnings,
        errors=all_errors,
        processing_duration_seconds=round(duration, 2),
        documents_summary=documents_summary,
    )

    # Save reports
    report_json_path = metadata_dir / "chunking_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    report_txt_path = metadata_dir / "chunking_report.txt"
    human_report = format_human_chunking_report(report)
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write(human_report)

    print("\n" + human_report)
    print(f"\nChunking Report JSON saved to: {report_json_path}")
    print(f"Chunking Report Text saved to: {report_txt_path}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="ChatLaw Legal-Aware Chunking Pipeline Runner (Phase RAG-02)."
    )
    default_proc, default_chunks, default_meta = resolve_default_paths(rag_engine_dir)

    parser.add_argument(
        "--processed-dir", "-p",
        type=Path,
        default=default_proc,
        help=f"Directory containing structured JSON documents (default: {default_proc})"
    )
    parser.add_argument(
        "--chunks-dir", "-c",
        type=Path,
        default=default_chunks,
        help=f"Directory to save output JSONL chunks (default: {default_chunks})"
    )
    parser.add_argument(
        "--metadata-dir", "-m",
        type=Path,
        default=default_meta,
        help=f"Directory to save chunking reports (default: {default_meta})"
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=3500,
        help="Maximum safe characters per chunk (default: 3500)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-chunking and overwriting existing JSONL files."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output logging."
    )

    args = parser.parse_args()

    run_chunking(
        processed_dir=args.processed_dir,
        chunks_dir=args.chunks_dir,
        metadata_dir=args.metadata_dir,
        max_chunk_chars=args.max_chars,
        force=args.force,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
