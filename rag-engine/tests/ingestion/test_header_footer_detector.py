"""Unit tests for HeaderFooterDetector."""

import unittest
from ingestion.cleaners.text_cleaner import HeaderFooterDetector


class TestHeaderFooterDetector(unittest.TestCase):
    """Tests detection and annotation of repeated headers and footers."""

    def test_detect_repeated_headers_and_footers(self):
        detector = HeaderFooterDetector(min_ratio=0.5, min_pages=3, sample_lines=2)

        pages = [
            "THE GAZETTE OF INDIA EXTRAORDINARY\nSEC. 1]\n\nBody text on page 1\n\nPage 1\nPUBLISHED BY AUTHORITY",
            "THE GAZETTE OF INDIA EXTRAORDINARY\nSEC. 1]\n\nBody text on page 2\n\nPage 2\nPUBLISHED BY AUTHORITY",
            "THE GAZETTE OF INDIA EXTRAORDINARY\nSEC. 1]\n\nBody text on page 3\n\nPage 3\nPUBLISHED BY AUTHORITY",
            "THE GAZETTE OF INDIA EXTRAORDINARY\nSEC. 1]\n\nBody text on page 4\n\nPage 4\nPUBLISHED BY AUTHORITY",
        ]

        headers, footers = detector.detect(pages)

        self.assertIn("THE GAZETTE OF INDIA EXTRAORDINARY", headers)
        self.assertIn("SEC. 1]", headers)
        self.assertIn("PUBLISHED BY AUTHORITY", footers)

    def test_annotate_page_without_text_deletion(self):
        detector = HeaderFooterDetector(min_ratio=0.5, min_pages=3, sample_lines=2)

        pages = [
            "THE GAZETTE OF INDIA EXTRAORDINARY\nSEC. 1]\n\nSection 1 text\n\nPUBLISHED BY AUTHORITY",
            "THE GAZETTE OF INDIA EXTRAORDINARY\nSEC. 1]\n\nSection 2 text\n\nPUBLISHED BY AUTHORITY",
            "THE GAZETTE OF INDIA EXTRAORDINARY\nSEC. 1]\n\nSection 3 text\n\nPUBLISHED BY AUTHORITY",
        ]

        headers, footers = detector.detect(pages)
        page1_headers, page1_footers = detector.annotate_page(pages[0], headers, footers)

        self.assertIn("THE GAZETTE OF INDIA EXTRAORDINARY", page1_headers)
        self.assertIn("SEC. 1]", page1_headers)
        self.assertIn("PUBLISHED BY AUTHORITY", page1_footers)


if __name__ == "__main__":
    unittest.main()
