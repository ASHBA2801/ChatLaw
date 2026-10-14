"""Drafting-template library: format exemplars for each office and court.

Templates live as Markdown under legal_corpus/drafting_templates/ and are
embedded into drafting_template_chunks (scripts/embed_drafting_templates.py).
At draft time the agent retrieves the closest sections for the chosen office
with pgvector; if the table is empty or unavailable it reads the file itself,
so drafting never depends on the embedding run having happened.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

logger = logging.getLogger(__name__)

_FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True)
class TemplateSection:
    heading: str
    body: str


@dataclass(frozen=True)
class DraftingTemplate:
    slug: str
    kind: str
    forum: str
    title: str
    document_type: str
    sources: tuple[str, ...]
    sections: tuple[TemplateSection, ...]
    court_subject: str | None = None
    content_hash: str = ""

    @property
    def text(self) -> str:
        return "\n\n".join(f"## {s.heading}\n{s.body}" for s in self.sections)

    def chunks(self) -> list[dict[str, Any]]:
        """One chunk per section, prefixed with the template title so each embeds in context."""
        return [
            {"index": index, "heading": section.heading,
             "content": f"{self.title}\n{section.heading}\n{section.body}"}
            for index, section in enumerate(self.sections)
        ]


@dataclass(frozen=True)
class RelatedSection:
    kind: str
    template_title: str
    heading: str
    content: str
    similarity: float


@dataclass(frozen=True)
class TemplateMatch:
    template: DraftingTemplate
    sections: tuple[TemplateSection, ...]
    related: tuple[RelatedSection, ...] = ()
    source: str = "file"  # "vector" | "file"

    def exemplar(self, limit: int = 9000) -> str:
        body = "\n\n".join(f"## {s.heading}\n{s.body}" for s in self.sections)
        text = f"# {self.template.title}\n\n{body}"
        if self.related:
            extra = "\n\n".join(f"### {r.heading} (from: {r.template_title})\n{r.content}" for r in self.related)
            text += "\n\n# Related format guidance for these facts\n\n" + extra
        return text[:limit]

    def audit(self) -> dict[str, Any]:
        return {"kind": self.template.kind, "title": self.template.title, "source": self.source,
                "sources": list(self.template.sources),
                "related": [{"kind": r.kind, "heading": r.heading, "similarity": round(r.similarity, 3)}
                            for r in self.related]}


def template_dir() -> Path:
    for candidate in (
        Path(__file__).resolve().parents[2] / "legal_corpus" / "drafting_templates",
        Path(__file__).resolve().parents[1] / "legal_corpus" / "drafting_templates",
        Path("/app/legal_corpus/drafting_templates"),
    ):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("legal_corpus/drafting_templates was not found")


def parse_template(slug: str, raw: str) -> DraftingTemplate:
    match = _FRONT_MATTER.match(raw)
    if not match:
        raise ValueError(f"{slug}: missing front matter")
    meta: dict[str, Any] = {}
    sources: list[str] = []
    current_list: list[str] | None = None
    for line in match.group(1).splitlines():
        if line.startswith("- ") and current_list is not None:
            current_list.append(line[2:].strip())
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key == "sources":
            current_list = sources
        elif key:
            meta[key] = value
            current_list = None
    body = raw[match.end():]
    sections: list[TemplateSection] = []
    for block in re.split(r"(?m)^##\s+", body):
        block = block.strip()
        if not block:
            continue
        heading, _, text = block.partition("\n")
        sections.append(TemplateSection(heading.strip(), text.strip()))
    for required in ("kind", "forum", "title"):
        if not meta.get(required):
            raise ValueError(f"{slug}: front matter needs {required}")
    if not sections:
        raise ValueError(f"{slug}: no sections")
    return DraftingTemplate(
        slug=slug, kind=meta["kind"], forum=meta["forum"], title=meta["title"],
        document_type=meta.get("document_type", meta["title"]), sources=tuple(sources),
        sections=tuple(sections), court_subject=meta.get("court_subject") or None,
        content_hash=hashlib.sha256(raw.encode()).hexdigest(),
    )


@lru_cache(maxsize=1)
def load_templates() -> dict[str, DraftingTemplate]:
    templates: dict[str, DraftingTemplate] = {}
    for path in sorted(template_dir().glob("*.md")):
        template = parse_template(path.stem, path.read_text(encoding="utf-8"))
        templates[template.kind] = template
    return templates


# Sections of *other* formats that fit these facts (e.g. the transaction table of
# the cyber-crime format when a police complaint is about UPI fraud).
RELATED_SQL = '''
SELECT t."kind", t."title", c."heading", c."content", 1 - (c."embedding" <=> %s::vector) AS similarity
FROM "drafting_template_chunks" AS c
JOIN "drafting_templates" AS t ON t."id" = c."templateId"
WHERE c."embedding" IS NOT NULL AND t."kind" <> %s AND t."forum" = %s
  AND c."heading" NOT IN ('Addressee', 'Subject', 'Closing', 'Filing notes', 'Cause title', 'Title',
                          'Introduction', 'Salutation and introduction', 'Verification', 'Prayer')
ORDER BY c."embedding" <=> %s::vector
LIMIT %s
'''
RELATED_MIN_SIMILARITY = 0.62


@dataclass
class TemplateLibrary:
    connection: Any = None
    embedding_provider: Any = None
    templates: dict[str, DraftingTemplate] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.templates:
            self.templates = load_templates()

    def get(self, kind: str) -> DraftingTemplate | None:
        return self.templates.get(kind)

    def match(self, kind: str, facts: str, *, top_k: int = 3) -> TemplateMatch | None:
        """The template for this office, plus related sections of other formats that fit the facts.

        The chosen office's template is always used whole (a complaint needs all
        its parts). The vector search over drafting_template_chunks adds up to
        `top_k` sections from other formats for the same forum when they are
        close to the facts.
        """
        template = self.get(kind)
        if template is None:
            return None
        if self.connection is None or self.embedding_provider is None or not facts.strip():
            return TemplateMatch(template, template.sections)
        try:
            vector = self.embedding_provider.embed(f"{template.title}\n{facts[:3000]}")
            vector_text = "[" + ",".join(repr(float(v)) for v in vector) + "]"
            cursor = self.connection.cursor()
            cursor.execute(RELATED_SQL, (vector_text, kind, template.forum, vector_text, top_k * 2))
            rows = cursor.fetchall()
        except Exception:  # missing table, provider outage — the file is authoritative anyway
            logger.warning("[FILINGS] template vector search unavailable; using file template", exc_info=True)
            try:
                self.connection.rollback()
            except Exception:
                pass
            return TemplateMatch(template, template.sections)
        related: list[RelatedSection] = []
        seen: set[tuple[str, str]] = set()
        for row in rows:
            similarity = float(_row(row, "similarity", 4) or 0.0)
            key = (_row(row, "kind", 0), _row(row, "heading", 2))
            if similarity < RELATED_MIN_SIMILARITY or key in seen:
                continue
            seen.add(key)
            related.append(RelatedSection(key[0], _row(row, "title", 1), key[1],
                                          str(_row(row, "content", 3))[:1500], similarity))
            if len(related) >= top_k:
                break
        return TemplateMatch(template, template.sections, tuple(related), source="vector")


def _row(row: Any, key: str, index: int) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    return row[index]


# ------------------------------------------------------------ embedding store

UPSERT_TEMPLATE_SQL = '''
INSERT INTO "drafting_templates"
  ("id", "slug", "kind", "forum", "title", "documentType", "courtSubject", "sources", "content",
   "contentHash", "createdAt", "updatedAt")
VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, NOW(), NOW())
ON CONFLICT ("slug") DO UPDATE SET
  "kind" = EXCLUDED."kind", "forum" = EXCLUDED."forum", "title" = EXCLUDED."title",
  "documentType" = EXCLUDED."documentType", "courtSubject" = EXCLUDED."courtSubject",
  "sources" = EXCLUDED."sources", "content" = EXCLUDED."content",
  "contentHash" = EXCLUDED."contentHash", "updatedAt" = NOW()
RETURNING "id", (xmax = 0) AS inserted
'''


def template_id(slug: str) -> str:
    return "tpl_" + hashlib.sha256(slug.encode()).hexdigest()[:24]


def store_template(connection: Any, template: DraftingTemplate, embed: Any) -> int:
    """Upsert one template and (re)embed its chunks when its content changed. Returns chunks written."""
    cursor = connection.cursor()
    cursor.execute('SELECT "contentHash" FROM "drafting_templates" WHERE "slug" = %s', (template.slug,))
    existing = cursor.fetchone()
    previous_hash = _row(existing, "contentHash", 0) if existing else None
    tid = template_id(template.slug)
    cursor.execute(UPSERT_TEMPLATE_SQL, (
        tid, template.slug, template.kind, template.forum, template.title, template.document_type,
        template.court_subject, json.dumps(list(template.sources)), template.text, template.content_hash,
    ))
    if previous_hash == template.content_hash:
        cursor.execute('SELECT COUNT(*) FROM "drafting_template_chunks" WHERE "templateId" = %s '
                       'AND "embedding" IS NOT NULL', (tid,))
        count = cursor.fetchone()
        if int(_row(count, "count", 0) or 0) == len(template.sections):
            return 0
    cursor.execute('DELETE FROM "drafting_template_chunks" WHERE "templateId" = %s', (tid,))
    written = 0
    for chunk in template.chunks():
        vector = embed(chunk["content"])
        vector_text = "[" + ",".join(repr(float(v)) for v in vector) + "]"
        cursor.execute(
            'INSERT INTO "drafting_template_chunks" ("id", "templateId", "chunkIndex", "heading", "content", '
            '"embedding", "createdAt") VALUES (%s, %s, %s, %s, %s, %s::vector, NOW())',
            (f"{tid}_{chunk['index']}", tid, chunk["index"], chunk["heading"], chunk["content"], vector_text),
        )
        written += 1
    return written


def template_summaries(templates: Sequence[DraftingTemplate]) -> list[dict[str, Any]]:
    return [{"kind": t.kind, "forum": t.forum, "title": t.title, "document_type": t.document_type,
             "sources": list(t.sources)} for t in templates]
