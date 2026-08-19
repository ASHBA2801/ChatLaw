"""Validation checks and quality assurance for legal chunks."""

from collections import Counter
from typing import Dict, List, Tuple
from .models import ChunkType, LegalChunk


class ChunkValidator:
    """Validates structural integrity, metadata consistency, and bounds of generated chunks."""

    def __init__(self, min_char_threshold: int = 15, max_char_threshold: int = 5000):
        self.min_char_threshold = min_char_threshold
        self.max_char_threshold = max_char_threshold

    def validate_chunks(self, chunks: List[LegalChunk]) -> Tuple[List[str], List[Dict[str, str]]]:
        """Runs validation checks on a list of chunks from a document.
        
        Returns:
            Tuple of (warnings, errors)
        """
        warnings: List[str] = []
        errors: List[Dict[str, str]] = []

        if not chunks:
            warnings.append("Document produced 0 chunks.")
            return warnings, errors

        seen_ids: Dict[str, int] = {}
        seen_hashes: Counter = Counter()

        for idx, chunk in enumerate(chunks):
            # 1. Missing IDs
            if not chunk.chunk_id:
                errors.append({"chunk_index": str(idx), "error": "Missing chunk_id"})
            elif chunk.chunk_id in seen_ids:
                errors.append({
                    "chunk_id": chunk.chunk_id,
                    "error": f"Duplicate chunk_id found (first seen at index {seen_ids[chunk.chunk_id]})"
                })
            else:
                seen_ids[chunk.chunk_id] = idx

            # 2. Duplicate Content Hash
            if chunk.chunk_hash:
                seen_hashes[chunk.chunk_hash] += 1

            # 3. Content emptiness
            if not chunk.content or not chunk.content.strip():
                errors.append({"chunk_id": chunk.chunk_id, "error": "Empty chunk content"})

            # 4. Length checks
            if len(chunk.content.strip()) < self.min_char_threshold:
                warnings.append(f"Suspiciously tiny chunk {chunk.chunk_id} ({len(chunk.content.strip())} chars)")
            elif len(chunk.content) > self.max_char_threshold:
                warnings.append(f"Oversized chunk {chunk.chunk_id} ({len(chunk.content)} chars) exceeds threshold {self.max_char_threshold}")

            # 5. Page Range validation
            if chunk.page_start < 1 or chunk.page_end < 1 or chunk.page_start > chunk.page_end:
                errors.append({
                    "chunk_id": chunk.chunk_id,
                    "error": f"Invalid page range [{chunk.page_start}, {chunk.page_end}]"
                })

            # 6. Continuation consistency
            if chunk.is_continuation and chunk.chunk_part <= 1:
                warnings.append(f"Continuation chunk {chunk.chunk_id} has chunk_part {chunk.chunk_part} <= 1")

            # 7. Hierarchy presence
            if not chunk.section and not chunk.schedule and chunk.chunk_type not in (ChunkType.ACT_PREAMBLE, ChunkType.FALLBACK):
                warnings.append(f"Chunk {chunk.chunk_id} lacks section and schedule context")

        # Report duplicate hashes
        for chash, count in seen_hashes.items():
            if count > 1:
                warnings.append(f"Duplicate content hash {chash[:12]}... appears in {count} chunks")

        return warnings, errors
