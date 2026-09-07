"""Version-aware and jurisdiction filters for legal chunk retrieval."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Iterable


def parse_as_of_date(query: str, *, default: date | None = None) -> date:
    """Extract an as-of date from natural language when present."""
    today = default or date.today()
    text = query.lower()
    year_match = re.search(r"\b(?:in|during|for)\s+(?:the\s+)?year\s+(\d{4})\b", text)
    if year_match:
        return date(int(year_match.group(1)), 12, 31)
    ay_match = re.search(r"\b(?:assessment\s+year|a\.?y\.?)\s*(\d{4})\s*[-–]\s*(\d{2,4})\b", text)
    if ay_match:
        end = ay_match.group(2)
        end_year = int(end) if len(end) == 4 else int(f"20{end}")
        return date(end_year, 3, 31)
    if re.search(r"\b(?:today|currently|now|present\s+law)\b", text):
        return today
    if re.search(r"\b(?:before\s+2026|prior\s+to\s+2026|1961\s+act|income\s*tax\s*act\s*1961)\b", text):
        return date(2025, 12, 31)
    return today


def _parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None


def chunk_applicable_on(as_of: date, metadata: dict) -> bool:
    """Return True if chunk metadata indicates law applicable on as_of."""
    status = str(metadata.get("status") or "in_force").lower()
    effective_from = _parse_iso(metadata.get("effective_from"))
    effective_to = _parse_iso(metadata.get("effective_to"))

    if effective_from and as_of < effective_from:
        return False
    if effective_to and as_of > effective_to:
        return False

    if status == "repealed" and effective_to and as_of > effective_to:
        return False

    # Default: include in_force and transitional/repealed if within effective window
    return True


def filter_results_by_version(results: Iterable, as_of: date) -> list:
    filtered = []
    for result in results:
        meta = result.metadata if isinstance(result.metadata, dict) else {}
        if chunk_applicable_on(as_of, meta):
            filtered.append(result)
    return filtered


def build_version_sql_clause(as_of: date) -> tuple[str, tuple]:
    """SQL fragment excluding chunks outside effective window for as_of."""
    clause = """
      AND (
        (c.metadata->>'effective_from' IS NULL OR (c.metadata->>'effective_from')::date <= %s)
        AND (
          c.metadata->>'effective_to' IS NULL
          OR (c.metadata->>'effective_to')::date >= %s
        )
      )
    """
    return clause, (as_of, as_of)
