"""Comprehensive unit tests for legal-aware chunking pipeline (Phase RAG-02)."""

import json
import unittest
from ingestion.chunking.hierarchy import HierarchyTracker
from ingestion.chunking.legal_chunker import LegalChunker
from ingestion.chunking.models import ChunkType, LegalChunk, LegalHierarchy
from ingestion.chunking.splitter import LegalSplitter
from ingestion.chunking.validator import ChunkValidator
from ingestion.models import DocumentData, ExtractionQuality, PageData, QualityFlag


class TestLegalHierarchyAndTracker(unittest.TestCase):
    """Tests hierarchy tracking, breadcrumb generation, and prefix formatting."""

    def test_hierarchy_tracking(self):
        tracker = HierarchyTracker(act_title="THE BHARATIYA NYAYA SANHITA, 2023")
        tracker.update_part("PART I")
        tracker.update_chapter("CHAPTER VI", "OF OFFENCES AFFECTING THE HUMAN BODY")
        tracker.update_section("103", "Punishment for murder")

        snap = tracker.snapshot(subsection="(1)", clause="(a)")
        context_path = tracker.build_context_path(snap)
        context_prefix = tracker.build_context_prefix(snap)

        self.assertIn("THE BHARATIYA NYAYA SANHITA, 2023", context_path)
        self.assertIn("CHAPTER VI", context_path)
        self.assertIn("Section 103", context_path)
        self.assertIn("Subsection (1)", context_path)
        self.assertIn("Clause (a)", context_path)

        self.assertIn("Section 103 (Punishment for murder)", context_prefix)
        self.assertIn("Sub-sec (1)", context_prefix)


class TestLegalSplitter(unittest.TestCase):
    """Tests safety boundary splitting and continuation preservation."""

    def setUp(self):
        self.splitter = LegalSplitter(max_chunk_chars=300)

    def test_undersized_text_not_split(self):
        text = "This is a small legal section text that is well within the 300 character limit."
        parts = self.splitter.split_legal_unit(text)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], text)

    def test_oversized_text_split_at_structural_or_sentence_boundary(self):
        text = (
            "103. (1) Whoever commits murder shall be punished with death or with imprisonment for life, "
            "and shall also be liable to fine. This provision lays down the highest statutory penalty.\n\n"
            "(2) When a group of five or more persons acting in concert commits murder on ground of race, caste or community, "
            "sex, place of birth, language, personal belief or any other ground, each member of such group shall be punished with death or with imprisonment for life."
        )
        parts = self.splitter.split_legal_unit(text)
        self.assertGreater(len(parts), 1)
        # Verify all parts are within limits
        for p in parts:
            self.assertLessEqual(len(p), 300)
            self.assertTrue(len(p.strip()) > 0)

    def test_split_preserves_content_words(self):
        text = "Sentence one. " * 30
        parts = self.splitter.split_legal_unit(text)
        total_len = sum(len(p.split()) for p in parts)
        self.assertEqual(total_len, len(text.split()))


class TestLegalChunker(unittest.TestCase):
    """Tests deterministic statutory chunking across pages and structural units."""

    def setUp(self):
        self.chunker = LegalChunker(max_chunk_chars=2000)

    def _create_mock_document(self) -> DocumentData:
        page1 = PageData(
            page_number=1,
            raw_text="Raw 1",
            cleaned_text=(
                "THE BHARATIYA NYAYA SANHITA, 2023\n"
                "NO. 45 OF 2023\n"
                "An Act to consolidate and amend the provisions relating to offences.\n"
                "BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as follows:—\n"
                "CHAPTER I\n"
                "PRELIMINARY\n"
                "1. (1) This Act may be called the Bharatiya Nyaya Sanhita, 2023.\n"
                "(2) It shall come into force on such date as the Central Government may appoint."
            ),
            character_count=350,
            word_count=55,
            line_count=8,
        )

        page2 = PageData(
            page_number=2,
            raw_text="Raw 2",
            cleaned_text=(
                "2. In this Sanhita, unless the context otherwise requires,—\n"
                '(a) "act" denotes as well a series of acts as a single act;\n'
                '(b) "animal" denotes any living creature, other than a human being;\n'
                '(c) "child" means any person below the age of eighteen years.\n'
                "3. General explanations regarding offences and exceptions.\n"
                "Explanation.—Every person who aids is liable.\n"
                "Illustrations.\n"
                "(a) A instigates B to burn a house."
            ),
            character_count=400,
            word_count=65,
            line_count=8,
        )

        page3 = PageData(
            page_number=3,
            raw_text="Raw 3",
            cleaned_text=(
                "103. (1) Whoever commits murder shall be punished with death or imprisonment for life.\n"
                "Provided that where the act is done with grave and sudden provocation, section 105 applies.\n"
                "THE FIRST SCHEDULE\n"
                "CLASSIFICATION OF OFFENCES\n"
                "Offences under Bharatiya Nyaya Sanhita shall be cognizable and non-bailable."
            ),
            character_count=300,
            word_count=45,
            line_count=6,
        )

        return DocumentData(
            document_id="BNS_TEST",
            filename="BNS_TEST.pdf",
            source_path="BNS_TEST.pdf",
            sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            file_size_bytes=10000,
            page_count=3,
            detected_act_title="THE BHARATIYA NYAYA SANHITA, 2023",
            extraction_quality=ExtractionQuality(
                total_characters=1050,
                total_words=165,
                total_lines=22,
                pages_with_text=3,
                pages_without_text=0,
                text_coverage=1.0,
                avg_chars_per_page=350.0,
                ocr_required=False,
                flags=[QualityFlag.OK],
            ),
            pages=[page1, page2, page3],
        )

    def test_chunk_types_and_counts(self):
        doc = self._create_mock_document()
        chunks = self.chunker.chunk_document(doc)

        self.assertGreater(len(chunks), 0)
        types = [c.chunk_type for c in chunks]

        self.assertIn(ChunkType.ACT_PREAMBLE, types)
        self.assertIn(ChunkType.SECTION, types)
        self.assertIn(ChunkType.DEFINITION, types)
        self.assertIn(ChunkType.SCHEDULE, types)

    def test_deterministic_chunk_ids_and_hashes(self):
        doc = self._create_mock_document()
        run1 = self.chunker.chunk_document(doc)
        run2 = self.chunker.chunk_document(doc)

        self.assertEqual(len(run1), len(run2))
        for c1, c2 in zip(run1, run2):
            self.assertEqual(c1.chunk_id, c2.chunk_id)
            self.assertEqual(c1.chunk_hash, c2.chunk_hash)
            self.assertEqual(c1.content, c2.content)
            self.assertEqual(c1.context_path, c2.context_path)

    def test_cross_page_section_continuation(self):
        # Create a document where a section spans across page 1 and page 2
        p1 = PageData(
            page_number=1,
            raw_text="p1",
            cleaned_text="103. (1) Whoever commits murder shall be punished with death or imprisonment for life.",
            character_count=87,
            word_count=13,
            line_count=1,
        )
        p2 = PageData(
            page_number=2,
            raw_text="p2",
            cleaned_text=(
                "(2) When a group of persons commit murder.\n"
                "Explanation.—For the purposes of this section."
            ),
            character_count=85,
            word_count=12,
            line_count=2,
        )
        doc = DocumentData(
            document_id="CROSS_PAGE_DOC",
            filename="test.pdf",
            source_path="test.pdf",
            sha256="12345678",
            file_size_bytes=1000,
            page_count=2,
            detected_act_title="THE TEST ACT, 2023",
            extraction_quality=ExtractionQuality(
                total_characters=172,
                total_words=25,
                total_lines=3,
                pages_with_text=2,
                pages_without_text=0,
                text_coverage=1.0,
                avg_chars_per_page=86.0,
                ocr_required=False,
                flags=[QualityFlag.OK],
            ),
            pages=[p1, p2],
        )

        chunks = self.chunker.chunk_document(doc)
        self.assertEqual(len(chunks), 1)
        c = chunks[0]
        self.assertEqual(c.section, "103")
        self.assertEqual(c.page_start, 1)
        self.assertEqual(c.page_end, 2)
        self.assertIn("Whoever commits murder", c.content)
        self.assertIn("When a group of persons", c.content)


class TestChunkValidator(unittest.TestCase):
    """Tests chunk validation rules and error trapping."""

    def setUp(self):
        self.validator = ChunkValidator(min_char_threshold=10, max_char_threshold=500)

    def test_valid_chunks_pass(self):
        chunk = LegalChunk(
            chunk_id="doc_p1_Sec_1_idx0_pt1",
            document_id="doc",
            document_title="Act Title",
            document_sha256="hash123",
            chunk_hash=LegalChunk.compute_content_hash("Section 1 text here."),
            chunk_type=ChunkType.SECTION,
            content="Section 1 text here.",
            context_path="Act Title > Section 1",
            section="1",
            page_start=1,
            page_end=1,
            chunk_index=0,
            chunk_part=1,
            character_count=20,
            word_count=4,
            line_count=1,
        )
        warnings, errors = self.validator.validate_chunks([chunk])
        self.assertEqual(len(errors), 0)

    def test_detect_empty_or_duplicate_chunks(self):
        c1 = LegalChunk(
            chunk_id="duplicate_id",
            document_id="doc",
            document_sha256="hash123",
            chunk_hash="chash1",
            chunk_type=ChunkType.SECTION,
            content="Valid content.",
            context_path="Path",
            page_start=1,
            page_end=1,
            chunk_index=0,
        )
        c2 = LegalChunk(
            chunk_id="duplicate_id",
            document_id="doc",
            document_sha256="hash123",
            chunk_hash="chash1",
            chunk_type=ChunkType.SECTION,
            content="",  # empty content
            context_path="Path",
            page_start=2,
            page_end=1,  # invalid page range
            chunk_index=1,
        )
        warnings, errors = self.validator.validate_chunks([c1, c2])
        self.assertGreater(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
