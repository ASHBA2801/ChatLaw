"""Conservative Text Cleaner and Header/Footer Detector for Legal Documents."""

import re
from collections import Counter
from typing import Dict, List, Set, Tuple


class TextCleaner:
    """Conservative legal text cleaner that preserves legal meaning, numbers, and citations."""

    # Unicode space variants to normalize to standard ASCII space
    UNICODE_SPACES = re.compile(r'[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000\uFEFF\u200B\u200C\u200D\u200E\u200F]')
    
    # Safe de-hyphenation pattern: lowercase word part hyphenated at end of line followed by lowercase word continuation
    # e.g., 'juris-\ndiction' -> 'jurisdiction', 'provi-\nsions' -> 'provisions'
    # Does NOT match section numbers like '21-A', negative numbers, or em-dashes '—'
    SAFE_HYPHEN_BREAK = re.compile(r'([a-zA-Z]{2,})-\n\s*([a-z]{2,})')

    # Null bytes and control characters (excluding tab and newline)
    CONTROL_CHARS = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')

    # Multiple blank lines (3 or more newlines collapsed to 2)
    MULTIPLE_BLANK_LINES = re.compile(r'\n{3,}')

    # Excessive horizontal spaces (2 or more spaces/tabs collapsed to single space)
    HORIZONTAL_SPACES = re.compile(r'[^\S\n]{2,}')

    @classmethod
    def clean_text(cls, raw_text: str) -> str:
        """Applies conservative cleaning transformations to raw PDF text.
        
        Args:
            raw_text: Raw text extracted from PDF page.
            
        Returns:
            Cleaned and normalized text.
        """
        if not raw_text:
            return ""

        # 1. Normalize line endings
        text = raw_text.replace('\r\n', '\n').replace('\r', '\n')

        # 2. Strip null and illegal control characters
        text = cls.CONTROL_CHARS.sub('', text)

        # 3. Normalize non-standard unicode whitespace
        text = cls.UNICODE_SPACES.sub(' ', text)

        # 4. Safe de-hyphenation across line breaks
        text = cls.SAFE_HYPHEN_BREAK.sub(r'\1\2', text)

        # 5. Clean trailing/leading spaces on each line while preserving line structure
        lines = [cls.HORIZONTAL_SPACES.sub(' ', line).rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # 6. Collapse runs of 3+ newlines to 2 newlines (preserves paragraph breaks)
        text = cls.MULTIPLE_BLANK_LINES.sub('\n\n', text)

        return text.strip()


class HeaderFooterDetector:
    """Detects recurring header and footer patterns across pages in a document."""

    def __init__(self, min_ratio: float = 0.20, min_pages: int = 3, sample_lines: int = 3):
        """
        Args:
            min_ratio: Minimum fraction of document pages a line must appear on (0.0 - 1.0).
            min_pages: Minimum absolute page count for a repeated pattern.
            sample_lines: Number of lines from top/bottom of each page to inspect.
        """
        self.min_ratio = min_ratio
        self.min_pages = min_pages
        self.sample_lines = sample_lines

    def detect(self, raw_pages: List[str]) -> Tuple[List[str], List[str]]:
        """Analyzes all pages in a document and detects repeated headers and footers.
        
        Args:
            raw_pages: List of raw page text strings in document order.
            
        Returns:
            Tuple of (repeated_headers, repeated_footers).
        """
        total_pages = len(raw_pages)
        if total_pages < self.min_pages:
            return [], []

        header_counts: Counter = Counter()
        footer_counts: Counter = Counter()

        for page in raw_pages:
            if not page or not page.strip():
                continue
            lines = [line.strip() for line in page.split('\n') if line.strip()]
            if not lines:
                continue

            # Top lines (potential headers)
            top_lines = lines[:self.sample_lines]
            for line in top_lines:
                normalized = self._normalize_for_matching(line)
                if self._is_candidate_header_footer(normalized):
                    header_counts[normalized] += 1

            # Bottom lines (potential footers)
            bottom_lines = lines[-self.sample_lines:]
            for line in bottom_lines:
                normalized = self._normalize_for_matching(line)
                if self._is_candidate_header_footer(normalized):
                    footer_counts[normalized] += 1

        threshold = max(self.min_pages, int(total_pages * self.min_ratio))

        repeated_headers = [line for line, count in header_counts.items() if count >= threshold]
        repeated_footers = [line for line, count in footer_counts.items() if count >= threshold]

        return sorted(repeated_headers), sorted(repeated_footers)

    def annotate_page(self, page_text: str, detected_headers: List[str], detected_footers: List[str]) -> Tuple[List[str], List[str]]:
        """Finds which detected headers and footers are present on a specific page.
        
        Args:
            page_text: The text of the page.
            detected_headers: Document-level detected headers.
            detected_footers: Document-level detected footers.
            
        Returns:
            Tuple of (page_headers, page_footers).
        """
        if not page_text or not page_text.strip():
            return [], []

        lines = [self._normalize_for_matching(line.strip()) for line in page_text.split('\n') if line.strip()]
        if not lines:
            return [], []

        top_lines = set(lines[:self.sample_lines])
        bottom_lines = set(lines[-self.sample_lines:])

        page_headers = [h for h in detected_headers if h in top_lines]
        page_footers = [f for f in detected_footers if f in bottom_lines]

        return page_headers, page_footers

    @staticmethod
    def _normalize_for_matching(line: str) -> str:
        """Normalizes line whitespace and casing for robust header/footer comparison."""
        return re.sub(r'\s+', ' ', line).strip()

    @staticmethod
    def _is_candidate_header_footer(line: str) -> bool:
        """Filters out lines that are unlikely to be standard headers/footers (e.g. empty or long prose)."""
        if not line or len(line) < 2 or len(line) > 120:
            return False
        # If it looks like pure page numbers or typical gazette headers
        if re.match(r'^\d+$', line):
            return True
        if re.match(r'^(SEC\.|PART|THE GAZETTE|PUBLISHED BY|EXTRAORDINARY|NO\.\s*\d+)', line, re.IGNORECASE):
            return True
        return True
