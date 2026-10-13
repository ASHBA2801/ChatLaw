#!/usr/bin/env python3
"""Build the verified case-law library used by the Research tab.

Every stored judgment has an official government copy that was downloaded and
checked to name the parties. Progress is kept in research_law_lookups, so an
interrupted run resumes where it stopped (use --refresh to redo sections).

  # Re-verify and import the curated cases shipped with ChatLaw
  python scripts/seed_case_law.py --import-curated

  # Landmark cases for every section of Acts in the embeddings
  python scripts/seed_case_law.py --acts BNS2023,HMA1955,CPA2019
  python scripts/seed_case_law.py --all-acts --workers 4

  # Act-level landmark cases for Acts not yet ingested (Income-tax, Labour Codes, ...)
  python scripts/seed_case_law.py --act-level ITA2025,COW2019,IRC2020,RAILWAYS1989
  python scripts/seed_case_law.py --act-level pending

  # See what would run and roughly how many grounded searches it needs
  python scripts/seed_case_law.py --all-acts --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

RAG_ENGINE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = RAG_ENGINE_DIR.parent
if str(RAG_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_ENGINE_DIR))
load_dotenv(RAG_ENGINE_DIR / ".env")

from acts.catalog import get_catalog  # noqa: E402
from research.discovery import CandidateCase, CaseDiscovery  # noqa: E402
from research.law_reference import (  # noqa: E402
    SUPPLEMENTARY_ACTS, act_official_title, extract_law_references, law_key,
)
from research.service import CACHE_TTL, ResearchService, create_research_service  # noqa: E402
from research.store import CaseLawStore, LawLink  # noqa: E402

CURATED_FILES = (
    REPO_ROOT / "web" / "data" / "legal" / "official-judgments.json",
    REPO_ROOT / "legal-data" / "cases" / "landmark-cases.json",
)
# Average grounded searches per section: one discovery call plus link searches.
SEARCHES_PER_SECTION = 3.5
_print_lock = threading.Lock()


def log(message: str) -> None:
    with _print_lock:
        print(message, flush=True)


# --------------------------------------------------------------------- curated

def _curated_candidates() -> list[tuple[CandidateCase, list[str]]]:
    catalog = get_catalog()
    seen: set[str] = set()
    items: list[tuple[CandidateCase, list[str]]] = []
    for path in CURATED_FILES:
        if not path.exists():
            continue
        for row in json.loads(path.read_text(encoding="utf-8")):
            title = row["title"].strip()
            if title.lower() in seen:
                continue
            seen.add(title.lower())
            provisions = [*row.get("sections", []), *row.get("relevant_sections", [])]
            keys: list[str] = []
            for act in row.get("acts", []):
                entry = catalog.find_by_alias(act)
                if entry:
                    keys.append(entry.act_id)
                elif "constitution" in act.lower():
                    keys.append("CONSTITUTION")
            for text in row.get("relevant_sections", []):
                keys.extend(ref.law_key for ref in extract_law_references(text))
            year = row.get("year")
            items.append((CandidateCase(
                title=title,
                court=row.get("court") or "Supreme Court of India",
                court_level=row.get("court_level") or (
                    "SUPREME_COURT" if "supreme" in (row.get("court") or "").lower() else "HIGH_COURT"),
                judgment_date=row.get("judgment_date") or (f"{year}-01-01" if year else None),
                citation=row.get("citation"),
                case_number=row.get("case_number"),
                petitioner=row.get("petitioner"),
                respondent=row.get("respondent"),
                official_url=row.get("source_url"),
                summary=row.get("facts_summary") or row.get("summary") or row.get("holding", ""),
                holding=row.get("holding") or row.get("summary", ""),
                relevance=row.get("why_relevant", ""),
                provisions=tuple(provisions),
            ), list(dict.fromkeys(keys))))
    return items


def import_curated(service: ResearchService, discovery: CaseDiscovery) -> None:
    items = _curated_candidates()
    log(f"Curated cases to check: {len(items)}")
    stored = 0
    for case, keys in items:
        checked = discovery.verify_case(case)
        if not checked.verified:
            log(f"  … {case.title}: stored link failed ({checked.verification.reason if checked.verification else 'no link'}); "
                "searching for an official copy")
            checked = discovery.find_official_copy(case)
        if not checked.verified:
            log(f"  ✗ {case.title}: no verified official copy found — skipped")
            continue
        case_id, _ = service.save_discovered(checked, origin="CURATED", primary_keys=keys, model=None)
        for key in keys:
            service.store.link_case(case_id, LawLink(key, is_landmark=True, note=case.relevance or None),
                                    origin="CURATED")
        service.store.commit()
        stored += 1
        log(f"  ✓ {case.title} → {checked.official_url}")
    log(f"Curated import: {stored}/{len(items)} stored with verified official links")


# ---------------------------------------------------------------------- seeding

def _section_jobs(store: CaseLawStore, act_ids: list[str], sections: set[str] | None,
                  limit: int | None) -> list[dict]:
    titles = store.act_titles()
    jobs = []
    for act_id in act_ids:
        if act_id not in titles:
            log(f"! {act_id} is not in the embeddings; use --act-level {act_id} instead")
            continue
        title = act_official_title(act_id)
        rows = store.sections_for_seeding(act_id)
        if sections:
            rows = [row for row in rows if row[0] in sections]
        for section, text in rows[:limit] if limit else rows:
            jobs.append({
                "law_key": law_key(act_id, section),
                "topic": f"Section {section} of {title}",
                "context": f"Section {section}, {title}:\n{text}",
                "max_cases": 3,
            })
    return jobs


def _act_level_jobs(spec: str) -> list[dict]:
    catalog = get_catalog()
    if spec == "pending":
        act_ids = [e.act_id for e in catalog.all_entries() if e.ingestion_status == "pending_source"
                   and e.status != "repealed"] + list(SUPPLEMENTARY_ACTS)
    else:
        act_ids = [x.strip() for x in spec.split(",") if x.strip()]
    jobs = []
    for act_id in act_ids:
        entry = catalog.get(act_id)
        if not entry and act_id not in SUPPLEMENTARY_ACTS:
            log(f"! Unknown Act id {act_id}; skipped")
            continue
        title = act_official_title(act_id)
        predecessors = [act_official_title(p) for p in (entry.repeals if entry else ())]
        hint = f" Include leading judgments under {', '.join(predecessors)} where the principle carries over." \
            if predecessors else ""
        jobs.append({
            "law_key": act_id,
            "topic": f"the {title} as a whole (its most important provisions).{hint}",
            "context": f"{title}" + (f" — {entry.category}" if entry and entry.category else ""),
            "max_cases": 8,
        })
    return jobs


def run_jobs(jobs: list[dict], *, workers: int, refresh: bool, court_levels: list[str]) -> None:
    totals = {"FOUND": 0, "NONE_FOUND": 0, "FAILED": 0, "SKIPPED": 0, "stored": 0}
    started = time.perf_counter()

    def work(job: dict) -> dict:
        service = create_research_service()
        try:
            return service.seed_law(job["law_key"], topic=job["topic"], provisions_context=job["context"],
                                    court_levels=court_levels, max_cases=job["max_cases"], refresh=refresh)
        finally:
            service.close()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, job): job for job in jobs}
        for done, future in enumerate(as_completed(futures), 1):
            job = futures[future]
            try:
                outcome = future.result()
            except Exception as exc:  # keep seeding the rest
                outcome = {"law_key": job["law_key"], "status": "FAILED", "stored": 0, "error": str(exc)[:200]}
            totals[outcome["status"]] = totals.get(outcome["status"], 0) + 1
            totals["stored"] += outcome.get("stored", 0)
            detail = ", ".join(outcome.get("titles", [])) or outcome.get("error", "")
            log(f"[{done}/{len(jobs)}] {outcome['law_key']}: {outcome['status']} "
                f"({outcome.get('stored', 0)}/{outcome.get('proposed', 0)} verified) {detail}"[:400])
    log(f"\nDone in {time.perf_counter() - started:.0f}s: {json.dumps(totals)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--import-curated", action="store_true", help="Verify and import bundled curated cases")
    parser.add_argument("--acts", help="Comma-separated Act ids from the embeddings (e.g. BNS2023,HMA1955)")
    parser.add_argument("--all-acts", action="store_true", help="Every Act in the embeddings")
    parser.add_argument("--sections", help="Only these section numbers (with --acts)")
    parser.add_argument("--act-level", help="Act-level seeding: comma-separated Act ids, or 'pending'")
    parser.add_argument("--limit", type=int, help="Max sections per Act")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--refresh", action="store_true", help="Re-run sections searched in the last 30 days")
    parser.add_argument("--court-levels", default="SUPREME_COURT,HIGH_COURT")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not (args.import_curated or args.acts or args.all_acts or args.act_level):
        parser.error("choose --import-curated, --acts, --all-acts or --act-level")

    service = create_research_service()
    try:
        jobs: list[dict] = []
        if args.acts or args.all_acts:
            act_ids = sorted(service.store.act_titles()) if args.all_acts else [
                x.strip() for x in args.acts.split(",") if x.strip()]
            sections = {x.strip().upper() for x in args.sections.split(",")} if args.sections else None
            jobs += _section_jobs(service.store, act_ids, sections, args.limit)
        if args.act_level:
            jobs += _act_level_jobs(args.act_level)
        if not args.refresh and jobs:
            fresh = service.store.fresh_lookups([job["law_key"] for job in jobs], CACHE_TTL)
            skipped = len([job for job in jobs if job["law_key"] in fresh])
            jobs = [job for job in jobs if job["law_key"] not in fresh]
            if skipped:
                log(f"Skipping {skipped} law keys already searched in the last 30 days")

        if args.dry_run:
            for job in jobs[:40]:
                log(f"  {job['law_key']}: {job['topic'][:100]}")
            if len(jobs) > 40:
                log(f"  … and {len(jobs) - 40} more")
            log(f"{len(jobs)} law keys ≈ {int(len(jobs) * SEARCHES_PER_SECTION)} grounded Gemini searches")
            if args.import_curated:
                log(f"Curated cases to verify: {len(_curated_candidates())}")
            return 0

        if args.import_curated:
            import_curated(service, CaseDiscovery())
        if jobs:
            levels = [x.strip() for x in args.court_levels.split(",") if x.strip()]
            run_jobs(jobs, workers=max(1, args.workers), refresh=args.refresh, court_levels=levels)
        return 0
    finally:
        service.close()
        from retrieval.vector_search import close_pool
        close_pool()


if __name__ == "__main__":
    raise SystemExit(main())
