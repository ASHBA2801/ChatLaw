"""Deterministic Legal Structure Detection for Indian Statutes and Legal Documents."""

import re
from typing import List, Optional, Tuple

from ..models import StructuralUnit, StructuralUnitType


class LegalStructureDetector:
    """Detects hierarchical Indian legal units deterministically using regex patterns."""

    # Act Title: e.g. "THE BHARATIYA NYAYA SANHITA, 2023", "THE BHARATIYA SAKSHYA ADHINIYAM, 2023"
    ACT_TITLE_RE = re.compile(
        r'^\s*(THE\s+[A-Z\s\(\)]+?(?:ACT|SANHITA|ADHINIYAM|CODE)[A-Z\s\(\),]*?(?:,\s*\d{4})?)\s*$',
        re.MULTILINE
    )

    # Preamble / Enactment Formula
    PREAMBLE_RE = re.compile(
        r'^\s*(An\s+Act\s+to\b[^\n]+)',
        re.IGNORECASE | re.MULTILINE
    )
    ENACTING_FORMULA_RE = re.compile(
        r'^\s*(BE\s+it\s+enacted\s+by\s+Parliament\b[^\n]+(?:follows:—|follows:)?)\s*$',
        re.IGNORECASE | re.MULTILINE
    )

    # Part: e.g. "PART I", "PART II", "PART IV"
    PART_RE = re.compile(
        r'^\s*(PART\s+([IVXLCDM\d]+))\b(?:\s*[-—–]\s*(.*))?',
        re.IGNORECASE | re.MULTILINE
    )

    # Chapter: e.g. "CHAPTER I", "CHAPTER XXV", "CHAPTER 3"
    CHAPTER_RE = re.compile(
        r'^\s*(CHAPTER\s+([IVXLCDM\d]+))\b(?:\s*[-—–]\s*(.*))?',
        re.IGNORECASE | re.MULTILINE
    )

    # Schedule: e.g. "THE FIRST SCHEDULE", "THE SCHEDULE", "SECOND SCHEDULE"
    SCHEDULE_RE = re.compile(
        r'^\s*(THE\s+(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|\d+)?\s*SCHEDULE|THESCHEDULE)\b(?:\s*[-—–]\s*(.*))?',
        re.IGNORECASE | re.MULTILINE
    )

    # Section: e.g. "1. (1) This Act...", "103. Whoever commits murder...", "37. Judgments or orders..."
    # Starts with a number from 1 to 9999, optional letter (e.g. 304B), followed by period.
    SECTION_RE = re.compile(
        r'^\s*(\d{1,4}[A-Z]?)\.\s+(?:(?:\((\d{1,3}[A-Z]?)\)\s+)?(.*))?$',
        re.MULTILINE
    )

    # Subsection: e.g. "(1) Whoever...", "(2) It applies to..."
    SUBSECTION_RE = re.compile(
        r'^\s*\((\d{1,3}[A-Z]?)\)\s+(.*)$',
        re.MULTILINE
    )

    # Clause: e.g. "(a) "Court" includes...", "(b) if any..."
    CLAUSE_RE = re.compile(
        r'^\s*\(([a-z]{1,2})\)\s+(.*)$',
        re.MULTILINE
    )

    # Subclause: e.g. "(i) That a person...", "(ii) That there are..."
    SUBCLAUSE_RE = re.compile(
        r'^\s*\(([ivxlcdm]+)\)\s+(.*)$',
        re.MULTILINE
    )

    # Proviso: e.g. "Provided that...", "Provided further that..."
    PROVISO_RE = re.compile(
        r'^\s*(Provided\s+(?:further\s+|also\s+)?that)\b\s*(.*)$',
        re.IGNORECASE | re.MULTILINE
    )

    # Explanation: e.g. "Explanation.—", "Explanation 1.—", "Explanation:"
    EXPLANATION_RE = re.compile(
        r'^\s*(Explanation(?:\s+\d+)?)(?:[\.—\-—–:]+)\s*(.*)$',
        re.IGNORECASE | re.MULTILINE
    )

    # Illustration: e.g. "Illustrations.", "Illustration."
    ILLUSTRATION_HEADER_RE = re.compile(
        r'^\s*(Illustrations?)\.?\s*$',
        re.IGNORECASE | re.MULTILINE
    )

    # Definition pattern within text: e.g. (a) "Court" includes... or "facts in issue" means...
    DEFINITION_RE = re.compile(
        r'(?:^|\s)\(([a-z]{1,2})\)\s+"([^"]+)"\s+(includes|means|shall have)',
        re.IGNORECASE
    )

    # Rule / Regulation
    RULE_RE = re.compile(
        r'^\s*(Rule|Regulation)\s+(\d+[A-Z]?)\.?\s*(.*)$',
        re.IGNORECASE | re.MULTILINE
    )

    def detect_units_on_page(self, page_text: str, page_number: int = 1) -> List[StructuralUnit]:
        """Detects legal structural units on a single page.
        
        Args:
            page_text: The text content of the page (cleaned or raw).
            page_number: 1-indexed page number.
            
        Returns:
            List of detected StructuralUnit objects ordered by line number.
        """
        if not page_text or not page_text.strip():
            return []

        units: List[StructuralUnit] = []
        lines = page_text.split('\n')
        char_offset = 0
        in_illustrations_block = False

        for idx, line in enumerate(lines):
            line_len = len(line) + 1  # include newline char
            trimmed = line.strip()
            line_no = idx + 1

            if not trimmed:
                char_offset += line_len
                continue

            # 1. Check Act Title (primarily on early pages)
            if page_number <= 3:
                m = self.ACT_TITLE_RE.match(trimmed)
                if m:
                    units.append(StructuralUnit(
                        unit_type=StructuralUnitType.ACT_TITLE,
                        identifier=m.group(1).strip(),
                        title=m.group(1).strip(),
                        line_number=line_no,
                        start_char=char_offset,
                        end_char=char_offset + len(line),
                        confidence=0.95,
                        raw_match=trimmed
                    ))
                    char_offset += line_len
                    continue

                m = self.PREAMBLE_RE.match(trimmed)
                if m:
                    units.append(StructuralUnit(
                        unit_type=StructuralUnitType.PREAMBLE,
                        identifier="PREAMBLE",
                        title=m.group(1).strip(),
                        line_number=line_no,
                        start_char=char_offset,
                        end_char=char_offset + len(line),
                        confidence=0.90,
                        raw_match=trimmed
                    ))
                    char_offset += line_len
                    continue

                m = self.ENACTING_FORMULA_RE.match(trimmed)
                if m:
                    units.append(StructuralUnit(
                        unit_type=StructuralUnitType.ENACTING_FORMULA,
                        identifier="ENACTING_FORMULA",
                        title=m.group(1).strip(),
                        line_number=line_no,
                        start_char=char_offset,
                        end_char=char_offset + len(line),
                        confidence=0.90,
                        raw_match=trimmed
                    ))
                    char_offset += line_len
                    continue

            # 2. Check Part
            m = self.PART_RE.match(trimmed)
            if m:
                part_id = m.group(1).upper()
                part_title = m.group(3).strip() if m.group(3) else None
                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.PART,
                    identifier=part_id,
                    title=part_title,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.95,
                    raw_match=trimmed
                ))
                char_offset += line_len
                continue

            # 3. Check Chapter
            m = self.CHAPTER_RE.match(trimmed)
            if m:
                chap_id = f"CHAPTER {m.group(2).upper()}"
                chap_title = m.group(3).strip() if m.group(3) else None
                # If title is on next line, check next line
                if not chap_title and idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    if next_line and next_line.isupper() and len(next_line) < 80:
                        chap_title = next_line

                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.CHAPTER,
                    identifier=chap_id,
                    title=chap_title,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.95,
                    raw_match=trimmed
                ))
                char_offset += line_len
                continue

            # 4. Check Schedule
            m = self.SCHEDULE_RE.match(trimmed)
            if m:
                sched_id = m.group(1).upper()
                sched_title = m.group(2).strip() if m.group(2) else None
                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.SCHEDULE,
                    identifier=sched_id,
                    title=sched_title,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.95,
                    raw_match=trimmed
                ))
                char_offset += line_len
                continue

            # 5. Check Explanation
            m = self.EXPLANATION_RE.match(trimmed)
            if m:
                in_illustrations_block = False
                expl_id = m.group(1).strip()
                expl_body = m.group(2).strip() if m.group(2) else None
                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.EXPLANATION,
                    identifier=expl_id,
                    title=expl_body[:60] if expl_body else None,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.95,
                    raw_match=trimmed
                ))
                char_offset += line_len
                continue

            # 6. Check Proviso
            m = self.PROVISO_RE.match(trimmed)
            if m:
                in_illustrations_block = False
                prov_id = m.group(1).strip()
                prov_body = m.group(2).strip() if m.group(2) else None
                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.PROVISO,
                    identifier=prov_id,
                    title=prov_body[:60] if prov_body else None,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.90,
                    raw_match=trimmed
                ))
                char_offset += line_len
                continue

            # 7. Check Illustration Header
            m = self.ILLUSTRATION_HEADER_RE.match(trimmed)
            if m:
                in_illustrations_block = True
                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.ILLUSTRATION,
                    identifier=m.group(1).strip(),
                    title=None,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.95,
                    raw_match=trimmed
                ))
                char_offset += line_len
                continue

            # 8. Check Section
            m = self.SECTION_RE.match(trimmed)
            if m:
                in_illustrations_block = False
                sec_num = m.group(1)
                sub_num = m.group(2)
                heading_or_body = m.group(3) if m.group(3) else ""

                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.SECTION,
                    identifier=sec_num,
                    title=heading_or_body[:80].strip() if heading_or_body else None,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.90,
                    raw_match=trimmed
                ))

                if sub_num:
                    units.append(StructuralUnit(
                        unit_type=StructuralUnitType.SUBSECTION,
                        identifier=f"({sub_num})",
                        title=heading_or_body[:60].strip() if heading_or_body else None,
                        line_number=line_no,
                        start_char=char_offset,
                        end_char=char_offset + len(line),
                        confidence=0.85,
                        raw_match=f"({sub_num})"
                    ))

                char_offset += line_len
                continue

            # 9. Check Subsection: e.g. "(1) ..."
            m = self.SUBSECTION_RE.match(trimmed)
            if m:
                in_illustrations_block = False
                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.SUBSECTION,
                    identifier=f"({m.group(1)})",
                    title=m.group(2)[:60].strip() if m.group(2) else None,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.85,
                    raw_match=trimmed[:40]
                ))
                char_offset += line_len
                continue

            # 10. Check Subclause (roman numerals): e.g. "(i) ...", "(iv) ..."
            m = self.SUBCLAUSE_RE.match(trimmed)
            if m and m.group(1).lower() in ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']:
                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.SUBCLAUSE,
                    identifier=f"({m.group(1)})",
                    title=m.group(2)[:60].strip() if m.group(2) else None,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.80,
                    raw_match=trimmed[:40]
                ))
                char_offset += line_len
                continue

            # 11. Check Definition: (a) "Court" includes...
            m_def = self.DEFINITION_RE.search(trimmed)
            if m_def:
                units.append(StructuralUnit(
                    unit_type=StructuralUnitType.DEFINITION,
                    identifier=m_def.group(2),
                    title=f'"{m_def.group(2)}" {m_def.group(3)}',
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.90,
                    raw_match=trimmed[:60]
                ))
                char_offset += line_len
                continue

            # 12. Check Clause: e.g. "(a) ..."
            m = self.CLAUSE_RE.match(trimmed)
            if m:
                # If currently in an illustrations block, this is an illustration case
                unit_type = StructuralUnitType.ILLUSTRATION if in_illustrations_block else StructuralUnitType.CLAUSE
                units.append(StructuralUnit(
                    unit_type=unit_type,
                    identifier=f"({m.group(1)})",
                    title=m.group(2)[:60].strip() if m.group(2) else None,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.75 if in_illustrations_block else 0.80,
                    raw_match=trimmed[:40]
                ))
                char_offset += line_len
                continue

            # 13. Check Rule / Regulation
            m = self.RULE_RE.match(trimmed)
            if m:
                u_type = StructuralUnitType.RULE if m.group(1).lower() == 'rule' else StructuralUnitType.REGULATION
                units.append(StructuralUnit(
                    unit_type=u_type,
                    identifier=f"{m.group(1)} {m.group(2)}",
                    title=m.group(3)[:60].strip() if m.group(3) else None,
                    line_number=line_no,
                    start_char=char_offset,
                    end_char=char_offset + len(line),
                    confidence=0.90,
                    raw_match=trimmed
                ))
                char_offset += line_len
                continue

            char_offset += line_len

        return units

    def detect_document_act_title(self, pages: List[str]) -> Optional[str]:
        """Scans the initial pages of a document to find the canonical Act title.
        
        Args:
            pages: List of page texts.
            
        Returns:
            The Act Title string if found, or None.
        """
        for page in pages[:5]:
            if not page:
                continue
            for line in page.split('\n')[:15]:
                trimmed = line.strip()
                m = self.ACT_TITLE_RE.match(trimmed)
                if m:
                    return m.group(1).strip()
        return None
