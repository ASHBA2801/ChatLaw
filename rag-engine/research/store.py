"""PostgreSQL access for statute sections and the verified case-law library."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Sequence
from urllib.parse import urlsplit

from .discovery import CandidateCase
from .law_reference import act_display_name, act_official_title, law_key, split_law_key

MAX_SECTION_CHARS = 9000
# Gazette page furniture that the PDF extraction leaves inside section text.
_GAZETTE_NOISE = re.compile(
    r"^\s*(?:[_\-–—]{5,}|THE GAZETTE OF INDIA EXTRAORDINARY|\[?PART II\b.*|SEC\.\s*\d+\]|\d{1,4})\s*$",
    re.IGNORECASE,
)


def clean_statute_text(text: str) -> str:
    lines = [line for line in text.splitlines() if not _GAZETTE_NOISE.match(line)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


@dataclass(frozen=True)
class Provision:
    act_id: str
    act_title: str
    short_title: str
    section: str | None
    text: str
    chapter: str | None = None
    page_number: int | None = None
    source_url: str | None = None
    similarity: float | None = None
    matched_by: str = "semantic"  # "reference" | "semantic"
    translated_from: str | None = None

    @property
    def law_key(self) -> str:
        return law_key(self.act_id, self.section)

    @property
    def label(self) -> str:
        return f"Section {self.section}, {self.short_title}" if self.section else self.short_title


@dataclass(frozen=True)
class CorpusAct:
    act_id: str
    title: str
    short_title: str
    domain: str | None
    source_url: str | None
    document_ids: tuple[str, ...]


@dataclass(frozen=True)
class LawLink:
    law_key: str
    is_landmark: bool = False
    note: str | None = None


@dataclass
class StoredCase:
    id: str
    title: str
    court: str
    court_level: str
    jurisdiction: str
    judgment_date: str | None
    case_number: str | None
    citation: str | None
    petitioner: str | None
    respondent: str | None
    source_url: str
    source_authority: str
    summary: str
    holding: str
    primary_issue: str
    metadata: dict[str, Any]
    law_keys: list[str] = field(default_factory=list)
    is_landmark: bool = False
    relevance_note: str | None = None
    similarity: float | None = None

    def as_dict(self) -> dict[str, Any]:
        meta = self.metadata or {}
        return {
            "id": self.id,
            "title": self.title,
            "court": self.court,
            "court_level": self.court_level,
            "jurisdiction": self.jurisdiction,
            "judgment_date": self.judgment_date,
            "case_number": self.case_number,
            "citation": self.citation,
            "petitioner": self.petitioner,
            "respondent": self.respondent,
            "source_url": self.source_url,
            "source_authority": self.source_authority,
            "summary": self.summary,
            "holding": self.holding,
            "relevance": self.relevance_note or meta.get("relevance") or self.primary_issue,
            "law_keys": self.law_keys,
            "is_landmark": self.is_landmark,
            "origin": meta.get("origin", "DISCOVERED"),
            "verification": meta.get("verification"),
            "predecessor_provision": meta.get("predecessor_provision"),
            "provisions": meta.get("provisions", []),
            "detailed_summary": meta.get("detailed_summary"),
        }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _date_str(value: Any) -> str | None:
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    return str(value)[:10] if value else None


def _json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def source_authority_for(url: str, court: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    return f"{court} ({host})" if host else court


def case_id_for_url(url: str) -> tuple[str, str]:
    """Stable (id, content_hash) for a judgment, keyed by its verified official URL."""
    digest = hashlib.sha256(url.strip().lower().encode()).hexdigest()
    return f"case_{digest[:24]}", digest


def _jurisdiction(court_level: str, court: str) -> str:
    if court_level == "SUPREME_COURT":
        return "NATIONAL"
    slug = re.sub(r"[^A-Z0-9]+", "_", court.upper()).strip("_")
    return slug[:80] or "UNKNOWN"


def _case_type(case_number: str | None) -> str:
    if not case_number:
        return "Judgment"
    match = re.match(r"\s*([A-Za-z.() ]+?)\s*(?:No\.?|Nos\.?|\d)", case_number)
    return (match.group(1).strip() if match else case_number.split(" ")[0])[:80] or "Judgment"


_CASE_COLUMNS = '''
  cc."id", cc."title", cc."court", cc."courtLevel", cc."jurisdiction", cc."judgmentDate",
  cc."caseNumber", cc."citation", cc."petitioner", cc."respondent", cc."sourceUrl",
  cc."sourceAuthority", cc."factsSummary", cc."holding", cc."primaryIssue", cc."metadata"
'''


class CaseLawStore:
    def __init__(self, connection: Any):
        self.connection = connection
        self._corpus_acts: dict[str, CorpusAct] | None = None

    def _cursor(self):
        from psycopg.rows import dict_row  # type: ignore

        return self.connection.cursor(row_factory=dict_row)

    def commit(self) -> None:
        self.connection.commit()

    # ------------------------------------------------------------------ statutes

    def corpus_acts(self) -> dict[str, CorpusAct]:
        """Acts in the statute corpus, keyed by catalog act id.

        Older ingests did not write act_id into legal_documents.metadata, so the
        id is resolved from the metadata, then the source document id, then the title.
        """
        if self._corpus_acts is None:
            from acts.catalog import get_catalog

            catalog = get_catalog()
            cursor = self._cursor()
            cursor.execute('SELECT d."id", d."title", d."metadata" FROM "legal_documents" d')
            grouped: dict[str, list[dict[str, Any]]] = {}
            for row in cursor.fetchall():
                meta = _json(row["metadata"]) or {}
                act_id = meta.get("act_id")
                if not act_id:
                    entry = (catalog.find_by_alias(meta.get("source_document_id"))
                             or catalog.find_by_alias(row["title"]) or catalog.get(row["title"]))
                    act_id = entry.act_id if entry else None
                if act_id:
                    grouped.setdefault(act_id, []).append({**row, "meta": meta})
            acts: dict[str, CorpusAct] = {}
            for act_id, rows in grouped.items():
                entry = catalog.get(act_id)
                meta = rows[0]["meta"]
                acts[act_id] = CorpusAct(
                    act_id=act_id,
                    title=rows[0]["title"],
                    short_title=(entry.short_title if entry else None) or meta.get("short_title") or rows[0]["title"],
                    domain=(entry.domain if entry else None) or meta.get("domain"),
                    source_url=meta.get("source_url") or (entry.official_url if entry else None),
                    document_ids=tuple(row["id"] for row in rows),
                )
            self._corpus_acts = acts
        return self._corpus_acts

    def act_for_document(self, document_id: str) -> str | None:
        for act in self.corpus_acts().values():
            if document_id in act.document_ids:
                return act.act_id
        return None

    def statute_section(self, act_id: str, section: str) -> Provision | None:
        act = self.corpus_acts().get(act_id)
        if act is None:
            return None
        cursor = self._cursor()
        cursor.execute('''
            SELECT c."content", c."chapter", c."pageNumber"
            FROM "legal_chunks" c
            WHERE c."documentId" = ANY(%s) AND upper(c."sectionNumber") = upper(%s)
            ORDER BY c."chunkIndex"
        ''', (list(act.document_ids), section))
        rows = cursor.fetchall()
        if not rows:
            return None
        text = clean_statute_text("\n".join(row["content"] for row in rows))
        if len(text) > MAX_SECTION_CHARS:
            text = text[:MAX_SECTION_CHARS].rsplit("\n", 1)[0] + "\n…"
        first = rows[0]
        return Provision(
            act_id=act_id, act_title=act.title, short_title=act.short_title,
            section=section, text=text, chapter=first["chapter"], page_number=first["pageNumber"],
            source_url=act.source_url, matched_by="reference",
        )

    def act_titles(self) -> dict[str, tuple[str, str]]:
        """act_id -> (official title, short title) for every Act in the corpus."""
        return {act.act_id: (act.title, act.short_title) for act in self.corpus_acts().values()}

    def list_acts(self) -> list[dict[str, Any]]:
        corpus = self.corpus_acts()
        cursor = self._cursor()
        cursor.execute('''
            SELECT c."documentId", COUNT(DISTINCT upper(c."sectionNumber")) AS section_count
            FROM "legal_chunks" c GROUP BY c."documentId"
        ''')
        sections_by_doc = {row["documentId"]: row["section_count"] for row in cursor.fetchall()}
        cursor.execute('''
            SELECT l."actId" AS act_id, COUNT(DISTINCT l."caseId") AS case_count
            FROM "court_case_laws" l GROUP BY l."actId"
        ''')
        cases_by_act = {row["act_id"]: row["case_count"] for row in cursor.fetchall()}
        acts = [{
            "act_id": act.act_id, "title": act.title, "short_title": act.short_title, "domain": act.domain,
            "section_count": sum(sections_by_doc.get(doc_id, 0) for doc_id in act.document_ids),
            "case_count": cases_by_act.get(act.act_id, 0),
        } for act in sorted(corpus.values(), key=lambda item: item.short_title)]
        # Acts not yet in the corpus but with seeded Act-level case law.
        for act_id, count in cases_by_act.items():
            if act_id not in corpus:
                acts.append({"act_id": act_id, "title": act_official_title(act_id),
                             "short_title": act_display_name(act_id),
                             "domain": None, "section_count": 0, "case_count": count})
        return acts

    def list_sections(self, act_id: str) -> list[dict[str, Any]]:
        act = self.corpus_acts().get(act_id)
        if act is None:
            return []
        cursor = self._cursor()
        cursor.execute('''
            WITH sections AS (
              SELECT DISTINCT ON (upper(c."sectionNumber"))
                     upper(c."sectionNumber") AS section, c."chunkIndex", left(c."content", 220) AS preview
              FROM "legal_chunks" c
              WHERE c."documentId" = ANY(%s) AND c."sectionNumber" IS NOT NULL
              ORDER BY upper(c."sectionNumber"), c."chunkIndex"
            )
            SELECT s.section, s.preview,
                   (SELECT COUNT(*) FROM "court_case_laws" l WHERE l."lawKey" = %s || ':' || s.section) AS case_count,
                   lk."status" AS lookup_status
            FROM sections s
            LEFT JOIN "research_law_lookups" lk ON lk."lawKey" = %s || ':' || s.section
            ORDER BY s."chunkIndex"
        ''', (list(act.document_ids), act_id, act_id))
        return [dict(row) for row in cursor.fetchall()]

    def sections_for_seeding(self, act_id: str) -> list[tuple[str, str]]:
        """(section, opening text) pairs for every section of an Act in the corpus."""
        act = self.corpus_acts().get(act_id)
        if act is None:
            return []
        cursor = self._cursor()
        cursor.execute('''
            SELECT DISTINCT ON (upper(c."sectionNumber")) upper(c."sectionNumber") AS section,
                   left(c."content", 900) AS text, c."chunkIndex"
            FROM "legal_chunks" c
            WHERE c."documentId" = ANY(%s) AND c."sectionNumber" IS NOT NULL
            ORDER BY upper(c."sectionNumber"), c."chunkIndex"
        ''', (list(act.document_ids),))
        rows = sorted(cursor.fetchall(), key=lambda row: row["chunkIndex"])
        return [(row["section"], row["text"]) for row in rows]

    # ------------------------------------------------------------------- cases

    def _hydrate(self, rows: Iterable[dict[str, Any]]) -> list[StoredCase]:
        cases = []
        for row in rows:
            meta = _json(row["metadata"]) or {}
            cases.append(StoredCase(
                id=row["id"], title=row["title"], court=row["court"], court_level=row["courtLevel"],
                jurisdiction=row["jurisdiction"],
                judgment_date=None if meta.get("date_unknown") else _date_str(row["judgmentDate"]),
                case_number=row["caseNumber"] or None, citation=row["citation"],
                petitioner=row["petitioner"], respondent=row["respondent"], source_url=row["sourceUrl"],
                source_authority=row["sourceAuthority"], summary=row["factsSummary"],
                holding=row["holding"], primary_issue=row["primaryIssue"], metadata=meta,
                law_keys=list(row.get("law_keys") or []), is_landmark=bool(row.get("is_landmark")),
                relevance_note=row.get("relevance_note"), similarity=row.get("similarity"),
            ))
        return cases

    def cases_for_law_keys(self, law_keys: Sequence[str], *, court_levels: Sequence[str],
                           limit: int = 20) -> list[StoredCase]:
        if not law_keys:
            return []
        cursor = self._cursor()
        cursor.execute(f'''
            SELECT {_CASE_COLUMNS},
                   array_agg(DISTINCT l."lawKey") AS law_keys,
                   bool_or(l."isLandmark") AS is_landmark,
                   max(l."relevanceNote") AS relevance_note
            FROM "court_case_laws" l JOIN "court_cases" cc ON cc."id" = l."caseId"
            WHERE l."lawKey" = ANY(%s) AND cc."courtLevel" = ANY(%s)
            GROUP BY cc."id"
            ORDER BY bool_or(l."isLandmark") DESC,
                     CASE cc."courtLevel" WHEN 'SUPREME_COURT' THEN 0 WHEN 'HIGH_COURT' THEN 1 ELSE 2 END,
                     cc."judgmentDate" DESC
            LIMIT %s
        ''', (list(law_keys), list(court_levels), limit))
        return self._hydrate(cursor.fetchall())

    def cases_by_ids(self, case_ids: Sequence[str]) -> list[StoredCase]:
        if not case_ids:
            return []
        cursor = self._cursor()
        cursor.execute(f'''
            SELECT {_CASE_COLUMNS},
                   array_remove(array_agg(DISTINCT l."lawKey"), NULL) AS law_keys,
                   COALESCE(bool_or(l."isLandmark"), false) AS is_landmark
            FROM "court_cases" cc LEFT JOIN "court_case_laws" l ON l."caseId" = cc."id"
            WHERE cc."id" = ANY(%s)
            GROUP BY cc."id"
        ''', (list(case_ids),))
        by_id = {case.id: case for case in self._hydrate(cursor.fetchall())}
        return [by_id[case_id] for case_id in case_ids if case_id in by_id]

    def similar_cases(self, vector_text: str, *, court_levels: Sequence[str], limit: int,
                      min_similarity: float) -> list[StoredCase]:
        cursor = self._cursor()
        cursor.execute(f'''
            SELECT * FROM (
              SELECT DISTINCT ON (cc."id") {_CASE_COLUMNS},
                     1 - (ch."embedding" <=> %s::vector) AS similarity
              FROM "court_case_chunks" ch JOIN "court_cases" cc ON cc."id" = ch."caseId"
              WHERE ch."embedding" IS NOT NULL AND cc."courtLevel" = ANY(%s)
              ORDER BY cc."id", ch."embedding" <=> %s::vector
            ) ranked
            WHERE similarity >= %s
            ORDER BY similarity DESC
            LIMIT %s
        ''', (vector_text, list(court_levels), vector_text, min_similarity, limit))
        cases = self._hydrate(cursor.fetchall())
        keys = self._law_keys_for([case.id for case in cases])
        for case in cases:
            case.law_keys, case.is_landmark = keys.get(case.id, ([], False))
        return cases

    def _law_keys_for(self, case_ids: Sequence[str]) -> dict[str, tuple[list[str], bool]]:
        if not case_ids:
            return {}
        cursor = self._cursor()
        cursor.execute('''
            SELECT "caseId", array_agg(DISTINCT "lawKey") AS law_keys, bool_or("isLandmark") AS landmark
            FROM "court_case_laws" WHERE "caseId" = ANY(%s) GROUP BY "caseId"
        ''', (list(case_ids),))
        return {row["caseId"]: (list(row["law_keys"]), bool(row["landmark"])) for row in cursor.fetchall()}

    def save_case(self, case: CandidateCase, *, origin: str, acts: Sequence[str],
                  links: Sequence[LawLink], embedding_text: str | None = None,
                  embedding: Sequence[float] | None = None, model: str | None = None) -> str:
        """Insert or refresh a verified judgment and attach it to law keys. Returns the case id."""
        if not case.verified or not case.official_url:
            raise ValueError("only cases with a verified official link can be stored")
        case_id, content_hash = case_id_for_url(case.official_url)
        verification = case.verification
        metadata = {
            "origin": origin,
            "relevance": case.relevance,
            "provisions": list(case.provisions),
            "predecessor_provision": case.predecessor_provision,
            "date_unknown": case.judgment_date is None,
            "discovery_model": model,
            "verification": {
                "status": "verified",
                "reason": verification.reason if verification else None,
                "content_type": verification.content_type if verification else None,
                "verified_at": _now().isoformat(),
            },
        }
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO "court_cases" (
              "id", "title", "court", "courtLevel", "jurisdiction", "caseNumber", "caseType",
              "judgmentDate", "judgeNames", "petitioner", "respondent", "citation", "officialSource",
              "sourceAuthority", "sourceUrl", "sourceType", "acts", "sections", "legalTopics",
              "primaryIssue", "factsSummary", "holding", "contentHash", "metadata", "updatedAt")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '[]'::jsonb, %s, %s, %s, true, %s, %s, 'JUDGMENT',
                    %s::jsonb, %s::jsonb, '[]'::jsonb, %s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT ("id") DO UPDATE SET
              "acts" = COALESCE((SELECT jsonb_agg(DISTINCT x) FROM jsonb_array_elements(
                          "court_cases"."acts" || EXCLUDED."acts") AS x), '[]'::jsonb),
              "sections" = COALESCE((SELECT jsonb_agg(DISTINCT x) FROM jsonb_array_elements(
                          "court_cases"."sections" || EXCLUDED."sections") AS x), '[]'::jsonb),
              "metadata" = EXCLUDED."metadata" || jsonb_strip_nulls(jsonb_build_object(
                          'detailed_summary', "court_cases"."metadata"->'detailed_summary',
                          'origin', "court_cases"."metadata"->'origin')),
              "updatedAt" = EXCLUDED."updatedAt"
        ''', (
            case_id, case.title, case.court, case.court_level,
            _jurisdiction(case.court_level, case.court), case.case_number or "",
            _case_type(case.case_number), case.judgment_date or "1900-01-01",
            case.petitioner, case.respondent, case.citation,
            source_authority_for(case.official_url, case.court), case.official_url,
            json.dumps(list(dict.fromkeys(acts))), json.dumps(list(case.provisions)),
            case.relevance or case.summary, case.summary, case.holding, content_hash,
            json.dumps(metadata), _now(),
        ))
        for link in links:
            self.link_case(case_id, link, origin=origin)
        if embedding is not None and embedding_text:
            vector_text = "[" + ",".join(repr(float(v)) for v in embedding) + "]"
            cursor.execute('''
                INSERT INTO "court_case_chunks" ("id", "caseId", "chunkIndex", "chunkType", "content", "embedding", "metadata")
                VALUES (%s, %s, 0, 'HOLDING', %s, %s::vector, '{"kind": "case_summary"}'::jsonb)
                ON CONFLICT ("id") DO UPDATE SET "content" = EXCLUDED."content", "embedding" = EXCLUDED."embedding"
            ''', (f"{case_id}:summary", case_id, embedding_text, vector_text))
        return case_id

    def link_case(self, case_id: str, link: LawLink, *, origin: str) -> None:
        act_id, section = split_law_key(link.law_key)
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO "court_case_laws" ("id", "caseId", "lawKey", "actId", "sectionNumber",
                                           "isLandmark", "relevanceNote", "origin")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ("caseId", "lawKey") DO UPDATE SET
              "isLandmark" = "court_case_laws"."isLandmark" OR EXCLUDED."isLandmark",
              "relevanceNote" = COALESCE("court_case_laws"."relevanceNote", EXCLUDED."relevanceNote")
        ''', (f"ccl_{uuid.uuid4().hex}", case_id, link.law_key, act_id, section,
              link.is_landmark, link.note, origin))

    def save_detailed_summary(self, case_id: str, summary: dict[str, Any]) -> None:
        cursor = self.connection.cursor()
        cursor.execute('''
            UPDATE "court_cases"
            SET "metadata" = COALESCE("metadata", '{}'::jsonb) || jsonb_build_object('detailed_summary', %s::jsonb),
                "updatedAt" = %s
            WHERE "id" = %s
        ''', (json.dumps(summary), _now(), case_id))

    # ----------------------------------------------------------------- lookups

    def fresh_lookups(self, law_keys: Sequence[str], max_age: timedelta) -> dict[str, str]:
        """law_key -> status for keys whose discovery ran within max_age."""
        if not law_keys:
            return {}
        cursor = self._cursor()
        cursor.execute('''
            SELECT "lawKey", "status" FROM "research_law_lookups"
            WHERE "lawKey" = ANY(%s) AND "lastDiscoveredAt" >= %s AND "status" <> 'FAILED'
        ''', (list(law_keys), _now() - max_age))
        return {row["lawKey"]: row["status"] for row in cursor.fetchall()}

    def record_lookup(self, key: str, *, status: str, mode: str, case_count: int,
                      proposed_count: int) -> None:
        act_id, section = split_law_key(key)
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO "research_law_lookups" ("lawKey", "actId", "sectionNumber", "status", "mode",
                "caseCount", "proposedCount", "lastDiscoveredAt", "updatedAt")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ("lawKey") DO UPDATE SET
              "status" = CASE WHEN EXCLUDED."status" = 'FAILED' AND "research_law_lookups"."status" = 'FOUND'
                              THEN 'FOUND' ELSE EXCLUDED."status" END,
              "mode" = EXCLUDED."mode",
              "caseCount" = GREATEST("research_law_lookups"."caseCount", EXCLUDED."caseCount"),
              "proposedCount" = EXCLUDED."proposedCount",
              "lastDiscoveredAt" = EXCLUDED."lastDiscoveredAt",
              "updatedAt" = EXCLUDED."updatedAt"
        ''', (key, act_id, section, status, mode, case_count, proposed_count, _now(), _now()))

    def count_hits(self, law_keys: Sequence[str]) -> None:
        if not law_keys:
            return
        cursor = self.connection.cursor()
        cursor.execute('''
            UPDATE "research_law_lookups" SET "hitCount" = "hitCount" + 1 WHERE "lawKey" = ANY(%s)
        ''', (list(law_keys),))

    # ----------------------------------------------------------------- queries

    def get_query(self, query_key: str) -> dict[str, Any] | None:
        cursor = self._cursor()
        cursor.execute('SELECT * FROM "research_queries" WHERE "queryKey" = %s', (query_key,))
        row = cursor.fetchone()
        if not row:
            return None
        row = dict(row)
        for column in ("lawKeys", "caseIds", "articulation"):
            row[column] = _json(row[column])
        return row

    def save_query(self, query_key: str, query: str, *, law_keys: Sequence[str] | None = None,
                   case_ids: Sequence[str] | None = None, articulation: Any = None,
                   discovered: bool = False) -> None:
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO "research_queries" ("id", "queryKey", "query", "lawKeys", "caseIds",
                                            "articulation", "discoveredAt", "updatedAt")
            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
            ON CONFLICT ("queryKey") DO UPDATE SET
              "lawKeys" = CASE WHEN %s THEN EXCLUDED."lawKeys" ELSE "research_queries"."lawKeys" END,
              "caseIds" = CASE WHEN %s THEN EXCLUDED."caseIds" ELSE "research_queries"."caseIds" END,
              "articulation" = COALESCE(EXCLUDED."articulation", "research_queries"."articulation"),
              "discoveredAt" = COALESCE(EXCLUDED."discoveredAt", "research_queries"."discoveredAt"),
              "hitCount" = "research_queries"."hitCount" + 1,
              "updatedAt" = EXCLUDED."updatedAt"
        ''', (
            f"rq_{uuid.uuid4().hex}", query_key, query[:4000],
            json.dumps(list(law_keys or [])), json.dumps(list(case_ids or [])),
            json.dumps(articulation) if articulation is not None else None,
            _now() if discovered else None, _now(),
            law_keys is not None, case_ids is not None,
        ))
