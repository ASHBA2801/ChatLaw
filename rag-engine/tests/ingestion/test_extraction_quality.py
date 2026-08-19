"""Unit tests for PDF extraction quality analyzer."""

import unittest
from ingestion.models import PageData, QualityFlag
from ingestion.parsers.pdf_parser import PDFParser


class TestExtractionQuality(unittest.TestCase):
    """Tests extraction quality metrics, OCR requirements, and anomaly detection."""

    def setUp(self):
        self.parser = PDFParser()

    def test_pristine_document_quality(self):
        pages = [
            PageData(
                page_number=1,
                raw_text="THE BHARATIYA NYAYA SANHITA, 2023. An Act to consolidate and amend the provisions relating to offences and for matters connected therewith. BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as follows: Chapter I Preliminary. 1. (1) This Act may be called the Bharatiya Nyaya Sanhita, 2023.",
                cleaned_text="THE BHARATIYA NYAYA SANHITA, 2023. An Act to consolidate and amend the provisions relating to offences and for matters connected therewith. BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as follows: Chapter I Preliminary. 1. (1) This Act may be called the Bharatiya Nyaya Sanhita, 2023.",
                character_count=335,
                word_count=52,
                line_count=4,
            ),
            PageData(
                page_number=2,
                raw_text="2. In this Sanhita, unless the context otherwise requires, (a) 'act' denotes as well a series of acts as a single act; (b) 'animal' denotes any living creature, other than a human being; (c) 'child' means any person below the age of eighteen years.",
                cleaned_text="2. In this Sanhita, unless the context otherwise requires, (a) 'act' denotes as well a series of acts as a single act; (b) 'animal' denotes any living creature, other than a human being; (c) 'child' means any person below the age of eighteen years.",
                character_count=250,
                word_count=42,
                line_count=3,
            )
        ]

        quality = self.parser.analyze_extraction_quality(pages, page_count=2)

        self.assertFalse(quality.ocr_required)
        self.assertEqual(quality.total_characters, 585)
        self.assertEqual(quality.total_words, 94)
        self.assertEqual(quality.text_coverage, 1.0)
        self.assertIn(QualityFlag.OK, quality.flags)
        self.assertGreaterEqual(quality.quality_score, 0.9)

    def test_ocr_required_on_empty_pages(self):
        pages = [
            PageData(
                page_number=1,
                raw_text="",
                cleaned_text="",
                character_count=0,
                word_count=0,
                line_count=0,
            ),
            PageData(
                page_number=2,
                raw_text="",
                cleaned_text="",
                character_count=0,
                word_count=0,
                line_count=0,
            )
        ]

        quality = self.parser.analyze_extraction_quality(pages, page_count=2)

        self.assertTrue(quality.ocr_required)
        self.assertIn(QualityFlag.OCR_REQUIRED, quality.flags)
        self.assertEqual(quality.text_coverage, 0.0)
        self.assertLess(quality.quality_score, 0.5)

    def test_repeated_garbage_characters(self):
        garbage_text = "Section \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd"
        pages = [
            PageData(
                page_number=1,
                raw_text=garbage_text,
                cleaned_text=garbage_text,
                character_count=len(garbage_text),
                word_count=2,
                line_count=1,
            )
        ]

        quality = self.parser.analyze_extraction_quality(pages, page_count=1)

        self.assertIn(QualityFlag.REPEATED_GARBAGE_CHARACTERS, quality.flags)
        self.assertLess(quality.quality_score, 1.0)

    def test_mostly_empty_pages_flag(self):
        pages = [
            PageData(
                page_number=1,
                raw_text="Some header.",
                cleaned_text="Some header.",
                character_count=12,
                word_count=2,
                line_count=1,
            ),
            PageData(
                page_number=2,
                raw_text="",
                cleaned_text="",
                character_count=0,
                word_count=0,
                line_count=0,
            ),
            PageData(
                page_number=3,
                raw_text="A lot of proper content here that has sufficient text to count as populated.",
                cleaned_text="A lot of proper content here that has sufficient text to count as populated.",
                character_count=77,
                word_count=14,
                line_count=1,
            )
        ]

        quality = self.parser.analyze_extraction_quality(pages, page_count=3)
        self.assertIn(QualityFlag.MOSTLY_EMPTY_PAGES, quality.flags)


if __name__ == "__main__":
    unittest.main()
