#!/usr/bin/env python3
"""ChatLaw Corpus Ingestion Script.

Discovers, hashes, parses, cleans, analyzes quality, detects legal structure,
and saves structured JSONs, metadata, and corpus reports.
"""

import argparse
import json
import os
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

from ingestion.loaders.pdf_loader import PDFLoader
from ingestion.parsers.pdf_parser import PDFParser
from ingestion.models import (
    CorpusIngestionReport,
    DocumentData,
    DocumentMetadata,
    QualityFlag,
)


def resolve_default_paths(base_dir: Path):
    """Resolves default input and output paths relative to rag-engine."""
    # Check if ../Law_files exists, or ./Law_files
    candidate_law_files = [
        base_dir.parent / "Law_files",
        base_dir / "Law_files",
        Path("Law_files"),
        Path("../Law_files"),
    ]
    input_dir = None
    for cand in candidate_law_files:
        if cand.exists() and cand.is_dir():
            input_dir = cand
            break
    if input_dir is None:
        input_dir = base_dir.parent / "Law_files"

    processed_dir = base_dir / "data" / "processed"
    metadata_dir = base_dir / "data" / "metadata"

    return input_dir, processed_dir, metadata_dir


def format_human_report(report: CorpusIngestionReport) -> str:
    """Formats the corpus ingestion report into a clean human-readable text document."""
    lines = [
        "==================================================================",
        "             CHATLAW CORPUS INGESTION REPORT",
        "==================================================================",
        f"Report Generated:     {report.report_timestamp_iso}",
        f"Processing Duration:  {report.processing_duration_seconds:.2f} seconds",
        "",
        "------------------------------------------------------------------",
        "SUMMARY METRICS",
        "------------------------------------------------------------------",
        f"Files Discovered:         {report.total_files_discovered}",
        f"Successfully Processed:   {report.successfully_processed}",
        f"Failed Files:             {report.failed_files}",
        f"OCR Required:             {report.ocr_required_count}",
        "",
        f"Total Pages:              {report.total_pages:,}",
        f"Total Characters:         {report.total_characters:,}",
        f"Total Words:              {report.total_words:,}",
        f"Average Pages / Document: {report.avg_pages_per_doc:.1f}",
        "",
    ]

    if report.duplicate_hashes:
        lines.append("------------------------------------------------------------------")
        lines.append("DUPLICATE FILES DETECTED (BY SHA-256)")
        lines.append("------------------------------------------------------------------")
        for dup in report.duplicate_hashes:
            lines.append(f"  - SHA256: {dup}")
        lines.append("")

    if report.warnings:
        lines.append("------------------------------------------------------------------")
        lines.append("WARNINGS & QUALITY FLAGS")
        lines.append("------------------------------------------------------------------")
        for warn in report.warnings:
            lines.append(f"  [!] {warn}")
        lines.append("")

    if report.errors:
        lines.append("------------------------------------------------------------------")
        lines.append("PROCESSING ERRORS")
        lines.append("------------------------------------------------------------------")
        for err in report.errors:
            lines.append(f"  [ERROR] {err.get('file')}: {err.get('error')}")
        lines.append("")

    lines.append("------------------------------------------------------------------")
    lines.append("PROCESSED DOCUMENTS BREAKDOWN")
    lines.append("------------------------------------------------------------------")
    for doc in report.documents_summary:
        lines.append(
            f"  * Document ID: {doc.get('document_id')}\n"
            f"    File:        {doc.get('filename')} ({doc.get('file_size_bytes', 0):,} bytes)\n"
            f"    Act Title:   {doc.get('detected_act_title') or 'N/A'}\n"
            f"    Pages:       {doc.get('page_count')} | Words: {doc.get('total_words', 0):,} | Chars: {doc.get('total_characters', 0):,}\n"
            f"    Coverage:    {doc.get('text_coverage', 0.0):.1%} | Quality Score: {doc.get('quality_score', 1.0):.2f}\n"
            f"    OCR Status:  {'OCR_REQUIRED' if doc.get('ocr_required') else 'OK'}\n"
            f"    Flags:       {', '.join(doc.get('quality_flags', []))}\n"
            f"    SHA256:      {doc.get('sha256')}\n"
        )

    lines.append("==================================================================")
    lines.append("                       END OF REPORT")
    lines.append("==================================================================")
    return "\n".join(lines)


def run_ingestion(
    input_path: Path,
    output_path: Path,
    metadata_path: Path,
    force: bool = False,
    verbose: bool = False,
) -> CorpusIngestionReport:
    """Executes the full corpus ingestion workflow."""
    start_time = time.time()
    output_path.mkdir(parents=True, exist_ok=True)
    metadata_path.mkdir(parents=True, exist_ok=True)

    print(f"\n==================================================")
    print(f"ChatLaw RAG Engine - Ingestion Pipeline (Phase RAG-01)")
    print(f"==================================================")
    print(f"Input Directory:    {input_path.resolve()}")
    print(f"Output Directory:   {output_path.resolve()}")
    print(f"Metadata Directory: {metadata_path.resolve()}")
    print(f"Force Overwrite:    {force}")
    print(f"==================================================\n")

    loader = PDFLoader(root_dir=input_path)
    file_infos, duplicate_hashes = loader.load_corpus_metadata()

    print(f"Discovered {len(file_infos)} PDF document(s).")
    if duplicate_hashes:
        print(f"Found {len(duplicate_hashes)} duplicate SHA-256 hash(es).")

    parser = PDFParser()

    successful_count = 0
    failed_count = 0
    ocr_required_count = 0
    total_pages = 0
    total_chars = 0
    total_words = 0
    documents_summary: List[Dict] = []
    errors: List[Dict[str, str]] = []
    warnings: List[str] = []

    if duplicate_hashes:
        warnings.append(f"Corpus contains {len(duplicate_hashes)} duplicate SHA-256 file hashes.")

    progress = tqdm(file_infos, desc="Ingesting PDFs", unit="doc")

    for file_info in progress:
        progress.set_postfix({"file": file_info.filename[:25]})
        try:
            doc_id = PDFLoader.generate_document_id(file_info.filename, file_info.sha256)
            out_file = output_path / f"{doc_id}.json"
            meta_file = metadata_path / f"{doc_id}.meta.json"

            if out_file.exists() and meta_file.exists() and not force:
                if verbose:
                    print(f"Skipping existing document {doc_id} (use --force to overwrite)")
                with open(out_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                successful_count += 1
                q = existing_data.get("extraction_quality", {})
                p_count = existing_data.get("page_count", 0)
                total_pages += p_count
                total_chars += q.get("total_characters", 0)
                total_words += q.get("total_words", 0)
                if q.get("ocr_required", False):
                    ocr_required_count += 1
                documents_summary.append({
                    "document_id": existing_data.get("document_id"),
                    "filename": existing_data.get("filename"),
                    "file_size_bytes": existing_data.get("file_size_bytes"),
                    "sha256": existing_data.get("sha256"),
                    "page_count": p_count,
                    "detected_act_title": existing_data.get("detected_act_title"),
                    "ocr_required": q.get("ocr_required", False),
                    "quality_flags": q.get("flags", []),
                    "quality_score": q.get("quality_score", 1.0),
                    "total_characters": q.get("total_characters", 0),
                    "total_words": q.get("total_words", 0),
                    "text_coverage": q.get("text_coverage", 0.0),
                })
                continue

            # Parse PDF
            doc_data: DocumentData = parser.parse_pdf(file_info)
            doc_meta: DocumentMetadata = parser.extract_document_metadata(doc_data)

            # Save full document JSON
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(doc_data.model_dump_json(indent=2))

            # Save document metadata JSON
            with open(meta_file, "w", encoding="utf-8") as f:
                f.write(doc_meta.model_dump_json(indent=2))

            successful_count += 1
            total_pages += doc_data.page_count
            total_chars += doc_data.extraction_quality.total_characters
            total_words += doc_data.extraction_quality.total_words

            if doc_data.extraction_quality.ocr_required:
                ocr_required_count += 1
                warnings.append(f"Document '{file_info.filename}' requires OCR.")

            for flag in doc_data.extraction_quality.flags:
                if flag not in (QualityFlag.OK, QualityFlag.OCR_REQUIRED):
                    warnings.append(f"Document '{file_info.filename}' flagged with {flag.value}.")

            documents_summary.append({
                "document_id": doc_data.document_id,
                "filename": doc_data.filename,
                "file_size_bytes": doc_data.file_size_bytes,
                "sha256": doc_data.sha256,
                "page_count": doc_data.page_count,
                "detected_act_title": doc_data.detected_act_title,
                "ocr_required": doc_data.extraction_quality.ocr_required,
                "quality_flags": [fl.value for fl in doc_data.extraction_quality.flags],
                "quality_score": doc_data.extraction_quality.quality_score,
                "total_characters": doc_data.extraction_quality.total_characters,
                "total_words": doc_data.extraction_quality.total_words,
                "text_coverage": doc_data.extraction_quality.text_coverage,
            })

            if verbose:
                print(f"Processed: {doc_data.filename} -> {doc_data.page_count} pages, {doc_data.extraction_quality.total_words:,} words")

        except Exception as e:
            failed_count += 1
            err_msg = str(e)
            errors.append({"file": file_info.filename, "error": err_msg})
            print(f"\n[ERROR] Failed processing {file_info.filename}: {err_msg}", file=sys.stderr)

    duration = time.time() - start_time
    avg_pages = (total_pages / len(file_infos)) if file_infos else 0.0

    report = CorpusIngestionReport(
        report_timestamp_iso=datetime.now(timezone.utc).isoformat(),
        total_files_discovered=len(file_infos),
        successfully_processed=successful_count,
        failed_files=failed_count,
        ocr_required_count=ocr_required_count,
        total_pages=total_pages,
        total_characters=total_chars,
        total_words=total_words,
        avg_pages_per_doc=round(avg_pages, 2),
        processing_duration_seconds=round(duration, 2),
        duplicate_hashes=duplicate_hashes,
        errors=errors,
        warnings=warnings,
        documents_summary=documents_summary,
    )

    # Save reports
    report_json_path = metadata_path / "ingestion_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    report_txt_path = metadata_path / "ingestion_report.txt"
    human_report = format_human_report(report)
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write(human_report)

    print("\n" + human_report)
    print(f"\nReport JSON saved to: {report_json_path}")
    print(f"Report Text saved to: {report_txt_path}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="ChatLaw Ingestion Pipeline (Phase RAG-01): PDF discovery, hashing, page extraction, quality analysis, cleaning, structure detection, and report generation."
    )
    default_in, default_out, default_meta = resolve_default_paths(rag_engine_dir)

    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=default_in,
        help=f"Directory containing source PDF files (default: {default_in})"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=default_out,
        help=f"Directory to save processed JSON documents (default: {default_out})"
    )
    parser.add_argument(
        "--metadata-dir", "-m",
        type=Path,
        default=default_meta,
        help=f"Directory to save metadata files and ingestion reports (default: {default_meta})"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-processing and overwriting of existing output JSON documents."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable detailed verbose output."
    )

    args = parser.parse_args()

    run_ingestion(
        input_path=args.input,
        output_path=args.output,
        metadata_path=args.metadata_dir,
        force=args.force,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
