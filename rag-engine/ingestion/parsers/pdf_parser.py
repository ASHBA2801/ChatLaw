"""PDF Parser, Quality Analyzer, and Document Assembler using PyMuPDF."""

import os
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple
import pymupdf

from ..cleaners.text_cleaner import HeaderFooterDetector, TextCleaner
from ..loaders.pdf_loader import FileHashInfo, PDFLoader
from ..models import (
    DocumentData,
    DocumentMetadata,
    ExtractionQuality,
    PageData,
    QualityFlag,
)
from ..structure.legal_structure import LegalStructureDetector


def _ocr_enabled() -> bool:
    return os.getenv("ENABLE_PDF_OCR", "").strip().lower() in {"1", "true", "yes"}


class PDFParser:
    """Extracts, cleans, analyzes, and structures PDF documents page-by-page."""

    def __init__(
        self,
        cleaner: Optional[TextCleaner] = None,
        header_footer_detector: Optional[HeaderFooterDetector] = None,
        structure_detector: Optional[LegalStructureDetector] = None,
        enable_ocr: Optional[bool] = None,
    ):
        self.cleaner = cleaner or TextCleaner()
        self.header_footer_detector = header_footer_detector or HeaderFooterDetector()
        self.structure_detector = structure_detector or LegalStructureDetector()
        self.enable_ocr = _ocr_enabled() if enable_ocr is None else enable_ocr

    def _extract_page_text(self, page: "pymupdf.Page") -> str:
        """Extract text; optionally OCR when native text layer is empty."""
        raw_text = page.get_text() or ""
        if raw_text.strip() or not self.enable_ocr:
            return raw_text
        try:
            # Requires a local Tesseract installation (PyMuPDF OCR backend).
            tp = page.get_textpage_ocr(dpi=200, full=True)
            return page.get_text(textpage=tp) or ""
        except Exception:
            return raw_text

    def parse_pdf(self, file_info: FileHashInfo) -> DocumentData:
        """Parses a PDF file into a full structured DocumentData object.
        
        Args:
            file_info: FileHashInfo metadata containing file paths and SHA-256 hash.
            
        Returns:
            Fully populated DocumentData model.
            
        Raises:
            Exception: If PDF cannot be opened or parsed.
        """
        pdf_path = Path(file_info.absolute_path)
        doc = pymupdf.open(pdf_path)
        page_count = len(doc)

        raw_pages_text: List[str] = []
        pages_data: List[PageData] = []

        # 1. Page-by-page raw extraction
        for pno in range(page_count):
            page = doc[pno]
            raw_text = self._extract_page_text(page)
            raw_pages_text.append(raw_text)

        doc.close()

        # 2. Document-level header / footer detection
        repeated_headers, repeated_footers = self.header_footer_detector.detect(raw_pages_text)

        # 3. Detect canonical Act Title
        detected_act_title = self.structure_detector.detect_document_act_title(raw_pages_text)

        # 4. Process each page (clean, structure, annotate)
        for pno, raw_text in enumerate(raw_pages_text):
            cleaned_text = self.cleaner.clean_text(raw_text)
            char_count = len(cleaned_text)
            words = cleaned_text.split()
            word_count = len(words)
            lines = [l for l in cleaned_text.split('\n') if l.strip()]
            line_count = len(lines)

            # Structure detection on cleaned text
            detected_units = self.structure_detector.detect_units_on_page(
                page_text=cleaned_text,
                page_number=pno + 1
            )

            # Page header/footer annotation
            page_headers, page_footers = self.header_footer_detector.annotate_page(
                raw_text,
                repeated_headers,
                repeated_footers
            )

            pages_data.append(
                PageData(
                    page_number=pno + 1,
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                    character_count=char_count,
                    word_count=word_count,
                    line_count=line_count,
                    detected_structure=detected_units,
                    repeated_headers=page_headers,
                    repeated_footers=page_footers,
                )
            )

        # 5. Extraction Quality Analysis
        quality = self.analyze_extraction_quality(pages_data, page_count)

        # 6. Generate document ID
        doc_id = PDFLoader.generate_document_id(file_info.filename, file_info.sha256)

        return DocumentData(
            document_id=doc_id,
            filename=file_info.filename,
            source_path=file_info.relative_path,
            sha256=file_info.sha256,
            file_size_bytes=file_info.file_size_bytes,
            page_count=page_count,
            detected_act_title=detected_act_title,
            metadata={
                "modified_at_iso": file_info.modified_at_iso,
                "detected_act_title": detected_act_title,
            },
            extraction_quality=quality,
            pages=pages_data,
            repeated_headers=repeated_headers,
            repeated_footers=repeated_footers,
        )

    def analyze_extraction_quality(self, pages: List[PageData], page_count: int) -> ExtractionQuality:
        """Calculates comprehensive extraction quality metrics and flags issues."""
        total_chars = sum(p.character_count for p in pages)
        total_words = sum(p.word_count for p in pages)
        total_lines = sum(p.line_count for p in pages)

        pages_with_text = sum(1 for p in pages if p.character_count >= 20)
        pages_without_text = page_count - pages_with_text

        text_coverage = (pages_with_text / page_count) if page_count > 0 else 0.0
        avg_chars = (total_chars / page_count) if page_count > 0 else 0.0
        avg_words = (total_words / page_count) if page_count > 0 else 0.0

        flags: List[QualityFlag] = []
        notes: List[str] = []
        quality_score = 1.0

        # Check OCR Requirement
        ocr_required = False
        if page_count > 0 and (text_coverage < 0.15 or avg_chars < 50):
            ocr_required = True
            flags.append(QualityFlag.OCR_REQUIRED)
            notes.append(f"Low text coverage ({text_coverage:.1%}) or average characters ({avg_chars:.1f}/page). OCR required.")
            quality_score -= 0.6

        # Check Extremely Low Character Count
        if page_count > 1 and avg_chars < 150 and not ocr_required:
            flags.append(QualityFlag.EXTREMELY_LOW_CHARACTER_COUNT)
            notes.append(f"Extremely low average character count: {avg_chars:.1f} chars/page.")
            quality_score -= 0.3

        # Check Mostly Empty Pages
        empty_page_ratio = (pages_without_text / page_count) if page_count > 0 else 1.0
        if empty_page_ratio > 0.50 and page_count > 2:
            flags.append(QualityFlag.MOSTLY_EMPTY_PAGES)
            notes.append(f"Over 50% of pages ({empty_page_ratio:.1%}) contain little or no text.")
            quality_score -= 0.3

        # Check Garbage Characters / Corrupted Text Layer
        garbage_detected = False
        for p in pages:
            if not p.raw_text:
                continue
            # Check replacement character (\ufffd) or excessive control/unprintable chars
            replacement_count = p.raw_text.count('\ufffd')
            # Check ratio of non-alphanumeric / non-punctuation glyphs
            if replacement_count > 10 or (p.character_count > 0 and (replacement_count / p.character_count) > 0.05):
                garbage_detected = True
                break

        if garbage_detected:
            flags.append(QualityFlag.REPEATED_GARBAGE_CHARACTERS)
            notes.append("High frequency of Unicode replacement or corrupted glyph characters detected.")
            quality_score -= 0.4

        # Check Abnormal Text Density
        if avg_chars > 9000 or (avg_chars < 40 and page_count > 0 and not ocr_required):
            flags.append(QualityFlag.ABNORMAL_TEXT_DENSITY)
            notes.append(f"Abnormal average character density: {avg_chars:.1f} chars/page.")
            quality_score -= 0.2

        if not flags:
            flags.append(QualityFlag.OK)

        quality_score = max(0.0, min(1.0, quality_score))

        return ExtractionQuality(
            total_characters=total_chars,
            total_words=total_words,
            total_lines=total_lines,
            pages_with_text=pages_with_text,
            pages_without_text=pages_without_text,
            text_coverage=round(text_coverage, 4),
            avg_chars_per_page=round(avg_chars, 2),
            avg_words_per_page=round(avg_words, 2),
            ocr_required=ocr_required,
            flags=flags,
            quality_score=round(quality_score, 2),
            notes=notes,
        )

    def extract_document_metadata(self, doc_data: DocumentData) -> DocumentMetadata:
        """Constructs a compact DocumentMetadata record from full DocumentData."""
        status = "COMPLETED"
        if doc_data.extraction_quality.ocr_required:
            status = "OCR_REQUIRED"

        return DocumentMetadata(
            document_id=doc_data.document_id,
            filename=doc_data.filename,
            source_path=doc_data.source_path,
            sha256=doc_data.sha256,
            file_size_bytes=doc_data.file_size_bytes,
            page_count=doc_data.page_count,
            detected_act_title=doc_data.detected_act_title,
            extraction_status=status,
            ocr_required=doc_data.extraction_quality.ocr_required,
            quality_flags=doc_data.extraction_quality.flags,
            quality_score=doc_data.extraction_quality.quality_score,
            total_characters=doc_data.extraction_quality.total_characters,
            total_words=doc_data.extraction_quality.total_words,
            avg_chars_per_page=doc_data.extraction_quality.avg_chars_per_page,
            text_coverage=doc_data.extraction_quality.text_coverage,
            processing_timestamp_iso=doc_data.processing_timestamp_iso,
            metadata_fields=doc_data.metadata,
        )
