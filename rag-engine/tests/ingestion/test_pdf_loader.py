"""Unit tests for PDF loader, discovery, and hashing."""

import hashlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from ingestion.loaders.pdf_loader import PDFLoader
from ingestion.models import FileHashInfo


class TestPDFLoader(unittest.TestCase):
    """Tests for PDF discovery, path handling, and hashing."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root_path = Path(self.test_dir)

        # Create nested test folder structure with mixed extensions and non-pdf files
        (self.root_path / "subdir with spaces").mkdir(parents=True)
        
        self.file1 = self.root_path / "doc_a.pdf"
        self.file2 = self.root_path / "subdir with spaces" / "doc_b.PDF"
        self.file3 = self.root_path / "doc_c.Pdf"
        self.non_pdf = self.root_path / "notes.txt"

        self.file1.write_bytes(b"Mock PDF Content A")
        self.file2.write_bytes(b"Mock PDF Content B")
        self.file3.write_bytes(b"Mock PDF Content C")
        self.non_pdf.write_text("Not a pdf file", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_discover_files_recursive_and_case_insensitive(self):
        loader = PDFLoader(self.root_path)
        discovered = loader.discover_files()

        self.assertEqual(len(discovered), 3)
        names = [p.name for p in discovered]
        self.assertIn("doc_a.pdf", names)
        self.assertIn("doc_b.PDF", names)
        self.assertIn("doc_c.Pdf", names)
        self.assertNotIn("notes.txt", names)

    def test_deterministic_ordering(self):
        loader = PDFLoader(self.root_path)
        discovered1 = loader.discover_files()
        discovered2 = loader.discover_files()

        self.assertEqual(discovered1, discovered2)
        # Should be sorted
        rel_paths = [p.relative_to(self.root_path).as_posix().lower() for p in discovered1]
        self.assertEqual(rel_paths, sorted(rel_paths))

    def test_compute_sha256(self):
        loader = PDFLoader(self.root_path)
        expected_hash = hashlib.sha256(b"Mock PDF Content A").hexdigest()
        actual_hash = loader.compute_sha256(self.file1)
        self.assertEqual(actual_hash, expected_hash)

    def test_get_file_info(self):
        loader = PDFLoader(self.root_path)
        info = loader.get_file_info(self.file2)

        self.assertIsInstance(info, FileHashInfo)
        self.assertEqual(info.filename, "doc_b.PDF")
        self.assertEqual(info.file_size_bytes, len(b"Mock PDF Content B"))
        self.assertEqual(info.sha256, hashlib.sha256(b"Mock PDF Content B").hexdigest())
        self.assertIn("subdir with spaces", info.relative_path)

    def test_duplicate_hash_detection(self):
        # Create duplicate file
        dup_file = self.root_path / "doc_duplicate.pdf"
        dup_file.write_bytes(b"Mock PDF Content A")

        loader = PDFLoader(self.root_path)
        file_infos, duplicates = loader.load_corpus_metadata()

        self.assertEqual(len(file_infos), 4)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0], hashlib.sha256(b"Mock PDF Content A").hexdigest())

    def test_nonexistent_directory_error(self):
        loader = PDFLoader(self.root_path / "does_not_exist")
        with self.assertRaises(FileNotFoundError):
            loader.discover_files()

    def test_generate_document_id(self):
        doc_id = PDFLoader.generate_document_id("Bharatiya_Nagarik_Suraksha_Sanhita,_2023.pdf", "abcdef123456")
        self.assertEqual(doc_id, "Bharatiya_Nagarik_Suraksha_Sanhita_2023")


if __name__ == "__main__":
    unittest.main()
