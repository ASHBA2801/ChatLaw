"""Deterministic Legal-Aware Document Chunker (Phase RAG-02)."""

import re
from typing import Dict, List, Optional, Tuple

from ..models import (
    DocumentData,
    PageData,
    StructuralUnit,
    StructuralUnitType,
)
from .hierarchy import HierarchyTracker
from .models import ChunkType, LegalChunk, LegalHierarchy
from .splitter import LegalSplitter


class LegalChunker:
    """Chunks structured legal documents into legally meaningful units with context hierarchy."""

    # Explicit section header pattern to detect when a line starts a new section
    SECTION_START_RE = re.compile(
        r'^\s*(\d{1,4}[A-Z]?)\.\s+(.*)$'
    )

    # Schedule header
    SCHEDULE_START_RE = re.compile(
        r'^\s*(THE\s+(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|\d+)?\s*SCHEDULE|THESCHEDULE)\b(?:\s*[-—–]\s*(.*))?',
        re.IGNORECASE
    )

    # Chapter header
    CHAPTER_START_RE = re.compile(
        r'^\s*(CHAPTER\s+([IVXLCDM\d]+))\b(?:\s*[-—–]\s*(.*))?',
        re.IGNORECASE
    )

    # Part header
    PART_START_RE = re.compile(
        r'^\s*(PART\s+([IVXLCDM\d]+))\b(?:\s*[-—–]\s*(.*))?',
        re.IGNORECASE
    )

    def __init__(
        self,
        max_chunk_chars: int = 3500,
        min_chunk_chars: int = 50,
        splitter: Optional[LegalSplitter] = None,
    ):
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars
        self.splitter = splitter or LegalSplitter(max_chunk_chars=max_chunk_chars)

    def chunk_document(self, document: DocumentData) -> List[LegalChunk]:
        """Processes a DocumentData instance and returns a deterministic list of LegalChunks."""
        chunks: List[LegalChunk] = []
        tracker = HierarchyTracker(act_title=document.detected_act_title)

        # 1. First extract and tag cross-page text blocks
        page_lines: List[Tuple[int, str]] = []  # List of (page_number, line_text)
        for page in document.pages:
            cleaned = page.cleaned_text
            if not cleaned:
                continue
            for line in cleaned.split('\n'):
                page_lines.append((page.page_number, line))

        if not page_lines:
            return []

        # 2. Iterate through lines, track statutory hierarchy, and group lines into units
        current_unit_lines: List[str] = []
        current_unit_pages: List[int] = []
        current_unit_type: ChunkType = ChunkType.FALLBACK
        current_unit_id: Optional[str] = None
        current_unit_title: Optional[str] = None
        current_hierarchy: LegalHierarchy = tracker.snapshot()

        chunk_counter = 0

        def emit_current_unit():
            nonlocal chunk_counter, current_unit_lines, current_unit_pages
            nonlocal current_unit_type, current_unit_id, current_unit_title, current_hierarchy

            if not current_unit_lines:
                return

            full_content = "\n".join(current_unit_lines).strip()
            if not full_content:
                current_unit_lines = []
                current_unit_pages = []
                return

            page_start = min(current_unit_pages)
            page_end = max(current_unit_pages)

            # Determine chunk type specifics (e.g. definition, preamble, schedule)
            assigned_type = current_unit_type
            if current_hierarchy.schedule and assigned_type != ChunkType.SCHEDULE:
                assigned_type = ChunkType.SCHEDULE
            elif not current_hierarchy.section and not current_hierarchy.schedule:
                if "An Act to" in full_content or "BE it enacted" in full_content:
                    assigned_type = ChunkType.ACT_PREAMBLE
                else:
                    assigned_type = ChunkType.FALLBACK

            # Check if unit contains definitions
            if '“' in full_content or '"' in full_content:
                if re.search(r'means\b|includes\b|shall have', full_content, re.IGNORECASE):
                    if current_hierarchy.section in ("2", "3", "2.", "3.") or "definition" in (current_unit_title or "").lower():
                        assigned_type = ChunkType.DEFINITION

            # Build context hierarchy
            context_path = tracker.build_context_path(current_hierarchy)
            context_prefix = tracker.build_context_prefix(current_hierarchy)

            # Handle potential oversized units
            if self.splitter.is_oversized(full_content):
                partitions = self.splitter.split_legal_unit(full_content)
                total_parts = len(partitions)
                parent_chunk_id = None

                for part_idx, part_text in enumerate(partitions, start=1):
                    is_cont = (part_idx > 1)
                    c_type = ChunkType.CONTINUATION if is_cont else assigned_type
                    c_id = LegalChunk.generate_chunk_id(
                        document_id=document.document_id,
                        section_or_unit=current_unit_id or current_hierarchy.section,
                        chunk_type=c_type,
                        page_start=page_start,
                        chunk_index=chunk_counter,
                        chunk_part=part_idx,
                    )
                    if part_idx == 1:
                        parent_chunk_id = c_id

                    words = part_text.split()
                    lines = [l for l in part_text.split('\n') if l.strip()]

                    chunk = LegalChunk(
                        chunk_id=c_id,
                        document_id=document.document_id,
                        document_title=document.detected_act_title,
                        document_sha256=document.sha256,
                        chunk_hash=LegalChunk.compute_content_hash(part_text),
                        chunk_type=c_type,
                        content=part_text,
                        context_path=context_path,
                        context_prefix=context_prefix,
                        part=current_hierarchy.part,
                        chapter=current_hierarchy.chapter,
                        section=current_hierarchy.section,
                        subsection=current_hierarchy.subsection,
                        clause=current_hierarchy.clause,
                        subclause=current_hierarchy.subclause,
                        schedule=current_hierarchy.schedule,
                        page_start=page_start,
                        page_end=page_end,
                        chunk_index=chunk_counter,
                        chunk_part=part_idx,
                        total_parts=total_parts,
                        is_continuation=is_cont,
                        parent_chunk_id=parent_chunk_id if is_cont else None,
                        character_count=len(part_text),
                        word_count=len(words),
                        line_count=len(lines),
                    )
                    chunks.append(chunk)
                    chunk_counter += 1
            else:
                words = full_content.split()
                lines = [l for l in full_content.split('\n') if l.strip()]
                c_id = LegalChunk.generate_chunk_id(
                    document_id=document.document_id,
                    section_or_unit=current_unit_id or current_hierarchy.section,
                    chunk_type=assigned_type,
                    page_start=page_start,
                    chunk_index=chunk_counter,
                    chunk_part=1,
                )

                chunk = LegalChunk(
                    chunk_id=c_id,
                    document_id=document.document_id,
                    document_title=document.detected_act_title,
                    document_sha256=document.sha256,
                    chunk_hash=LegalChunk.compute_content_hash(full_content),
                    chunk_type=assigned_type,
                    content=full_content,
                    context_path=context_path,
                    context_prefix=context_prefix,
                    part=current_hierarchy.part,
                    chapter=current_hierarchy.chapter,
                    section=current_hierarchy.section,
                    subsection=current_hierarchy.subsection,
                    clause=current_hierarchy.clause,
                    subclause=current_hierarchy.subclause,
                    schedule=current_hierarchy.schedule,
                    page_start=page_start,
                    page_end=page_end,
                    chunk_index=chunk_counter,
                    chunk_part=1,
                    total_parts=1,
                    is_continuation=False,
                    character_count=len(full_content),
                    word_count=len(words),
                    line_count=len(lines),
                )
                chunks.append(chunk)
                chunk_counter += 1

            current_unit_lines = []
            current_unit_pages = []

        # Process lines
        i = 0
        total_lines = len(page_lines)

        while i < total_lines:
            pno, line = page_lines[i]
            trimmed = line.strip()

            if not trimmed:
                i += 1
                continue

            # Check for PART header
            m_part = self.PART_START_RE.match(trimmed)
            if m_part:
                part_id = m_part.group(1).upper()
                tracker.update_part(part_id)

            # Check for CHAPTER header
            m_chap = self.CHAPTER_START_RE.match(trimmed)
            if m_chap:
                chap_id = f"CHAPTER {m_chap.group(2).upper()}"
                chap_title = m_chap.group(3).strip() if m_chap.group(3) else None
                if not chap_title and (i + 1 < total_lines):
                    next_pno, next_line = page_lines[i + 1]
                    if next_line.strip().isupper() and len(next_line.strip()) < 80:
                        chap_title = next_line.strip()
                tracker.update_chapter(chap_id, chap_title)

            # Check for SCHEDULE header
            m_sched = self.SCHEDULE_START_RE.match(trimmed)
            if m_sched:
                emit_current_unit()
                sched_id = m_sched.group(1).upper()
                sched_title = m_sched.group(2).strip() if m_sched.group(2) else None
                tracker.reset_for_schedule(sched_id, sched_title)
                current_unit_type = ChunkType.SCHEDULE
                current_unit_id = sched_id
                current_hierarchy = tracker.snapshot()
                current_unit_lines.append(line)
                current_unit_pages.append(pno)
                i += 1
                continue

            # Check for SECTION start
            m_sec = self.SECTION_START_RE.match(trimmed)
            # Avoid matching decimal numbers or small numbered list items when inside schedules
            if m_sec and not tracker.current_schedule:
                sec_num = m_sec.group(1)
                sec_rest = m_sec.group(2)
                
                # Emit whatever unit was accumulating
                emit_current_unit()

                # Update hierarchy
                sec_title = sec_rest[:80].strip() if sec_rest else None
                tracker.update_section(sec_num, sec_title)
                current_unit_type = ChunkType.SECTION
                current_unit_id = f"Sec_{sec_num}"
                current_hierarchy = tracker.snapshot()

                current_unit_lines.append(line)
                current_unit_pages.append(pno)
                i += 1
                continue

            # Standard line belonging to the active unit
            if not current_unit_lines:
                current_hierarchy = tracker.snapshot()
                current_unit_id = f"Sec_{current_hierarchy.section}" if current_hierarchy.section else "preamble"
                current_unit_type = ChunkType.SECTION if current_hierarchy.section else ChunkType.ACT_PREAMBLE

            current_unit_lines.append(line)
            current_unit_pages.append(pno)
            i += 1

        # Emit the final remaining unit
        emit_current_unit()

        return chunks
