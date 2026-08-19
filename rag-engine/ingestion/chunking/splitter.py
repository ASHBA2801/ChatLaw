"""Safe boundary-aware splitter for oversized legal text units."""

import re
from typing import List, Tuple


class LegalSplitter:
    """Splits oversized legal units safely at structural or grammatical boundaries."""

    # Sentence boundary: period followed by space and capital letter or quote
    SENTENCE_END = re.compile(r'(?<=[.\?!;])\s+(?=[A-Z"\'\(])')

    # Structural item boundaries inside text
    SUB_ITEM_BOUNDARY = re.compile(
        r'(?:\n|\r\n)(?=(?:\(\d{1,3}[A-Z]?\)|\([a-z]{1,2}\)|\([ivxlcdm]+\)|Explanation(?:\s+\d+)?|Provided\s+(?:further\s+|also\s+)?that|Illustration))',
        re.IGNORECASE
    )

    def __init__(self, max_chunk_chars: int = 3500, min_chunk_chars: int = 200):
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars

    def is_oversized(self, text: str) -> bool:
        """Checks if text exceeds the configured safe chunk character limit."""
        return len(text.strip()) > self.max_chunk_chars

    def split_legal_unit(self, text: str) -> List[str]:
        """Splits an oversized legal text unit into continuation segments.
        
        Order of splitting priority:
        1. Structural sub-boundaries (subsections, clauses, provisos, explanations)
        2. Paragraph boundaries (\n\n)
        3. Sentence boundaries (. followed by capital)
        4. Whitespace boundary as a last resort
        
        Args:
            text: The full text of the oversized unit.
            
        Returns:
            List of non-empty text partitions.
        """
        clean_text = text.strip()
        if not self.is_oversized(clean_text):
            return [clean_text]

        # Step 1: Try splitting by structural sub-items
        parts = self._split_by_pattern(clean_text, self.SUB_ITEM_BOUNDARY)
        if len(parts) > 1 and all(len(p) <= self.max_chunk_chars for p in parts):
            return self._pack_segments(parts)

        # Step 2: Try splitting by paragraphs (\n\n)
        paragraphs = clean_text.split('\n\n')
        if len(paragraphs) > 1:
            packed_paras = self._pack_segments(paragraphs, joiner="\n\n")
            # If all packed paragraphs are now within limit, return them
            if all(len(p) <= self.max_chunk_chars for p in packed_paras):
                return packed_paras
            # Otherwise recursively split any remaining oversized paragraphs
            result = []
            for para in packed_paras:
                if self.is_oversized(para):
                    result.extend(self._split_sentences(para))
                else:
                    result.append(para)
            return self._pack_segments(result, joiner="\n\n")

        # Step 3: Sentence-based splitting
        return self._split_sentences(clean_text)

    def _split_sentences(self, text: str) -> List[str]:
        """Splits text using sentence boundaries and packs into chunks."""
        sentences = self.SENTENCE_END.split(text)
        if len(sentences) > 1:
            packed = self._pack_segments(sentences, joiner=" ")
            if all(len(p) <= self.max_chunk_chars for p in packed):
                return packed
            # If an individual sentence is STILL oversized (rare statutory monolithic sentence),
            # split on line or word boundary
            final_parts = []
            for sent in packed:
                if self.is_oversized(sent):
                    final_parts.extend(self._split_lines_or_words(sent))
                else:
                    final_parts.append(sent)
            return final_parts

        return self._split_lines_or_words(text)

    def _split_lines_or_words(self, text: str) -> List[str]:
        """Last-resort fallback to split on newline or word boundaries."""
        lines = text.split('\n')
        if len(lines) > 1:
            packed = self._pack_segments(lines, joiner="\n")
            if all(len(p) <= self.max_chunk_chars for p in packed):
                return packed

        # Word boundary split
        words = text.split(' ')
        segments = []
        current_words = []
        current_len = 0

        for word in words:
            word_len = len(word) + 1
            if current_len + word_len > self.max_chunk_chars and current_words:
                segments.append(" ".join(current_words))
                current_words = [word]
                current_len = len(word)
            else:
                current_words.append(word)
                current_len += word_len

        if current_words:
            segments.append(" ".join(current_words))

        return segments

    def _split_by_pattern(self, text: str, pattern: re.Pattern) -> List[str]:
        """Splits text using regex lookahead/lookbehind while keeping segments."""
        parts = [p.strip() for p in pattern.split(text) if p.strip()]
        return parts

    def _pack_segments(self, segments: List[str], joiner: str = "\n\n") -> List[str]:
        """Packs smaller pieces greedily up to max_chunk_chars."""
        packed: List[str] = []
        current_buf: List[str] = []
        current_len = 0
        joiner_len = len(joiner)

        for seg in segments:
            seg_len = len(seg)
            if current_buf and (current_len + joiner_len + seg_len > self.max_chunk_chars):
                packed.append(joiner.join(current_buf))
                current_buf = [seg]
                current_len = seg_len
            else:
                current_buf.append(seg)
                current_len += (joiner_len + seg_len) if current_buf else seg_len

        if current_buf:
            packed.append(joiner.join(current_buf))

        return packed
