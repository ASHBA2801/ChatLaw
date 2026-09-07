"""Local clarification interview (slot-filling) before grounded RAG generation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .domains import DOMAINS, Domain, get_domain
from .languages import normalize_language

MAX_ROUNDS = 3

_PROCEED_PHRASES = (
    "just answer",
    "answer anyway",
    "skip",
    "go ahead",
    "no more questions",
    "proceed",
    "don't ask",
    "dont ask",
)

# Specific legal-lookup patterns: section/Act/BNS/IPC style questions.
_LOOKUP_PATTERNS = (
    re.compile(r"\bsection\s+\d+", re.I),
    re.compile(r"\bsec\.?\s*\d+", re.I),
    re.compile(r"\b(?:under|of)\s+(?:the\s+)?(?:bns|ipc|crpc|cpc|bnss|bsa)\b", re.I),
    re.compile(r"\b(?:bns|ipc|crpc|cpc|bnss|bsa)\s*(?:section|sec\.?)?\s*\d+", re.I),
    re.compile(r"\b(?:indian\s+penal\s+code|bharatiya\s+nyaya\s+sanhita)\b", re.I),
    re.compile(r"\bact[,\s]+(?:19|20)\d{2}\b", re.I),
    re.compile(r"\bwhat\s+is\s+(?:the\s+)?(?:punishment|definition|meaning)\s+(?:for|of)\b", re.I),
)


@dataclass(frozen=True)
class InterviewResult:
    action: str  # "clarify" | "answer"
    question: str | None
    state: dict[str, Any]
    assembled_situation: str


def _questions_path() -> Path:
    return Path(__file__).resolve().parent / "questions.json"


@lru_cache(maxsize=1)
def _load_questions() -> dict[str, dict[str, dict[str, str]]]:
    path = _questions_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        return {}
    return data


def _question_text(domain_id: str, slot_id: str, language: str) -> str:
    lang = normalize_language(language)
    questions = _load_questions()
    by_slot = questions.get(domain_id, {}).get(slot_id, {})
    if lang in by_slot and by_slot[lang].strip():
        return by_slot[lang].strip()
    return (by_slot.get("en") or f"Could you tell me more about {slot_id.replace('_', ' ')}?").strip()


def _empty_state(
    *,
    domain: str | None = None,
    original_query: str = "",
    slots: dict[str, str] | None = None,
    asked: list[str] | None = None,
    round_n: int = 0,
    assumptions: list[str] | None = None,
    pending: bool = False,
) -> dict[str, Any]:
    return {
        "domain": domain,
        "round": round_n,
        "max_rounds": MAX_ROUNDS,
        "slots": dict(slots or {}),
        "asked": list(asked or []),
        "assumptions": list(assumptions or []),
        "original_query": original_query,
        "pending": pending,
    }


def _normalize_prior(prior: dict[str, Any] | None) -> dict[str, Any] | None:
    if not prior or not isinstance(prior, dict):
        return None
    pending = prior.get("pending")
    return {
        "domain": prior.get("domain"),
        "round": int(prior.get("round") or 0),
        "max_rounds": int(prior.get("max_rounds") or MAX_ROUNDS),
        "slots": dict(prior.get("slots") or {}),
        "asked": list(prior.get("asked") or []),
        "assumptions": list(prior.get("assumptions") or []),
        "original_query": str(prior.get("original_query") or ""),
        "pending": pending if isinstance(pending, bool) else None,
    }


def _is_lookup_question(message: str) -> bool:
    return any(pattern.search(message or "") for pattern in _LOOKUP_PATTERNS)


def active_interview_from_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Resume an interview only when the last assistant turn asked a clarification."""
    if not metadata or not isinstance(metadata, dict):
        return None
    if metadata.get("kind") != "clarification":
        return None
    return interview_state_from_metadata(metadata)


class InterviewManager:
    """Deterministic domain detect + slot fill; never calls Gemini."""

    MAX_ROUNDS = MAX_ROUNDS

    def detect_domain(self, message: str) -> tuple[str | None, float]:
        text = (message or "").lower()
        if not text.strip():
            return None, 0.0
        best_id: str | None = None
        best_hits = 0
        for domain in DOMAINS.values():
            hits = 0
            for kw in domain.keywords:
                kw_l = kw.lower()
                if kw_l.isascii() and re.fullmatch(r"[a-z0-9][a-z0-9\s\-']*", kw_l):
                    if re.search(rf"(?<![a-z0-9]){re.escape(kw_l)}(?![a-z0-9])", text):
                        hits += 1
                elif kw_l in text or kw_l in (message or ""):
                    hits += 1
            if hits > best_hits:
                best_hits = hits
                best_id = domain.id
        if best_hits <= 0:
            return None, 0.0
        # One keyword hit → medium; two+ → high. Confidence in [0, 1].
        confidence = 0.55 if best_hits == 1 else min(1.0, 0.55 + 0.15 * best_hits)
        return best_id, confidence

    def should_skip_interview(self, message: str, *, confidence: float | None = None) -> bool:
        text = (message or "").strip()
        if not text:
            return True
        lowered = text.lower()
        if any(phrase in lowered for phrase in _PROCEED_PHRASES):
            return True
        if _is_lookup_question(text):
            return True
        if confidence is not None and confidence < 0.5:
            return True
        return False

    def extract_slots(
        self,
        message: str,
        domain: Domain | str | None,
        asked_slot: str | None = None,
    ) -> dict[str, str]:
        domain_obj = domain if isinstance(domain, Domain) else get_domain(domain)
        if domain_obj is None:
            return {}
        text = (message or "").strip()
        if not text:
            return {}
        lowered = text.lower()
        filled: dict[str, str] = {}

        def _contains(token: str) -> bool:
            token_l = token.lower()
            if token_l.isascii() and re.fullmatch(r"[a-z0-9][a-z0-9\s\-']*", token_l):
                return re.search(rf"(?<![a-z0-9]){re.escape(token_l)}(?![a-z0-9])", lowered) is not None
            return token_l in text or token_l in lowered

        for slot_id, values in domain_obj.slot_values.items():
            for value in values:
                if _contains(value):
                    filled[slot_id] = value if value.isascii() else value
                    break

        # Heuristic: landlord/tenant style role phrases.
        if "party_role" in domain_obj.slots and "party_role" not in filled:
            if re.search(r"\b(?:i'?m|i am|am)\s+(?:a\s+)?(?:the\s+)?tenant\b", lowered):
                filled["party_role"] = "tenant"
            elif re.search(r"\b(?:i'?m|i am|am)\s+(?:a\s+)?(?:the\s+)?landlord\b", lowered):
                filled["party_role"] = "landlord"
            elif re.search(r"\b(?:i'?m|i am|am)\s+(?:a\s+)?(?:an\s+)?employee\b", lowered):
                filled["party_role"] = "employee"
            elif re.search(r"\b(?:i'?m|i am|am)\s+(?:a\s+)?(?:an\s+)?employer\b", lowered):
                filled["party_role"] = "employer"

        if "written_agreement" in domain_obj.slots and "written_agreement" not in filled:
            if re.search(r"\b(?:no|don'?t|do not)\b.*\b(?:agreement|contract|written)\b", lowered) or \
               re.search(r"\b(?:agreement|contract)\b.*\b(?:no|don'?t|oral|verbal)\b", lowered):
                filled["written_agreement"] = "no"
            elif re.search(r"\b(?:yes|have|written|signed)\b.*\b(?:agreement|contract|lease)\b", lowered) or \
                 re.search(r"\b(?:agreement|contract|lease)\b.*\b(?:yes|written|signed)\b", lowered):
                filled["written_agreement"] = "yes"

        if "written_contract" in domain_obj.slots and "written_contract" not in filled:
            if re.search(r"\b(?:no|don'?t|oral|verbal)\b", lowered) and "contract" in lowered:
                filled["written_contract"] = "no"
            elif re.search(r"\b(?:yes|written|signed|appointment)\b", lowered) and "contract" in lowered:
                filled["written_contract"] = "yes"

        # If we asked a specific slot and nothing matched, treat a short reply as the value.
        if asked_slot and asked_slot not in filled and text:
            cleaned = " ".join(text.split())
            vague = re.search(
                r"^(?:not sure|i don'?t know|dont know|unclear|maybe|idk|no idea)(?:\s+yet)?(?:\s+reply\s+\d+)?$",
                cleaned,
                re.I,
            )
            if len(cleaned) <= 160 and not vague:
                filled[asked_slot] = cleaned

        return filled

    def next_question(
        self,
        domain: Domain | str | None,
        slots: dict[str, str],
        language: str = "en",
    ) -> tuple[str, str] | None:
        domain_obj = domain if isinstance(domain, Domain) else get_domain(domain)
        if domain_obj is None:
            return None
        for slot_id in domain_obj.slots:
            if slot_id not in slots or not str(slots.get(slot_id) or "").strip():
                return slot_id, _question_text(domain_obj.id, slot_id, language)
        return None

    def _sufficient(self, domain: Domain, slots: dict[str, str]) -> bool:
        return all(str(slots.get(slot) or "").strip() for slot in domain.required_slots)

    def _assumptions(self, domain: Domain, slots: dict[str, str]) -> list[str]:
        missing = [
            slot.replace("_", " ")
            for slot in domain.slots
            if not str(slots.get(slot) or "").strip()
        ]
        if not missing:
            return []
        return [f"Details not provided for: {', '.join(missing)}."]

    def assemble_situation(
        self,
        *,
        original_query: str,
        domain: Domain | None,
        slots: dict[str, str],
        assumptions: list[str] | None = None,
    ) -> str:
        parts = [original_query.strip()] if original_query and original_query.strip() else []
        if domain is not None:
            parts.append(f"Domain: {domain.id}.")
        if slots:
            slot_bits = [f"{key.replace('_', ' ')}: {value}" for key, value in slots.items() if value]
            if slot_bits:
                parts.append("Known facts: " + "; ".join(slot_bits) + ".")
        if assumptions:
            parts.append("Assumptions: " + " ".join(assumptions))
        return " ".join(parts).strip() or (original_query or "").strip()

    def _is_topic_change(self, text: str, prior_domain: str | None) -> bool:
        if _is_lookup_question(text):
            return True
        new_domain_id, confidence = self.detect_domain(text)
        return bool(
            new_domain_id
            and prior_domain
            and new_domain_id != prior_domain
            and confidence >= 0.5
        )

    def _should_continue(self, prior: dict[str, Any], text: str) -> bool:
        if not prior.get("domain"):
            return False
        if self._is_topic_change(text, str(prior.get("domain") or "") or None):
            return False
        pending = prior.get("pending")
        if pending is False:
            return False
        if pending is True:
            return True
        # Legacy rows: only resume when a clarification was actually asked.
        return bool(prior.get("asked"))

    def process_turn(
        self,
        message: str,
        language: str = "en",
        prior_interview_state: dict[str, Any] | None = None,
    ) -> InterviewResult:
        lang = normalize_language(language)
        text = (message or "").strip()
        prior = _normalize_prior(prior_interview_state)

        # Continue only while a clarification is still awaiting a reply.
        if prior and self._should_continue(prior, text):
            domain = get_domain(str(prior["domain"]))
            if domain is not None:
                asked = list(prior.get("asked") or [])
                last_asked = asked[-1] if asked else None
                slots = dict(prior.get("slots") or {})
                slots.update(self.extract_slots(text, domain, last_asked))
                original = str(prior.get("original_query") or text)
                round_n = int(prior.get("round") or 0)
                max_rounds = int(prior.get("max_rounds") or MAX_ROUNDS)

                if any(phrase in text.lower() for phrase in _PROCEED_PHRASES):
                    assumptions = self._assumptions(domain, slots)
                    state = _empty_state(
                        domain=domain.id,
                        original_query=original,
                        slots=slots,
                        asked=asked,
                        round_n=round_n,
                        assumptions=assumptions,
                    )
                    return InterviewResult(
                        action="answer",
                        question=None,
                        state=state,
                        assembled_situation=self.assemble_situation(
                            original_query=original, domain=domain, slots=slots, assumptions=assumptions,
                        ),
                    )

                sufficient = self._sufficient(domain, slots)
                nxt = None if sufficient else self.next_question(domain, slots, lang)
                # Answer when facts are enough, nothing left to ask, or round budget is spent.
                if sufficient or nxt is None or round_n >= max_rounds:
                    assumptions = [] if sufficient else self._assumptions(domain, slots)
                    state = _empty_state(
                        domain=domain.id,
                        original_query=original,
                        slots=slots,
                        asked=asked,
                        round_n=round_n,
                        assumptions=assumptions,
                    )
                    return InterviewResult(
                        action="answer",
                        question=None,
                        state=state,
                        assembled_situation=self.assemble_situation(
                            original_query=original, domain=domain, slots=slots, assumptions=assumptions,
                        ),
                    )

                slot_id, question = nxt
                new_asked = asked + [slot_id]
                new_round = round_n + 1
                state = _empty_state(
                    domain=domain.id,
                    original_query=original,
                    slots=slots,
                    asked=new_asked,
                    round_n=new_round,
                    pending=True,
                )
                return InterviewResult(
                    action="clarify",
                    question=question,
                    state=state,
                    assembled_situation=self.assemble_situation(
                        original_query=original, domain=domain, slots=slots,
                    ),
                )

        # Fresh turn.
        domain_id, confidence = self.detect_domain(text)
        if self.should_skip_interview(text, confidence=confidence) or domain_id is None:
            state = _empty_state(domain=domain_id, original_query=text)
            return InterviewResult(
                action="answer",
                question=None,
                state=state,
                assembled_situation=text,
            )

        domain = get_domain(domain_id)
        assert domain is not None
        slots = self.extract_slots(text, domain, None)

        if self._sufficient(domain, slots):
            state = _empty_state(domain=domain.id, original_query=text, slots=slots)
            return InterviewResult(
                action="answer",
                question=None,
                state=state,
                assembled_situation=self.assemble_situation(
                    original_query=text, domain=domain, slots=slots,
                ),
            )

        nxt = self.next_question(domain, slots, lang)
        if nxt is None:
            state = _empty_state(domain=domain.id, original_query=text, slots=slots)
            return InterviewResult(
                action="answer",
                question=None,
                state=state,
                assembled_situation=self.assemble_situation(
                    original_query=text, domain=domain, slots=slots,
                ),
            )

        slot_id, question = nxt
        state = _empty_state(
            domain=domain.id,
            original_query=text,
            slots=slots,
            asked=[slot_id],
            round_n=1,
            pending=True,
        )
        return InterviewResult(
            action="clarify",
            question=question,
            state=state,
            assembled_situation=self.assemble_situation(
                original_query=text, domain=domain, slots=slots,
            ),
        )


def interview_state_from_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Pull persistable interview state from assistant message metadata."""
    if not metadata or not isinstance(metadata, dict):
        return None
    interview = metadata.get("interview")
    if isinstance(interview, dict):
        return interview
    # Flat metadata shape used when kind=clarification.
    if metadata.get("kind") == "clarification" and metadata.get("domain") is not None:
        return {
            "domain": metadata.get("domain"),
            "round": metadata.get("round", 0),
            "max_rounds": metadata.get("max_rounds", MAX_ROUNDS),
            "slots": metadata.get("slots") or {},
            "asked": metadata.get("asked") or [],
            "assumptions": metadata.get("assumptions") or [],
            "original_query": metadata.get("original_query"),
            "pending": True,
        }
    return None
