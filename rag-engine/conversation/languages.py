"""Eighth Schedule + English language catalog for ChatLaw."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# Embedded fallback if legal-data metadata is unavailable.
_FALLBACK_LANGUAGES: list[dict[str, Any]] = [
    {"code": "en", "name": "English", "nativeName": "English", "bcp47": "en-IN", "pinned": True},
    {"code": "as", "name": "Assamese", "nativeName": "অসমীয়া", "bcp47": "as-IN", "pinned": False},
    {"code": "bn", "name": "Bengali", "nativeName": "বাংলা", "bcp47": "bn-IN", "pinned": True},
    {"code": "brx", "name": "Bodo", "nativeName": "बड़ो", "bcp47": "brx-IN", "pinned": False},
    {"code": "doi", "name": "Dogri", "nativeName": "डोगरी", "bcp47": "doi-IN", "pinned": False},
    {"code": "gu", "name": "Gujarati", "nativeName": "ગુજરાતી", "bcp47": "gu-IN", "pinned": True},
    {"code": "hi", "name": "Hindi", "nativeName": "हिन्दी", "bcp47": "hi-IN", "pinned": True},
    {"code": "kn", "name": "Kannada", "nativeName": "ಕನ್ನಡ", "bcp47": "kn-IN", "pinned": True},
    {"code": "ks", "name": "Kashmiri", "nativeName": "کٲشُر", "bcp47": "ks-IN", "pinned": False},
    {"code": "kok", "name": "Konkani", "nativeName": "कोंकणी", "bcp47": "kok-IN", "pinned": False},
    {"code": "mai", "name": "Maithili", "nativeName": "मैथिली", "bcp47": "mai-IN", "pinned": False},
    {"code": "ml", "name": "Malayalam", "nativeName": "മലയാളം", "bcp47": "ml-IN", "pinned": True},
    {"code": "mni", "name": "Manipuri", "nativeName": "ꯃꯤꯇꯩꯂꯣꯟ", "bcp47": "mni-IN", "pinned": False},
    {"code": "mr", "name": "Marathi", "nativeName": "मराठी", "bcp47": "mr-IN", "pinned": True},
    {"code": "ne", "name": "Nepali", "nativeName": "नेपाली", "bcp47": "ne-IN", "pinned": False},
    {"code": "or", "name": "Odia", "nativeName": "ଓଡ଼ିଆ", "bcp47": "or-IN", "pinned": False},
    {"code": "pa", "name": "Punjabi", "nativeName": "ਪੰਜਾਬੀ", "bcp47": "pa-IN", "pinned": True},
    {"code": "sa", "name": "Sanskrit", "nativeName": "संस्कृतम्", "bcp47": "sa-IN", "pinned": False},
    {"code": "sat", "name": "Santali", "nativeName": "ᱥᱟᱱᱛᱟᱲᱤ", "bcp47": "sat-IN", "pinned": False},
    {"code": "sd", "name": "Sindhi", "nativeName": "سنڌي", "bcp47": "sd-IN", "pinned": False},
    {"code": "ta", "name": "Tamil", "nativeName": "தமிழ்", "bcp47": "ta-IN", "pinned": True},
    {"code": "te", "name": "Telugu", "nativeName": "తెలుగు", "bcp47": "te-IN", "pinned": True},
    {"code": "ur", "name": "Urdu", "nativeName": "اردو", "bcp47": "ur-IN", "pinned": False},
]


def _repo_root() -> Path:
    # rag-engine/conversation/languages.py → repo root
    return Path(__file__).resolve().parents[2]


def _metadata_path() -> Path:
    return _repo_root() / "legal-data" / "metadata" / "eighth-schedule-languages.json"


@lru_cache(maxsize=1)
def _load_languages() -> dict[str, dict[str, Any]]:
    path = _metadata_path()
    raw: list[dict[str, Any]]
    try:
        with path.open(encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, list) and loaded:
            raw = loaded
        else:
            raw = list(_FALLBACK_LANGUAGES)
    except (OSError, json.JSONDecodeError, TypeError):
        raw = list(_FALLBACK_LANGUAGES)
    catalog: dict[str, dict[str, Any]] = {}
    for entry in raw:
        code = str(entry.get("code", "")).strip().lower()
        if not code:
            continue
        catalog[code] = {
            "code": code,
            "name": str(entry.get("name") or code),
            "nativeName": str(entry.get("nativeName") or entry.get("name") or code),
            "bcp47": str(entry.get("bcp47") or code),
            "pinned": bool(entry.get("pinned", False)),
        }
    if "en" not in catalog:
        catalog["en"] = dict(_FALLBACK_LANGUAGES[0])
    return catalog


def normalize_language(code: str | None) -> str:
    """Return a known language code, defaulting to English."""
    if not code or not str(code).strip():
        return "en"
    raw = str(code).strip().lower().replace("_", "-")
    catalog = _load_languages()
    if raw in catalog:
        return raw
    primary = raw.split("-", 1)[0]
    if primary in catalog:
        return primary
    # Common aliases
    aliases = {"eng": "en", "hin": "hi", "tam": "ta", "tel": "te", "kan": "kn", "mal": "ml"}
    return aliases.get(primary, "en")


def get_language(code: str | None) -> dict[str, Any]:
    """Return the language catalog entry for *code* (normalized)."""
    normalized = normalize_language(code)
    return dict(_load_languages()[normalized])


def language_name(code: str | None) -> str:
    """Human-readable English name for the language."""
    return str(get_language(code)["name"])


def all_language_codes() -> tuple[str, ...]:
    return tuple(sorted(_load_languages().keys()))
