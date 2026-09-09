"""Unified Multilingual Language Detection Engine for ChatLaw backend.

Detects Indian languages (Tamil, Hindi, Telugu, Kannada, Malayalam, Bengali,
Gujarati, Punjabi, Urdu, Marathi, etc.) and English using Unicode script analysis,
code-switching detection, explicit language directives, and conversation memory.
"""

from __future__ import annotations

import re
from typing import Any

# Unicode script ranges for Indian Eighth Schedule languages & Latin
SCRIPT_RANGES: dict[str, re.Pattern[str]] = {
    "ta": re.compile(r"[\u0B80-\u0BFF]"),  # Tamil
    "hi": re.compile(r"[\u0900-\u097F]"),  # Devanagari (Hindi, Marathi, etc.)
    "te": re.compile(r"[\u0C00-\u0C7F]"),  # Telugu
    "kn": re.compile(r"[\u0C80-\u0CFF]"),  # Kannada
    "ml": re.compile(r"[\u0D00-\u0D7F]"),  # Malayalam
    "bn": re.compile(r"[\u0980-\u09FF]"),  # Bengali / Assamese
    "gu": re.compile(r"[\u0A80-\u0AFF]"),  # Gujarati
    "pa": re.compile(r"[\u0A00-\u0A7F]"),  # Gurmukhi (Punjabi)
    "ur": re.compile(r"[\u0600-\u06FF]"),  # Perso-Arabic (Urdu)
    "en": re.compile(r"[a-zA-Z]"),         # Latin (English)
}

# Common Marathi disambiguation markers written in Devanagari
MARATHI_MARKERS = re.compile(r"\b(?:आहे|नाही|झाला|केला|म्हणून|आणि|काय|कसे|करणे)\b")

# Common English legal loan words frequently mixed in Indian code-switching
COMMON_LOAN_WORDS = {
    "tenant", "landlord", "rent", "agreement", "lease", "deposit", "advance",
    "court", "police", "fir", "case", "lawyer", "advocate", "notice", "property",
    "flat", "house", "shop", "office", "salary", "bonus", "cheque", "check", "bank",
    "account", "bribe", "bail", "affidavit", "deed", "stamp", "registration",
    "sub", "registrar", "mutation", "patta", "chitta", "month", "months", "year",
    "years", "rupees", "rs", "inr", "lakh", "crore", "rights", "problem", "dispute",
    "contract", "service", "company", "owner", "pay", "payment", "due", "refund",
    "evict", "eviction", "vacate", "stay", "order", "document", "papers", "draft"
}

# Short neutral inputs that usually continue the prior conversation language
SHORT_NEUTRAL_WORDS = {
    "yes", "no", "ok", "okay", "fine", "sure", "done", "next", "proceed",
    "agree", "correct", "right", "cancel", "skip", "continue",
    "chennai", "delhi", "mumbai", "bengaluru", "bangalore", "hyderabad", "kolkata",
    "tamil nadu", "karnataka", "telangana", "andhra", "maharashtra", "kerala",
}

# Explicit directives where user requests a specific response language
DIRECTIVES: list[tuple[str, re.Pattern[str]]] = [
    (
        "en",
        re.compile(
            r"\b(?:(?:answer|reply|respond|speak|explain|talk|tell\s+me)\s+(?:in\s+)?english|in\s+english\b|english\s+(?:please|only))\b",
            re.I,
        ),
    ),
    (
        "ta",
        re.compile(
            r"(?:தமிழில்\s*(?:பதில்|சொல்லுங்கள்|சொல்லுங்க|விளக்குங்கள்|விளக்குங்க|பேசுங்கள்|பேசுங்க|கூறுங்கள்|கூறுங்க|பதிலளிக்கவும்|பதிலளி)|tamilil\s*(?:sol|bathil|pesu)|in\s+tamil\b)",
            re.I,
        ),
    ),
    (
        "hi",
        re.compile(
            r"(?:हिंदी\s*में\s*(?:बोलिए|बोलो|बताएं|बताओ|उत्तर|जवाब|समझाएं|समझाइए|लिखिए|लिखें)|hindi\s*me(?:in)?\s*(?:bolo|batao|samjhao|jawab)|in\s+hindi\b)",
            re.I,
        ),
    ),
    (
        "te",
        re.compile(
            r"(?:తెలుగులో\s*(?:చెప్పండి|సమాధానం|వివరించండి|రాయండి|మాట్లాడండి)|telugu\s*lo\s*(?:cheppandi|matladandi)|in\s+telugu\b)",
            re.I,
        ),
    ),
    (
        "kn",
        re.compile(r"(?:ಕನ್ನಡದಲ್ಲಿ\s*(?:ಹೇಳಿ|ಉತ್ತರಿಸಿ|ವಿವರಿಸಿ)|in\s+kannada\b)", re.I),
    ),
    (
        "ml",
        re.compile(r"(?:മലയാളത്തിൽ\s*(?:പറയൂ|മറുപടി|വിശദീകരിക്കൂ)|in\s+malayalam\b)", re.I),
    ),
    (
        "bn",
        re.compile(r"(?:বাংলায়\s*(?:বলুন|উত্তর|বোঝান)|in\s+bengali\b)", re.I),
    ),
]


def detect_language(
    text: str,
    input_type: str = "text",
    prior_language: str | None = None,
) -> dict[str, Any]:
    """Detect language of a message using script analysis, code-switching,

    directives, and prior conversation memory.
    """
    trimmed = (text or "").strip()

    if not trimmed:
        fallback = prior_language or "en"
        return {
            "detected_language": fallback,
            "confidence": 0.5,
            "input_type": input_type,
            "is_code_switched": False,
            "directive_applied": False,
        }

    # 1. Check for explicit directives
    for lang, pattern in DIRECTIVES:
        if pattern.search(trimmed):
            return {
                "detected_language": lang,
                "confidence": 0.99,
                "input_type": input_type,
                "is_code_switched": False,
                "directive_applied": True,
            }

    # 2. Count Unicode script characters
    counts: dict[str, int] = {}
    for lang, regex in SCRIPT_RANGES.items():
        counts[lang] = len(regex.findall(trimmed))

    indic_scripts = ["ta", "hi", "te", "kn", "ml", "bn", "gu", "pa", "ur"]
    total_indic = 0
    dominant_indic = "en"
    max_indic_count = 0

    for code in indic_scripts:
        count = counts.get(code, 0)
        total_indic += count
        if count > max_indic_count:
            max_indic_count = count
            dominant_indic = code

    latin_count = counts.get("en", 0)

    # Disambiguate Devanagari if Marathi
    if dominant_indic == "hi" and MARATHI_MARKERS.search(trimmed):
        dominant_indic = "mr"

    # 3. Indian Code-Switching handling:
    if total_indic > 0:
        is_code_switched = latin_count > 0
        lower_tokens = trimmed.lower().split()
        loan_word_count = sum(
            1 for token in lower_tokens if re.sub(r"[^a-z]", "", token) in COMMON_LOAN_WORDS
        )

        confidence = 0.98 if (total_indic >= 3 or (total_indic > 0 and loan_word_count > 0)) else 0.85
        return {
            "detected_language": dominant_indic,
            "confidence": confidence,
            "input_type": input_type,
            "is_code_switched": is_code_switched,
            "directive_applied": False,
        }

    # 4. Latin characters only / Numeric only
    is_numeric_only = bool(re.match(r"^[\d\s,.\-+₹$/]+$", trimmed))
    normalized_lower = re.sub(r"[^a-z0-9\s]", " ", trimmed.lower()).strip()
    is_short_neutral = (
        normalized_lower in SHORT_NEUTRAL_WORDS
        or is_numeric_only
        or (
            len(normalized_lower.split()) <= 2
            and any(w in SHORT_NEUTRAL_WORDS for w in normalized_lower.split())
        )
    )

    if is_short_neutral and prior_language and prior_language != "en":
        return {
            "detected_language": prior_language,
            "confidence": 0.85,
            "input_type": input_type,
            "is_code_switched": False,
            "directive_applied": False,
        }

    # 5. Standard English text
    if latin_count > 0:
        confidence = 0.98 if latin_count >= 5 else 0.75
        return {
            "detected_language": "en",
            "confidence": confidence,
            "input_type": input_type,
            "is_code_switched": False,
            "directive_applied": False,
        }

    # 6. Fallback
    fallback = prior_language or "en"
    return {
        "detected_language": fallback,
        "confidence": 0.5,
        "input_type": input_type,
        "is_code_switched": False,
        "directive_applied": False,
    }
