"""Data models for legal-aware chunking pipeline (Phase RAG-02)."""

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChunkType(str, Enum):
    """Types of legal chunks representing distinct structural units."""
    ACT_PREAMBLE = "act_preamble"
    SECTION = "section"
    SUBSECTION = "subsection"
    CLAUSE = "clause"
    DEFINITION = "definition"
    PROVISO = "proviso"
    EXPLANATION = "explanation"
    ILLUSTRATION = "illustration"
    SCHEDULE = "schedule"
    FALLBACK = "fallback"
    CONTINUATION = "continuation"


class LegalHierarchy(BaseModel):
    """Explicit statutory hierarchy metadata for a legal chunk."""
    act_title: Optional[str] = None
    part: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    clause: Optional[str] = None
    subclause: Optional[str] = None
    schedule: Optional[str] = None
    heading: Optional[str] = None


class LegalChunk(BaseModel):
    """Deterministic, legally meaningful unit ready for downstream embedding."""
    chunk_id: str = Field(description="Deterministic unique chunk identifier")
    document_id: str = Field(description="Parent document identifier")
    document_title: Optional[str] = Field(default=None, description="Canonical title of the Act/document")
    document_sha256: str = Field(description="SHA-256 hash of the parent source PDF")
    chunk_hash: str = Field(description="SHA-256 content hash of the chunk text")
    chunk_type: ChunkType = Field(description="Structural category of the chunk")
    content: str = Field(description="Exact unaltered text of the legal unit")
    context_path: str = Field(description="Breadcrumb hierarchy path e.g. Act > Chapter > Section > Subsection")
    context_prefix: Optional[str] = Field(
        default=None,
        description="Minimal parent context heading string for downstream retrieval understanding"
    )

    # Hierarchy details
    part: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    clause: Optional[str] = None
    subclause: Optional[str] = None
    schedule: Optional[str] = None

    # Location
    page_start: int = Field(description="1-indexed physical page where this chunk begins")
    page_end: int = Field(description="1-indexed physical page where this chunk ends")

    # Sequence & Continuation
    chunk_index: int = Field(description="0-indexed global sequence order within the document")
    chunk_part: int = Field(default=1, description="1-indexed segment index when split across continuation chunks")
    total_parts: int = Field(default=1, description="Total split pieces if unit was partitioned")
    is_continuation: bool = Field(default=False, description="True if this chunk is a continued partition of an oversized unit")
    parent_chunk_id: Optional[str] = Field(
        default=None,
        description="Chunk ID of parent provision (e.g. parent section for a split subsection or proviso)"
    )

    # Metadata & Statistics
    character_count: int = Field(default=0)
    word_count: int = Field(default=0)
    line_count: int = Field(default=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def compute_content_hash(cls, content: str) -> str:
        """Computes SHA-256 hash of chunk content."""
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

    @classmethod
    def generate_chunk_id(
        cls,
        document_id: str,
        section_or_unit: Optional[str],
        chunk_type: ChunkType,
        page_start: int,
        chunk_index: int,
        chunk_part: int = 1,
    ) -> str:
        """Generates a clean deterministic chunk ID."""
        unit_label = (section_or_unit or chunk_type.value).replace(" ", "_")
        # Ensure safe alphanumeric characters
        safe_unit = "".join(c if (c.isalnum() or c in "_-.") else "_" for c in unit_label).strip("_")
        return f"{document_id}_p{page_start}_{safe_unit}_idx{chunk_index}_pt{chunk_part}"


class ChunkingReport(BaseModel):
    """Comprehensive report summarizing chunking execution across the corpus."""
    report_timestamp_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    documents_processed: int = 0
    total_chunks: int = 0
    chunks_per_document: Dict[str, int] = Field(default_factory=dict)
    chunks_by_type: Dict[str, int] = Field(default_factory=dict)
    
    # Text length statistics
    avg_characters_per_chunk: float = 0.0
    median_characters_per_chunk: float = 0.0
    min_characters_per_chunk: int = 0
    max_characters_per_chunk: int = 0

    # Categorical counts
    oversized_chunks_count: int = 0
    fallback_chunks_count: int = 0
    continuation_chunks_count: int = 0
    duplicate_chunk_hashes: List[str] = Field(default_factory=list)
    missing_hierarchy_count: int = 0

    warnings: List[str] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    processing_duration_seconds: float = 0.0
    documents_summary: List[Dict[str, Any]] = Field(default_factory=list)
