"""Unit tests for TextCleaner and conservative normalization."""

import unittest
from ingestion.cleaners.text_cleaner import TextCleaner


class TestTextCleaner(unittest.TestCase):
    """Tests conservative text cleaner rules and invariants."""

    def test_normalize_line_endings(self):
        raw = "Line 1\r\nLine 2\rLine 3\nLine 4"
        cleaned = TextCleaner.clean_text(raw)
        self.assertEqual(cleaned, "Line 1\nLine 2\nLine 3\nLine 4")

    def test_strip_null_and_control_chars(self):
        raw = "Section 103.\x00 Punishment\x07 for\x1f murder."
        cleaned = TextCleaner.clean_text(raw)
        self.assertEqual(cleaned, "Section 103. Punishment for murder.")

    def test_normalize_unicode_spaces(self):
        raw = "The\u00a0Bharatiya\u200bNyaya\ufeffSanhita"
        cleaned = TextCleaner.clean_text(raw)
        self.assertEqual(cleaned, "The Bharatiya Nyaya Sanhita")

    def test_safe_dehyphenation(self):
        raw = "The appro-\npriate Government may, by notifi-\ncation in the Official Gazette, appoint."
        cleaned = TextCleaner.clean_text(raw)
        self.assertEqual(
            cleaned,
            "The appropriate Government may, by notification in the Official Gazette, appoint."
        )

    def test_preserve_legal_section_numbers_and_hyphens(self):
        # Must NOT dehyphenate or corrupt section references
        raw = "refer to section 21-A or section 304-B of the Act."
        cleaned = TextCleaner.clean_text(raw)
        self.assertIn("21-A", cleaned)
        self.assertIn("304-B", cleaned)

    def test_preserve_em_dash_and_punctuation(self):
        raw = "BE it enacted by Parliament as follows:—\n\nExplanation.—Whenever a Court records an issue..."
        cleaned = TextCleaner.clean_text(raw)
        self.assertIn("follows:—", cleaned)
        self.assertIn("Explanation.—Whenever", cleaned)

    def test_collapse_multiple_blank_lines(self):
        raw = "Paragraph 1\n\n\n\n\nParagraph 2"
        cleaned = TextCleaner.clean_text(raw)
        self.assertEqual(cleaned, "Paragraph 1\n\nParagraph 2")

    def test_horizontal_spaces(self):
        raw = "Section    103.     Punishment    for murder."
        cleaned = TextCleaner.clean_text(raw)
        self.assertEqual(cleaned, "Section 103. Punishment for murder.")

    def test_empty_string(self):
        self.assertEqual(TextCleaner.clean_text(""), "")
        self.assertEqual(TextCleaner.clean_text("   \n\n  "), "")


if __name__ == "__main__":
    unittest.main()
