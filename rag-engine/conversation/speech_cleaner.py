"""Deterministic speech cleaner for Text-to-Speech preparation.

Converts legal markdown and formatted answers into natural spoken prose
without changing the substantive legal meaning.
"""

from __future__ import annotations

import re

ONES = [
    "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen"
]

TENS = [
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"
]


def _three_digits(num: int) -> str:
    if num == 0:
        return ""
    hundreds = num // 100
    rem = num % 100
    res = f"{ONES[hundreds]} hundred" if hundreds > 0 else ""
    if rem > 0:
        if res:
            res += " "
        if rem < 20:
            res += ONES[rem]
        else:
            t = rem // 10
            u = rem % 10
            res += f"{TENS[t]} {ONES[u]}".strip()
    return res.strip()


def number_to_indian_words(num: int) -> str:
    if num <= 0:
        return "zero" if num == 0 else ""
    crore = num // 10_000_000
    rem = num % 10_000_000
    lakh = rem // 100_000
    rem = rem % 100_000
    thousand = rem // 1000
    rem = rem % 1000

    parts = []
    if crore > 0:
        parts.append(f"{_three_digits(crore)} crore")
    if lakh > 0:
        parts.append(f"{_three_digits(lakh)} lakh")
    if thousand > 0:
        parts.append(f"{_three_digits(thousand)} thousand")
    if rem > 0:
        parts.append(_three_digits(rem))
    return " ".join(parts).strip()


ACT_ABBREVIATIONS = {
    "bns": "Bharatiya Nyaya Sanhita",
    "bnss": "Bharatiya Nagarik Suraksha Sanhita",
    "bsa": "Bharatiya Sakshya Adhiniyam",
    "ipc": "Indian Penal Code",
    "crpc": "Code of Criminal Procedure",
    "cpc": "Code of Civil Procedure",
    "nia": "Negotiable Instruments Act",
    "tpa": "Transfer of Property Act",
    "ica": "Indian Contract Act",
}


def clean_speech_text(text: str) -> str:
    """Prepare assistant answer for text-to-speech audio synthesis.

    Strips citations, URLs, and markdown formatting, and normalizes
    currency, legal sections, and abbreviations.
    """
    if not text or not text.strip():
        return ""

    t = text.strip()

    # 1. Remove citations: [SOURCE 1], [1], [2], (1)
    t = re.sub(r"\[SOURCE\s+\d+\]", "", t, flags=re.I)
    t = re.sub(r"\[\d+\]", "", t)

    # 2. Remove URLs
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"www\.\S+", "", t)

    # 3. Currency normalization: ₹18,000 / Rs. 18,000 / 18000 INR
    def _replace_currency(m: re.Match) -> str:
        amt_str = m.group(1).replace(",", "")
        try:
            amt = int(amt_str)
            words = number_to_indian_words(amt)
            return f"{words} rupees"
        except ValueError:
            return m.group(0)

    t = re.sub(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", _replace_currency, t, flags=re.I)

    # 4. Section normalization: Section 303(2) BNS -> Section 303, sub-section 2 of the Bharatiya Nyaya Sanhita
    def _replace_section(m: re.Match) -> str:
        sec = m.group(1)
        subsec = m.group(2)
        act = (m.group(3) or "").strip().lower()
        act_name = ACT_ABBREVIATIONS.get(act, m.group(3) or "")
        res = f"Section {sec}"
        if subsec:
            res += f", sub-section {subsec}"
        if act_name:
            res += f" of the {act_name}"
        return res

    t = re.sub(
        r"\b(?:Section|Sec\.?)\s+(\d+)(?:\s*\(\s*(\d+)\s*\))?(?:\s+(BNS|BNSS|BSA|IPC|CrPC|CPC|NIA|TPA|ICA))?\b",
        _replace_section,
        t,
        flags=re.I,
    )

    # 5. Remove remaining markdown syntax
    t = re.sub(r"^#{1,6}\s+", "", t, flags=re.M)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)
    t = re.sub(r"^\s*\d+\.\s+", "", t, flags=re.M)
    t = re.sub(r"\|", " ", t)
    t = re.sub(r"-{3,}", " ", t)

    # 6. Normalize whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t
