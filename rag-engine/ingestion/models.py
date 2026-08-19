"""Data models for ChatLaw ingestion pipeline."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QualityFlag(str, Enum):
    """Flags indicating potential document extraction quality issues."""
    OK = "OK"
    OCR_REQUIRED = "OCR_REQUIRED"
    EXTREMELY_LOW_CHARACTER_COUNT = "EXTREMELY_LOW_CHARACTER_COUNT"
    MOSTLY_EMPTY_PAGES = "MOSTLY_EMPTY_PAGES"
    REPEATED_GARBAGE_CHARACTERS = "REPEATED_GARBAGE_CHARACTERS"
    ABNORMAL_TEXT_DENSITY = "ABNORMAL_TEXT_DENSITY"


class StructuralUnitType(str, Enum):
    """Types of legal structural units in Indian statutes."""
    ACT_TITLE = "ACT_TITLE"
    PREAMBLE = "PREAMBLE"
    ENACTING_FORMULA = "ENACTING_FORMULA"
    PART = "PART"
    CHAPTER = "CHAPTER"
    SECTION = "SECTION"
    SUBSECTION = "SUBSECTION"
    CLAUSE = "CLAUSE"
    SUBCLAUSE = "SUBCLAUSE"
    PROVISO = "PROVISO"
    EXPLANATION = "EXPLANATION"
    ILLUSTRATION = "ILLUSTRATION"
    DEFINITION = "DEFINITION"
    SCHEDULE = "SCHEDULE"
    RULE = "RULE"
    REGULATION = "REGULATION"
    STATEMENT_OF_OBJECTS = "STATEMENT_OF_OBJECTS"
    UNKNOWN = "UNKNOWN"


class StructuralUnit(BaseModel):
    """A detected legal structural unit within a document page."""
    unit_type: StructuralUnitType
    identifier: Optional[str] = Field(
        default=None,
        description="The formal identifier e.g. '103', 'CHAPTER III', 'PART I', '(1)', '(a)', 'Explanation 1'"
    )
    title: Optional[str] = Field(
        default=None,
        description="Title or heading associated with the unit, if any"
    )
    line_number: Optional[int] = Field(
        default=None,
        description="1-indexed line number where the unit begins on this page"
    )
    start_char: Optional[int] = Field(
        default=None,
        description="Start character index within the page text"
    )
    end_char: Optional[int] = Field(
        default=None,
        description="End character index within the page text"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Detection confidence score"
    )
    raw_match: Optional[str] = Field(
        default=None,
        description="Exact raw text fragment that matched the structural pattern"
    )


class FileHashInfo(BaseModel):
    """File metadata and cryptographic hash information."""
    filename: str
    relative_path: str
    absolute_path: str
    file_size_bytes: int
    sha256: str
    modified_at_iso: str


class ExtractionQuality(BaseModel):
    """Statistical and quality metrics for PDF text extraction."""
    total_characters: int = 0
    total_words: int = 0
    total_lines: int = 0
    pages_with_text: int = 0
    pages_without_text: int = 0
    text_coverage: float = Field(
        default=0.0,
        description="Ratio of pages containing text to total pages (0.0 to 1.0)"
    )
    avg_chars_per_page: float = 0.0
    avg_words_per_page: float = 0.0
    ocr_required: bool = False
    flags: List[QualityFlag] = Field(default_factory=list)
    quality_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall extraction quality score (1.0 = pristine, 0.0 = unreadable)"
    )
    notes: List[str] = Field(default_factory=list)


class PageData(BaseModel):
    """Structured data extracted from a single PDF page."""
    page_number: int = Field(description="1-indexed physical page number")
    raw_text: str = Field(description="Unaltered text as extracted from the PDF")
    cleaned_text: str = Field(description="Conservatively cleaned and normalized text")
    character_count: int = Field(default=0)
    word_count: int = Field(default=0)
    line_count: int = Field(default=0)
    detected_structure: List[StructuralUnit] = Field(default_factory=list)
    repeated_headers: List[str] = Field(default_factory=list)
    repeated_footers: List[str] = Field(default_factory=list)


class DocumentData(BaseModel):
    """Full structured representation of a processed legal document."""
    document_id: str
    filename: str
    source_path: str
    sha256: str
    file_size_bytes: int
    page_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_quality: ExtractionQuality
    pages: List[PageData] = Field(default_factory=list)
    detected_act_title: Optional[str] = None
    repeated_headers: List[str] = Field(default_factory=list)
    repeated_footers: List[str] = Field(default_factory=list)
    processing_timestamp_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class DocumentMetadata(BaseModel):
    """Compact metadata record stored alongside processed data."""
    document_id: str
    filename: str
    source_path: str
    sha256: str
    file_size_bytes: int
    page_count: int
    detected_act_title: Optional[str] = None
    extraction_status: str = "COMPLETED"  # COMPLETED | FAILED | OCR_REQUIRED
    ocr_required: bool = False
    quality_flags: List[QualityFlag] = Field(default_factory=list)
    quality_score: float = 1.0
    total_characters: int = 0
    total_words: int = 0
    avg_chars_per_page: float = 0.0
    text_coverage: float = 0.0
    processing_timestamp_iso: str
    metadata_fields: Dict[str, Any] = Field(default_factory=dict)


class CorpusIngestionReport(BaseModel):
    """Corpus-level summary of the ingestion run."""
    report_timestamp_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_files_discovered: int = 0
    successfully_processed: int = 0
    failed_files: int = 0
    ocr_required_count: int = 0
    total_pages: int = 0
    total_characters: int = 0
    total_words: int = 0
    avg_pages_per_doc: float = 0.0
    processing_duration_seconds: float = 0.0
    duplicate_hashes: List[str] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    documents_summary: List[Dict[str, Any]] = Field(default_factory=list)
