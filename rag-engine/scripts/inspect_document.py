#!/usr/bin/env python3
"""ChatLaw Document Inspection Utility.

Allows inspecting raw PDFs or processed JSON documents to review extraction quality,
cleaning diffs, and detected legal structure hierarchy.
"""

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

script_dir = Path(__file__).resolve().parent
rag_engine_dir = script_dir.parent
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))

from ingestion.loaders.pdf_loader import PDFLoader
from ingestion.parsers.pdf_parser import PDFParser
from ingestion.models import DocumentData


def inspect_document(
    input_file: Path,
    page_num: Optional[int] = None,
    structure_only: bool = False,
    quality_only: bool = False,
    show_diff: bool = False,
):
    """Inspects a PDF or processed JSON document."""
    input_path = Path(input_file).resolve()
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    doc_data: DocumentData

    if input_path.suffix.lower() == ".json":
        with open(input_path, "r", encoding="utf-8") as f:
            data_dict = json.load(f)
            doc_data = DocumentData.model_validate(data_dict)
    elif input_path.suffix.lower() == ".pdf":
        loader = PDFLoader(root_dir=input_path.parent)
        file_info = loader.get_file_info(input_path)
        parser = PDFParser()
        print("Parsing PDF on-the-fly for inspection...")
        doc_data = parser.parse_pdf(file_info)
    else:
        print(f"Unsupported file format: {input_path.suffix} (expected .pdf or .json)", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 70)
    print("                    CHATLAW DOCUMENT INSPECTION")
    print("=" * 70)
    print(f"Document ID:      {doc_data.document_id}")
    print(f"Filename:         {doc_data.filename}")
    print(f"Source Path:      {doc_data.source_path}")
    print(f"SHA-256:          {doc_data.sha256}")
    print(f"File Size:        {doc_data.file_size_bytes:,} bytes")
    print(f"Total Pages:      {doc_data.page_count}")
    print(f"Detected Act:     {doc_data.detected_act_title or 'None'}")
    print(f"Processing Date:  {doc_data.processing_timestamp_iso}")

    # Extraction Quality
    q = doc_data.extraction_quality
    print("\n" + "-" * 70)
    print("EXTRACTION QUALITY ANALYSIS")
    print("-" * 70)
    print(f"Quality Score:    {q.quality_score:.2f} / 1.00")
    print(f"OCR Status:       {'OCR_REQUIRED [!]' if q.ocr_required else 'TEXT EXTRACTABLE [OK]'}")
    print(f"Flags:            {', '.join([f.value for f in q.flags])}")
    print(f"Text Coverage:    {q.text_coverage:.1%} ({q.pages_with_text}/{doc_data.page_count} pages)")
    print(f"Total Characters: {q.total_characters:,} (avg {q.avg_chars_per_page:.1f}/page)")
    print(f"Total Words:      {q.total_words:,} (avg {q.avg_words_per_page:.1f}/page)")
    if q.notes:
        print("Quality Notes:")
        for note in q.notes:
            print(f"  * {note}")

    if doc_data.repeated_headers:
        print("\nRepeated Headers Detected:")
        for h in doc_data.repeated_headers[:5]:
            print(f"  [Header] {h}")

    if doc_data.repeated_footers:
        print("\nRepeated Footers Detected:")
        for f_line in doc_data.repeated_footers[:5]:
            print(f"  [Footer] {f_line}")

    if quality_only:
        print("=" * 70 + "\n")
        return

    # Structure Overview
    all_units = []
    unit_counts = {}
    for p in doc_data.pages:
        for u in p.detected_structure:
            all_units.append((p.page_number, u))
            unit_counts[u.unit_type.value] = unit_counts.get(u.unit_type.value, 0) + 1

    print("\n" + "-" * 70)
    print("LEGAL STRUCTURE SUMMARY")
    print("-" * 70)
    for u_type, count in sorted(unit_counts.items()):
        print(f"  - {u_type:<20}: {count} detected")

    if structure_only and page_num is None:
        print("\nDetected Structural Units (first 30):")
        for pno, u in all_units[:30]:
            id_str = f"[{u.identifier}]" if u.identifier else ""
            title_str = f"- {u.title}" if u.title else ""
            print(f"  Page {pno:3d} | Line {u.line_number or 0:2d} | {u.unit_type.value:<15} {id_str:<15} {title_str[:35]}")
        if len(all_units) > 30:
            print(f"  ... and {len(all_units) - 30} more units.")
        print("=" * 70 + "\n")
        return

    # Page-Specific Inspection
    if page_num is not None:
        if page_num < 1 or page_num > doc_data.page_count:
            print(f"\nError: Requested page {page_num} is out of bounds (1-{doc_data.page_count})", file=sys.stderr)
            sys.exit(1)

        page_data = doc_data.pages[page_num - 1]
        print("\n" + "=" * 70)
        print(f"PAGE {page_num} DETAILS")
        print("=" * 70)
        print(f"Characters: {page_data.character_count} | Words: {page_data.word_count} | Lines: {page_data.line_count}")

        if page_data.repeated_headers:
            print(f"Headers: {page_data.repeated_headers}")
        if page_data.repeated_footers:
            print(f"Footers: {page_data.repeated_footers}")

        print("\nDetected Legal Units on Page:")
        if page_data.detected_structure:
            for u in page_data.detected_structure:
                id_str = f"[{u.identifier}]" if u.identifier else ""
                title_str = f"- {u.title}" if u.title else ""
                print(f"  * Line {u.line_number or 0:2d} | {u.unit_type.value:<14} {id_str:<12} {title_str}")
        else:
            print("  (No legal units detected on this page)")

        if show_diff:
            print("\n" + "-" * 70)
            print("DIFF: RAW TEXT VS CLEANED TEXT")
            print("-" * 70)
            raw_lines = page_data.raw_text.splitlines(keepends=True)
            clean_lines = page_data.cleaned_text.splitlines(keepends=True)
            diff = difflib.unified_diff(raw_lines, clean_lines, fromfile="raw_text", tofile="cleaned_text")
            diff_text = "".join(diff)
            if diff_text:
                print(diff_text)
            else:
                print("(Raw text and cleaned text are identical)")
        else:
            print("\n" + "-" * 70)
            print("CLEANED TEXT PREVIEW:")
            print("-" * 70)
            print(page_data.cleaned_text[:1200])
            if len(page_data.cleaned_text) > 1200:
                print(f"\n... [Truncated {len(page_data.cleaned_text) - 1200} characters]")

    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="ChatLaw Document Inspector: Review extraction, quality, and legal structure."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to raw PDF file or processed JSON document."
    )
    parser.add_argument(
        "--page", "-p",
        type=int,
        default=None,
        help="Optional 1-indexed page number to inspect in detail."
    )
    parser.add_argument(
        "--structure-only", "-s",
        action="store_true",
        help="Display only the detected legal structure units."
    )
    parser.add_argument(
        "--quality-only", "-q",
        action="store_true",
        help="Display only the extraction quality report."
    )
    parser.add_argument(
        "--diff", "-d",
        action="store_true",
        help="Show diff between raw text and cleaned text for the inspected page."
    )

    args = parser.parse_args()
    inspect_document(
        input_file=args.input,
        page_num=args.page,
        structure_only=args.structure_only,
        quality_only=args.quality_only,
        show_diff=args.diff,
    )


if __name__ == "__main__":
    main()
