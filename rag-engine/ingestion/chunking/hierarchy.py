"""Statutory hierarchy tracking and context path builder for Indian statutes."""

from typing import Optional
from .models import LegalHierarchy


class HierarchyTracker:
    """Tracks current statutory scope (Act, Part, Chapter, Section, Schedule) as the document is parsed."""

    def __init__(self, act_title: Optional[str] = None):
        self.act_title: Optional[str] = act_title
        self.current_part: Optional[str] = None
        self.current_chapter: Optional[str] = None
        self.current_chapter_title: Optional[str] = None
        self.current_schedule: Optional[str] = None
        self.current_section: Optional[str] = None
        self.current_section_title: Optional[str] = None

    def reset_for_schedule(self, schedule_id: str, schedule_title: Optional[str] = None):
        """Sets active schedule context and clears chapter/section scope."""
        self.current_schedule = schedule_id
        self.current_section = None
        self.current_section_title = None

    def update_part(self, part_id: str):
        """Updates active Part."""
        self.current_part = part_id

    def update_chapter(self, chapter_id: str, chapter_title: Optional[str] = None):
        """Updates active Chapter."""
        self.current_chapter = chapter_id
        self.current_chapter_title = chapter_title

    def update_section(self, section_id: str, section_title: Optional[str] = None):
        """Updates active Section."""
        self.current_section = section_id
        self.current_section_title = section_title
        self.current_schedule = None  # Clear schedule if we entered a section

    def snapshot(
        self,
        subsection: Optional[str] = None,
        clause: Optional[str] = None,
        subclause: Optional[str] = None,
        heading: Optional[str] = None,
    ) -> LegalHierarchy:
        """Takes a frozen snapshot of the hierarchy at this point in time."""
        return LegalHierarchy(
            act_title=self.act_title,
            part=self.current_part,
            chapter=self.current_chapter,
            section=self.current_section,
            subsection=subsection,
            clause=clause,
            subclause=subclause,
            schedule=self.current_schedule,
            heading=heading or self.current_section_title or self.current_chapter_title,
        )

    def build_context_path(self, hierarchy: LegalHierarchy) -> str:
        """Builds a breadcrumb path string e.g.
        'Bharatiya Nyaya Sanhita, 2023 > Chapter VI > Section 103 > Subsection (1)'
        """
        parts = []
        if hierarchy.act_title:
            parts.append(hierarchy.act_title)
        if hierarchy.part:
            parts.append(hierarchy.part)
        if hierarchy.chapter:
            chap_str = hierarchy.chapter
            parts.append(chap_str)
        if hierarchy.schedule:
            parts.append(hierarchy.schedule)
        if hierarchy.section:
            sec_str = f"Section {hierarchy.section}"
            parts.append(sec_str)
        if hierarchy.subsection:
            sub_str = f"Subsection {hierarchy.subsection}" if not hierarchy.subsection.startswith("Subsection") else hierarchy.subsection
            parts.append(sub_str)
        if hierarchy.clause:
            clause_str = f"Clause {hierarchy.clause}" if not hierarchy.clause.startswith("Clause") else hierarchy.clause
            parts.append(clause_str)
        if hierarchy.subclause:
            subclause_str = f"Subclause {hierarchy.subclause}" if not hierarchy.subclause.startswith("Subclause") else hierarchy.subclause
            parts.append(subclause_str)

        if not parts:
            return "General Legal Context"
        return " > ".join(parts)

    def build_context_prefix(self, hierarchy: LegalHierarchy) -> str:
        """Builds a concise prefix heading for retrieval understanding."""
        elements = []
        if hierarchy.act_title:
            elements.append(f"[{hierarchy.act_title}]")
        if hierarchy.chapter:
            elements.append(hierarchy.chapter)
        if hierarchy.schedule:
            elements.append(hierarchy.schedule)
        if hierarchy.section:
            sec_header = f"Section {hierarchy.section}"
            if hierarchy.heading:
                sec_header += f" ({hierarchy.heading})"
            elements.append(sec_header)
        if hierarchy.subsection:
            elements.append(f"Sub-sec {hierarchy.subsection}")
        if hierarchy.clause:
            elements.append(f"Cl. {hierarchy.clause}")

        return " | ".join(elements) if elements else ""
