"""Research orchestration: statutes from the embeddings, then cases from the library or official sites."""

from __future__ import annotations

import hashlib
import logging
import os
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Sequence

from .articulation import articulate_law, summarize_judgment
from .discovery import COURT_LEVELS, CandidateCase, CaseDiscovery
from .law_reference import act_display_name, act_official_title, extract_law_references, split_law_key
from .store import CaseLawStore, LawLink, Provision, StoredCase, clean_statute_text
from .verification import fetch_document_text

logger = logging.getLogger(__name__)

MAX_PROVISIONS = 6
MIN_CASES = 3
SEMANTIC_LAW_KEY_SIMILARITY = 0.60
SIMILAR_CASE_THRESHOLD = float(os.getenv("RESEARCH_SIMILAR_CASE_THRESHOLD", "0.72"))
CACHE_TTL = timedelta(days=int(os.getenv("RESEARCH_CACHE_DAYS", "30")))
_LAW_KEY_RE = re.compile(r"^[A-Z0-9_]{2,40}(?::[0-9A-Z]{1,8})?$")

TextGenerator = Callable[[str], str]


@dataclass
class LawResearch:
    query: str
    provisions: list[Provision]
    law_keys: list[str]
    articulation: dict[str, Any] | None
    notes: list[str] = field(default_factory=list)
    articulation_error: str | None = None


@dataclass
class CaseResearch:
    query: str
    law_keys: list[str]
    cases: list[dict[str, Any]]
    source: str  # "library" | "official_search" | "mixed" | "none"
    discovery_ran: bool = False
    proposed: int = 0
    verified: int = 0
    message: str | None = None


def query_key(query: str, *parts: str) -> str:
    normalized = " ".join(re.sub(r"[^\w]+", " ", query.lower()).split())
    return hashlib.sha256("|".join([normalized, *parts]).encode()).hexdigest()


def valid_law_keys(keys: Sequence[str] | None) -> list[str]:
    return [key for key in dict.fromkeys(keys or []) if _LAW_KEY_RE.match(key)][:12]


def _is_fresh(value: Any) -> bool:
    if not isinstance(value, datetime):
        return False
    stamp = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - stamp < CACHE_TTL


def _vector_text(vector: Sequence[float]) -> str:
    return "[" + ",".join(repr(float(value)) for value in vector) + "]"


class ResearchService:
    def __init__(self, connection: Any, embedding_provider: Any, *,
                 discovery_factory: Callable[[], CaseDiscovery] | None = None,
                 generator: TextGenerator | None = None, searcher: Any = None):
        self.connection = connection
        self.store = CaseLawStore(connection)
        self.embedding_provider = embedding_provider
        if searcher is None:
            from retrieval.vector_search import VectorSearcher
            searcher = VectorSearcher(connection, embedding_provider)
        self.searcher = searcher
        self._discovery_factory = discovery_factory
        self._generator = generator

    # ----------------------------------------------------------------- statutes

    def law(self, query: str, *, articulate: bool = True) -> LawResearch:
        references = extract_law_references(query)
        titles = self.store.act_titles()
        provisions: list[Provision] = []
        notes: list[str] = []

        for ref in references:
            name = titles.get(ref.act_id, (None, act_display_name(ref.act_id)))[1]
            if ref.act_id not in titles:
                notes.append(f"{name} is not yet in the ChatLaw statute corpus, so its text cannot be "
                             "shown. Case law is still searched for it.")
                continue
            if ref.translated_from:
                notes.append(
                    f"{ref.translated_from} has been replaced; it corresponds to Section {ref.section}, {name}."
                    if ref.section else
                    f"{ref.translated_from} has been replaced by {name}; no single corresponding section is mapped."
                )
            if ref.section:
                provision = self.store.statute_section(ref.act_id, ref.section)
                if provision:
                    provisions.append(replace(provision, translated_from=ref.translated_from))
                else:
                    notes.append(f"Section {ref.section} of {name} was not found in the corpus text.")

        semantic = self._semantic_provisions(query, exclude={p.law_key for p in provisions})
        provisions.extend(semantic[: max(0, MAX_PROVISIONS - len(provisions))])

        law_keys = [ref.law_key for ref in references]
        law_keys += [
            p.law_key for p in semantic[:3]
            if p.section and (p.similarity or 0) >= SEMANTIC_LAW_KEY_SIMILARITY
        ]
        law_keys = valid_law_keys(law_keys)

        articulation, error = None, None
        if articulate and provisions:
            articulation, error = self._articulation(query, provisions, law_keys)
        return LawResearch(query, provisions, law_keys, articulation, notes, error)

    def _semantic_provisions(self, query: str, *, exclude: set[str]) -> list[Provision]:
        try:
            response = self.searcher.search(query, top_k=10, min_similarity=0.5)
        except Exception:
            logger.exception("[RESEARCH] semantic statute search failed")
            return []
        provisions: list[Provision] = []
        seen = set(exclude)
        for result in response.results:
            act_id = (result.metadata or {}).get("act_id") or self.store.act_for_document(result.document_id)
            if not act_id:
                continue
            section = (result.section_number or "").upper() or None
            key = f"{act_id}:{section}" if section else f"{act_id}#{result.chunk_id}"
            if key in seen:
                continue
            seen.add(key)
            full = self.store.statute_section(act_id, section) if section else None
            provisions.append(replace(full, matched_by="semantic", similarity=result.similarity) if full else Provision(
                act_id=act_id, act_title=result.document_title,
                short_title=self.store.act_titles().get(act_id, (None, result.document_title))[1],
                section=section, text=clean_statute_text(result.content), chapter=result.chapter,
                page_number=result.page_number, source_url=result.source_url,
                similarity=result.similarity,
            ))
        return provisions

    def _articulation(self, query: str, provisions: Sequence[Provision],
                      law_keys: Sequence[str]) -> tuple[dict[str, Any] | None, str | None]:
        key = query_key(query, "law")
        cached = self.store.get_query(key)
        if cached and cached.get("articulation"):
            return cached["articulation"], None
        if self._generator is None:
            return None, "Explanations are unavailable because the language model is not configured."
        try:
            articulation = articulate_law(query, provisions, self._generator)
        except Exception:
            logger.exception("[RESEARCH] articulation failed")
            return None, "The explanation could not be generated. The statutory text is shown below."
        if articulation:
            self.store.save_query(key, query, law_keys=law_keys, articulation=articulation)
            self.store.commit()
        return articulation, None

    # -------------------------------------------------------------------- cases

    def cases(self, query: str, *, law_keys: Sequence[str] | None = None,
              court_levels: Sequence[str] = COURT_LEVELS, refresh: bool = False,
              limit: int = 8) -> CaseResearch:
        levels = [level for level in court_levels if level in COURT_LEVELS] or list(COURT_LEVELS)
        explicit = [ref.law_key for ref in extract_law_references(query)]
        keys = valid_law_keys(law_keys) if law_keys is not None else self.law(query, articulate=False).law_keys
        key = query_key(query, "cases", *sorted(levels))
        cached = self.store.get_query(key)

        library = self._library_cases(query, keys, levels, cached)
        # Sections named in the query decide whether this law was already searched;
        # otherwise the closest semantic matches do.
        primary = [k for k in explicit if k in keys] or keys[:2]
        fresh_laws = self.store.fresh_lookups(primary, CACHE_TTL)
        law_already_searched = bool(primary) and all(k in fresh_laws for k in primary)
        query_already_searched = bool(cached and _is_fresh(cached.get("discoveredAt")))

        result = CaseResearch(query, keys, [], "none")
        new_ids: list[str] = []
        if refresh or (len(library) < MIN_CASES and not query_already_searched and not law_already_searched):
            new_ids = self._discover_for_query(query, keys, primary, levels, result)
            if new_ids:
                library = self._library_cases(query, keys, levels, self.store.get_query(key)) or library

        self.store.count_hits(keys)
        self.store.commit()

        ranked = self._rank(library, explicit=explicit, keys=keys, new_ids=set(new_ids))[:limit]
        result.cases = [{**case.as_dict(), "similarity": case.similarity,
                         "is_new": case.id in new_ids} for case in ranked]
        if not ranked:
            result.source = "none"
            result.message = result.message or (
                "No judgment with a verified official copy was found for this research yet."
            )
        elif new_ids and len(new_ids) < len(ranked):
            result.source = "mixed"
        elif new_ids:
            result.source = "official_search"
        else:
            result.source = "library"
        return result

    def _library_cases(self, query: str, keys: Sequence[str], levels: Sequence[str],
                       cached: dict[str, Any] | None) -> list[StoredCase]:
        merged: dict[str, StoredCase] = {}
        if cached and isinstance(cached.get("caseIds"), list):
            for case in self.store.cases_by_ids([str(x) for x in cached["caseIds"]]):
                if case.court_level in levels:
                    merged[case.id] = case
        for case in self.store.cases_for_law_keys(keys, court_levels=levels, limit=20):
            merged.setdefault(case.id, case)
        try:
            vector = self.searcher._get_embedding(query)
            for case in self.store.similar_cases(_vector_text(vector), court_levels=levels, limit=8,
                                                 min_similarity=SIMILAR_CASE_THRESHOLD):
                if case.id in merged:
                    merged[case.id].similarity = case.similarity
                else:
                    merged[case.id] = case
        except Exception:
            logger.warning("[RESEARCH] similar-case search unavailable", exc_info=True)
        return list(merged.values())

    @staticmethod
    def _rank(cases: Sequence[StoredCase], *, explicit: Sequence[str], keys: Sequence[str],
              new_ids: set[str]) -> list[StoredCase]:
        explicit_set, key_set = set(explicit), set(keys)
        court_weight = {"SUPREME_COURT": 0.6, "HIGH_COURT": 0.3}

        def score(case: StoredCase) -> float:
            linked = set(case.law_keys)
            value = 3.0 if linked & explicit_set else (2.0 if linked & key_set else 0.0)
            value += 3.0 * (case.similarity or 0.0)
            value += 1.5 if case.id in new_ids else 0.0
            value += 1.0 if case.is_landmark else 0.0
            return value + court_weight.get(case.court_level, 0.0)

        return sorted(cases, key=score, reverse=True)

    def _discover_for_query(self, query: str, keys: Sequence[str], primary: Sequence[str],
                            levels: Sequence[str], result: CaseResearch) -> list[str]:
        result.discovery_ran = True
        provisions = [p for p in (self._provision_for_key(k) for k in keys[:3]) if p]
        context = "\n\n".join(f"{p.label}:\n{p.text[:1800]}" for p in provisions)
        try:
            discovery = self._discovery()
            found = discovery.discover(topic=query, provisions_context=context, court_levels=levels,
                                       max_cases=6, landmark=False)
        except Exception:
            logger.exception("[RESEARCH] official case search failed")
            for k in primary:
                self.store.record_lookup(k, status="FAILED", mode="QUERY", case_count=0, proposed_count=0)
            self.store.commit()
            result.message = "Official court sources could not be searched right now. Showing saved cases only."
            return []

        result.proposed = len(found.cases) + len(found.rejected)
        result.verified = len(found.cases)
        saved = [
            self.save_discovered(case, origin="DISCOVERED", primary_keys=list(primary[:1]), model=found.model)
            for case in found.cases
        ]
        new_ids = [case_id for case_id, _ in saved]
        for k in primary:
            linked = sum(1 for _, linked_keys in saved if k in linked_keys)
            self.store.record_lookup(k, status="FOUND" if linked else "NONE_FOUND", mode="QUERY",
                                     case_count=linked, proposed_count=result.proposed)
        self.store.save_query(query_key(query, "cases", *sorted(levels)), query, law_keys=keys,
                              case_ids=new_ids, discovered=True)
        self.store.commit()
        if result.proposed and not new_ids:
            result.message = (f"{result.proposed} possible judgments were found, but none had an official "
                              "government copy that could be verified, so they are not shown.")
        return new_ids

    def save_discovered(self, case: CandidateCase, *, origin: str, primary_keys: Sequence[str],
                        landmark_key: str | None = None, model: str | None = None) -> tuple[str, set[str]]:
        """Store a verified case, linking it to the provisions it says it applies.

        Returns the case id and the law keys it was linked to.
        """
        claimed: set[str] = set()
        for provision in (*case.provisions, case.predecessor_provision):
            for ref in extract_law_references(provision or ""):
                if ref.section:
                    claimed.add(ref.law_key)
        links = [LawLink(k, note=case.relevance or None) for k in sorted(claimed) if k != landmark_key]
        if landmark_key:
            links.append(LawLink(landmark_key, is_landmark=True, note=case.relevance or None))
        elif not claimed & set(primary_keys):
            links.extend(LawLink(k, note=case.relevance or None) for k in primary_keys)
        acts = []
        for link in links:
            acts.append(act_official_title(split_law_key(link.law_key)[0]))
        embedding_text = " ".join(filter(None, [
            case.title, case.court, "; ".join(case.provisions), case.summary, case.holding,
        ]))[:4000]
        try:
            embedding = self.embedding_provider.embed(embedding_text)
        except Exception:
            logger.warning("[RESEARCH] case embedding failed; storing without it", exc_info=True)
            embedding = None
        case_id = self.store.save_case(case, origin=origin, acts=acts, links=links,
                                       embedding_text=embedding_text, embedding=embedding, model=model)
        return case_id, {link.law_key for link in links}

    def _provision_for_key(self, key: str) -> Provision | None:
        act_id, section = split_law_key(key)
        return self.store.statute_section(act_id, section) if section else None

    def _discovery(self) -> CaseDiscovery:
        if self._discovery_factory is None:
            raise RuntimeError("Case discovery is not configured")
        return self._discovery_factory()

    # ------------------------------------------------------------ landmark seed

    def seed_law(self, key: str, *, topic: str, provisions_context: str,
                 court_levels: Sequence[str] = ("SUPREME_COURT", "HIGH_COURT"),
                 max_cases: int = 4, refresh: bool = False,
                 link_budget_seconds: float = 120.0) -> dict[str, Any]:
        """Find and store the landmark judgments for one law key (used by the seed script)."""
        if not refresh and key in self.store.fresh_lookups([key], CACHE_TTL):
            return {"law_key": key, "status": "SKIPPED", "stored": 0, "proposed": 0}
        try:
            found = self._discovery().discover(topic=topic, provisions_context=provisions_context,
                                               court_levels=court_levels, max_cases=max_cases,
                                               landmark=True, link_budget_seconds=link_budget_seconds)
        except Exception as exc:
            self.connection.rollback()
            self.store.record_lookup(key, status="FAILED", mode="LANDMARK", case_count=0, proposed_count=0)
            self.store.commit()
            return {"law_key": key, "status": "FAILED", "stored": 0, "proposed": 0, "error": str(exc)[:300]}
        stored = [self.save_discovered(case, origin="SEED", primary_keys=[key], landmark_key=key,
                                       model=found.model) for case in found.cases]
        status = "FOUND" if stored else "NONE_FOUND"
        proposed = len(found.cases) + len(found.rejected)
        self.store.record_lookup(key, status=status, mode="LANDMARK", case_count=len(stored),
                                 proposed_count=proposed)
        self.store.commit()
        return {"law_key": key, "status": status, "stored": len(stored), "proposed": proposed,
                "titles": [case.title for case in found.cases]}

    # ------------------------------------------------------------------ browse

    def case_summary(self, case_id: str) -> dict[str, Any] | None:
        cases = self.store.cases_by_ids([case_id])
        if not cases:
            return None
        case = cases[0]
        if case.metadata.get("detailed_summary"):
            return case.metadata["detailed_summary"]
        if self._generator is None:
            raise RuntimeError("Judgment summaries need the language model to be configured")
        _, text = fetch_document_text(case.source_url, max_pages=30)
        summary = summarize_judgment(case.title, case.court, text, self._generator)
        if summary:
            self.store.save_detailed_summary(case.id, summary)
            self.store.commit()
        return summary

    def law_cases(self, key: str, court_levels: Sequence[str] = COURT_LEVELS, limit: int = 20) -> list[dict[str, Any]]:
        keys = valid_law_keys([key])
        return [case.as_dict() for case in self.store.cases_for_law_keys(keys, court_levels=court_levels, limit=limit)]

    def close(self) -> None:
        try:
            self.connection.rollback()  # end any read-only transaction before returning to the pool
        finally:
            self.connection.close()


def create_research_service() -> ResearchService:
    from embeddings.provider import create_embedding_provider
    from retrieval.vector_search import connect_from_environment

    connection = connect_from_environment()
    try:
        provider = create_embedding_provider()
    except Exception:
        connection.close()
        raise

    def generate(prompt: str) -> str:
        from generation.gemini import GeminiGenerator
        return GeminiGenerator().generate_text(prompt, thinking_level="low").answer

    has_model = bool(os.getenv("GEMINI_API_KEY", "").strip() and os.getenv("GEMINI_GENERATION_MODEL", "").strip())
    return ResearchService(connection, provider, discovery_factory=CaseDiscovery,
                           generator=generate if has_model else None)
