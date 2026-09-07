"""Unit tests for deterministic LegalStructureDetector."""

import unittest
from ingestion.models import StructuralUnitType
from ingestion.structure.legal_structure import LegalStructureDetector


class TestLegalStructureDetector(unittest.TestCase):
    """Tests pattern matching for Indian statutory elements."""

    def setUp(self):
        self.detector = LegalStructureDetector()

    def test_detect_act_title(self):
        page_text = "THE BHARATIYA NYAYA SANHITA, 2023\nNO. 45 OF 2023\n[25th December, 2023.]"
        units = self.detector.detect_units_on_page(page_text, page_number=1)

        act_units = [u for u in units if u.unit_type == StructuralUnitType.ACT_TITLE]
        self.assertEqual(len(act_units), 1)
        self.assertIn("THE BHARATIYA NYAYA SANHITA, 2023", act_units[0].identifier)

    def test_detect_preamble_and_enacting_formula(self):
        page_text = (
            "An Act to consolidate and amend the provisions relating to offences and for matters connected therewith.\n"
            "BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as follows:—\n"
            "PART I\nCHAPTER I\nPRELIMINARY\n1. (1) This Act may be called..."
        )
        units = self.detector.detect_units_on_page(page_text, page_number=1)

        preambles = [u for u in units if u.unit_type == StructuralUnitType.PREAMBLE]
        enactings = [u for u in units if u.unit_type == StructuralUnitType.ENACTING_FORMULA]

        self.assertEqual(len(preambles), 1)
        self.assertEqual(len(enactings), 1)

    def test_detect_part_and_chapter(self):
        page_text = "PART II\nCHAPTER III\nGENERAL EXCEPTIONS\n"
        units = self.detector.detect_units_on_page(page_text, page_number=5)

        part_units = [u for u in units if u.unit_type == StructuralUnitType.PART]
        chap_units = [u for u in units if u.unit_type == StructuralUnitType.CHAPTER]

        self.assertEqual(len(part_units), 1)
        self.assertEqual(part_units[0].identifier, "PART II")
        self.assertEqual(len(chap_units), 1)
        self.assertEqual(chap_units[0].identifier, "CHAPTER III")
        self.assertEqual(chap_units[0].title, "GENERAL EXCEPTIONS")

    def test_detect_sections_and_subsections(self):
        page_text = (
            "103. (1) Whoever commits murder shall be punished with death or imprisonment for life.\n"
            "(2) When a group of five or more persons acting in concert..."
        )
        units = self.detector.detect_units_on_page(page_text, page_number=20)

        sections = [u for u in units if u.unit_type == StructuralUnitType.SECTION]
        subsections = [u for u in units if u.unit_type == StructuralUnitType.SUBSECTION]

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].identifier, "103")

        self.assertEqual(len(subsections), 2)
        self.assertEqual(subsections[0].identifier, "(1)")
        self.assertEqual(subsections[1].identifier, "(2)")

    def test_detect_proviso_and_explanation(self):
        page_text = (
            "Provided that where the value of property stolen does not exceed five thousand rupees...\n"
            "Explanation.—For the purposes of this sub-section, property means..."
        )
        units = self.detector.detect_units_on_page(page_text, page_number=30)

        provisos = [u for u in units if u.unit_type == StructuralUnitType.PROVISO]
        explanations = [u for u in units if u.unit_type == StructuralUnitType.EXPLANATION]

        self.assertEqual(len(provisos), 1)
        self.assertIn("Provided that", provisos[0].identifier)

        self.assertEqual(len(explanations), 1)
        self.assertEqual(explanations[0].identifier, "Explanation")

    def test_detect_illustrations(self):
        page_text = (
            "Illustrations.\n"
            "(a) A is accused of the murder of B.\n"
            "(b) A sues B for the price of goods."
        )
        units = self.detector.detect_units_on_page(page_text, page_number=15)

        illustrations = [u for u in units if u.unit_type == StructuralUnitType.ILLUSTRATION]
        self.assertEqual(len(illustrations), 3)  # Header + (a) + (b)

    def test_detect_definitions(self):
        page_text = '2. (1) In this Adhiniyam, unless the context otherwise requires,—\n(a) "Court" includes all Judges and Magistrates...'
        units = self.detector.detect_units_on_page(page_text, page_number=2)

        definitions = [u for u in units if u.unit_type == StructuralUnitType.DEFINITION]
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0].identifier, "Court")

    def test_detect_schedule(self):
        page_text = "THE FIRST SCHEDULE\nCLASSIFICATION OF OFFENCES\n"
        units = self.detector.detect_units_on_page(page_text, page_number=50)

        schedules = [u for u in units if u.unit_type == StructuralUnitType.SCHEDULE]
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0].identifier, "THE FIRST SCHEDULE")


if __name__ == "__main__":
    unittest.main()
