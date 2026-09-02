"""Act catalog model and registry loader for ChatLaw.

Provides typed access to legal_corpus/acts/catalog.json and helper functions
for document/Act identification, domain detection, and alias normalization.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ActCatalogEntry:
    act_id: str
    official_title: str
    short_title: str
    year: int
    act_number: str
    category: str
    domain: str
    jurisdiction: str
    document_type: str
    source_authority: str
    official_url: str
    status: str  # in_force | repealed | pending_commencement | transitional
    effective_from: str | None = None
    effective_to: str | None = None
    repeals: tuple[str, ...] = ()
    priority: str = "tier_1"  # tier_1 | tier_2 | tier_3
    aliases: tuple[str, ...] = ()
    ingestion_status: str = "pending_source"  # ingested | pending_source | error
    source_file: str | None = None
    sub_domains: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    jurisdiction_level: str = "CENTRAL"
    source_type: str = "official_gazette"
    retrieval_date: str | None = None
    ingestion_stage: str | None = None
    personal_law_framework: str | None = None
    gst_component: str | None = None
    assessment_year_from: str | None = None
    assessment_year_to: str | None = None
    implementation_notes: str | None = None
    amended_on: str | None = None
    version: str | None = None
    source_date: str | None = None
    state: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "ActCatalogEntry":
        primary_domain = str(data.get("domain", "general_legal"))
        raw_domains = data.get("domains") or [primary_domain]
        domains = tuple(str(d) for d in raw_domains)
        doc_type = str(data.get("document_type", "STATUTE")).upper()
        return cls(
            act_id=str(data["act_id"]),
            official_title=str(data["official_title"]),
            short_title=str(data.get("short_title") or data["official_title"]),
            year=int(data.get("year", 0)),
            act_number=str(data.get("act_number", "")),
            category=str(data.get("category", "")),
            domain=primary_domain,
            jurisdiction=str(data.get("jurisdiction", "India")),
            document_type=doc_type,
            source_authority=str(data.get("source_authority", "")),
            official_url=str(data.get("official_url", "")),
            status=str(data.get("status", "in_force")),
            effective_from=data.get("effective_from") if data.get("effective_from") else None,
            effective_to=data.get("effective_to") if data.get("effective_to") else None,
            repeals=tuple(data.get("repeals", ())),
            priority=str(data.get("priority", "tier_1")),
            aliases=tuple(data.get("aliases", ())),
            ingestion_status=str(data.get("ingestion_status", "pending_source")),
            source_file=data.get("source_file") if data.get("source_file") else None,
            sub_domains=tuple(data.get("sub_domains", ())),
            domains=domains,
            jurisdiction_level=str(data.get("jurisdiction_level", "CENTRAL")),
            source_type=str(data.get("source_type", "official_gazette")),
            retrieval_date=data.get("retrieval_date") if data.get("retrieval_date") else None,
            ingestion_stage=data.get("ingestion_stage") if data.get("ingestion_stage") else None,
            personal_law_framework=data.get("personal_law_framework") if data.get("personal_law_framework") else None,
            gst_component=data.get("gst_component") if data.get("gst_component") else None,
            assessment_year_from=data.get("assessment_year_from") if data.get("assessment_year_from") else None,
            assessment_year_to=data.get("assessment_year_to") if data.get("assessment_year_to") else None,
            implementation_notes=data.get("implementation_notes") if data.get("implementation_notes") else None,
            amended_on=data.get("amended_on") if data.get("amended_on") else None,
            version=data.get("version") if data.get("version") else None,
            source_date=data.get("source_date") if data.get("source_date") else None,
            state=data.get("state") if data.get("state") else None,
        )


class ActCatalog:
    """In-memory loaded registry of all known Acts in ChatLaw."""

    def __init__(self, entries: Sequence[ActCatalogEntry]):
        self._entries_by_id: dict[str, ActCatalogEntry] = {e.act_id: e for e in entries}
        # Build normalized alias index: norm_alias -> ActCatalogEntry
        self._alias_index: dict[str, ActCatalogEntry] = {}
        for entry in entries:
            # Index act_id
            self._alias_index[self._norm(entry.act_id)] = entry
            # Index official title and short title
            self._alias_index[self._norm(entry.official_title)] = entry
            self._alias_index[self._norm(entry.short_title)] = entry
            # Index all listed aliases
            for alias in entry.aliases:
                self._alias_index[self._norm(alias)] = entry

    @staticmethod
    def _norm(text: str | None) -> str:
        if not text:
            return ""
        import unicodedata
        import re
        norm = unicodedata.normalize("NFKC", text).lower()
        norm = re.sub(r"[^\w\s]", " ", norm)
        norm = " ".join(norm.split())
        if norm.startswith("the "):
            norm = norm[4:]
        return norm

    def get(self, act_id: str) -> ActCatalogEntry | None:
        return self._entries_by_id.get(act_id)

    def find_by_alias(self, text: str | None) -> ActCatalogEntry | None:
        if not text:
            return None
        norm = self._norm(text)
        if not norm:
            return None
        # Exact match
        if norm in self._alias_index:
            return self._alias_index[norm]
        # Underscore-replaced check
        without_underscore = norm.replace("_", " ")
        if without_underscore in self._alias_index:
            return self._alias_index[without_underscore]
        return None

    def get_ingested(self) -> tuple[ActCatalogEntry, ...]:
        return tuple(e for e in self._entries_by_id.values() if e.ingestion_status == "ingested")

    def get_by_domain(self, domain: str) -> tuple[ActCatalogEntry, ...]:
        """Return acts whose primary or secondary domain matches."""
        return tuple(
            e for e in self._entries_by_id.values()
            if e.domain == domain or domain in e.domains
        )

    def get_by_stage(self, stage: str) -> tuple[ActCatalogEntry, ...]:
        return tuple(
            e for e in self._entries_by_id.values()
            if e.ingestion_stage == stage
        )

    def get_by_priority(self, priority: str) -> tuple[ActCatalogEntry, ...]:
        return tuple(e for e in self._entries_by_id.values() if e.priority == priority)

    def all_entries(self) -> tuple[ActCatalogEntry, ...]:
        return tuple(self._entries_by_id.values())

    def domain_index(self) -> dict[str, tuple[str, ...]]:
        """Build act_id lists grouped by domain slug."""
        from collections import defaultdict
        index: dict[str, list[str]] = defaultdict(list)
        for entry in self._entries_by_id.values():
            for domain in entry.domains or (entry.domain,):
                index[domain].append(entry.act_id)
        return {k: tuple(v) for k, v in sorted(index.items())}

    def get_document_aliases_table(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Returns list of (canonical_id, (aliases...)) suitable for reranker._DOCUMENT_ALIASES."""
        result = []
        for entry in self._entries_by_id.values():
            aliases_list = list(entry.aliases)
            norm_title = self._norm(entry.official_title)
            if norm_title and norm_title not in aliases_list:
                aliases_list.append(norm_title)
            norm_short = self._norm(entry.short_title)
            if norm_short and norm_short not in aliases_list:
                aliases_list.append(norm_short)
            result.append((entry.act_id, tuple(aliases_list)))
        return tuple(result)


_GLOBAL_CATALOG: ActCatalog | None = None


def get_default_catalog_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "legal_corpus" / "acts" / "catalog.json",
        Path(__file__).resolve().parent.parent / "legal_corpus" / "acts" / "catalog.json",
        Path("legal_corpus/acts/catalog.json"),
        Path("../legal_corpus/acts/catalog.json"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def load_catalog(path: Path | str | None = None) -> ActCatalog:
    catalog_path = Path(path) if path else get_default_catalog_path()
    if not catalog_path.exists():
        # Fallback to minimal hardcoded catalog if file is missing
        return ActCatalog([])
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = [ActCatalogEntry.from_dict(item) for item in data.get("acts", [])]
    return ActCatalog(entries)


def get_catalog() -> ActCatalog:
    global _GLOBAL_CATALOG
    if _GLOBAL_CATALOG is None:
        _GLOBAL_CATALOG = load_catalog()
    return _GLOBAL_CATALOG


def reset_catalog_cache() -> None:
    """Clear cached catalog (for tests)."""
    global _GLOBAL_CATALOG
    _GLOBAL_CATALOG = None
