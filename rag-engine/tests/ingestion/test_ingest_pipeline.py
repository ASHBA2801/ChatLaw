"""End-to-end integration test for ChatLaw ingestion pipeline."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
import pymupdf

from ingestion.loaders.pdf_loader import PDFLoader
from ingestion.parsers.pdf_parser import PDFParser
from ingestion.models import (
    DocumentData,
    DocumentMetadata,
    QualityFlag,
    StructuralUnitType,
)


class TestIngestPipeline(unittest.TestCase):
    """End-to-end integration test of PDF parsing, cleaning, structuring, and metadata generation."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root_path = Path(self.test_dir)
        self.pdf_path = self.root_path / "Test_Indian_Act_2023.pdf"

        # Create a synthetic 3-page PDF with realistic Indian legal formatting
        doc = pymupdf.open()

        # Page 1
        page1 = doc.new_page()
        text_p1 = (
            "THE TEST INDIAN LEGAL ACT, 2023\n"
            "NO. 99 OF 2023\n"
            "An Act to consolidate and amend the law relating to digital rights.\n"
            "BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as follows:—\n"
            "PART I\n"
            "CHAPTER I\n"
            "PRELIMINARY\n"
            "1. (1) This Act may be called the Test Indian Legal Act, 2023.\n"
            "(2) It extends to the whole of India.\n"
            "PUBLISHED BY AUTHORITY"
        )
        page1.insert_text((50, 50), text_p1)

        # Page 2
        page2 = doc.new_page()
        text_p2 = (
            "THE GAZETTE OF INDIA EXTRAORDINARY\n"
            "2. In this Act, unless the context otherwise requires,—\n"
            '(a) "Data" includes digital communications and records;\n'
            '(b) "User" means any citizen accessing online services.\n'
            "3. Rights of the citizen regarding personal data.\n"
            "Explanation.—For the purposes of this section, rights include privacy.\n"
            "Illustrations.\n"
            "(a) A requests deletion of account data. The provider must comply.\n"
            "PUBLISHED BY AUTHORITY"
        )
        page2.insert_text((50, 50), text_p2)

        # Page 3
        page3 = doc.new_page()
        text_p3 = (
            "THE GAZETTE OF INDIA EXTRAORDINARY\n"
            "4. Penalty for unauthorized access.\n"
            "Whoever knowingly breaches digital records shall be punished with imprisonment.\n"
            "Provided that the penalty may be reduced if reported voluntarily.\n"
            "THE FIRST SCHEDULE\n"
            "LIST OF EXEMPTIONS\n"
            "PUBLISHED BY AUTHORITY"
        )
        page3.insert_text((50, 50), text_p3)

        doc.save(str(self.pdf_path))
        doc.close()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_pipeline_execution(self):
        # 1. Loader & Hashing
        loader = PDFLoader(self.root_path)
        file_infos, duplicates = loader.load_corpus_metadata()

        self.assertEqual(len(file_infos), 1)
        self.assertEqual(len(duplicates), 0)
        file_info = file_infos[0]

        # 2. Parsing & Structuring
        parser = PDFParser()
        doc_data = parser.parse_pdf(file_info)

        # Validate DocumentData
        self.assertIsInstance(doc_data, DocumentData)
        self.assertEqual(doc_data.page_count, 3)
        self.assertIn("THE TEST INDIAN LEGAL ACT, 2023", doc_data.detected_act_title)
        self.assertFalse(doc_data.extraction_quality.ocr_required)
        self.assertEqual(doc_data.extraction_quality.text_coverage, 1.0)
        self.assertIn(QualityFlag.OK, doc_data.extraction_quality.flags)

        # Verify pages data
        self.assertEqual(len(doc_data.pages), 3)

        # Verify detected legal structural units across pages
        p1_units = doc_data.pages[0].detected_structure
        p1_types = [u.unit_type for u in p1_units]
        self.assertIn(StructuralUnitType.ACT_TITLE, p1_types)
        self.assertIn(StructuralUnitType.PREAMBLE, p1_types)
        self.assertIn(StructuralUnitType.ENACTING_FORMULA, p1_types)
        self.assertIn(StructuralUnitType.PART, p1_types)
        self.assertIn(StructuralUnitType.CHAPTER, p1_types)
        self.assertIn(StructuralUnitType.SECTION, p1_types)

        p2_units = doc_data.pages[1].detected_structure
        p2_types = [u.unit_type for u in p2_units]
        self.assertIn(StructuralUnitType.SECTION, p2_types)
        self.assertIn(StructuralUnitType.DEFINITION, p2_types)
        self.assertIn(StructuralUnitType.EXPLANATION, p2_types)
        self.assertIn(StructuralUnitType.ILLUSTRATION, p2_types)

        p3_units = doc_data.pages[2].detected_structure
        p3_types = [u.unit_type for u in p3_units]
        self.assertIn(StructuralUnitType.SECTION, p3_types)
        self.assertIn(StructuralUnitType.PROVISO, p3_types)
        self.assertIn(StructuralUnitType.SCHEDULE, p3_types)

        # 3. Metadata Generation
        doc_meta = parser.extract_document_metadata(doc_data)
        self.assertIsInstance(doc_meta, DocumentMetadata)
        self.assertEqual(doc_meta.document_id, doc_data.document_id)
        self.assertEqual(doc_meta.page_count, 3)
        self.assertEqual(doc_meta.extraction_status, "COMPLETED")

        # 4. JSON Serialization check
        json_output = doc_data.model_dump_json(indent=2)
        parsed_back = json.loads(json_output)
        self.assertEqual(parsed_back["document_id"], doc_data.document_id)
        self.assertEqual(len(parsed_back["pages"]), 3)


if __name__ == "__main__":
    unittest.main()
