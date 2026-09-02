#!/usr/bin/env python3
"""Download official source PDFs for catalog acts from India Code / ministry URLs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

script_dir = Path(__file__).resolve().parent
rag_engine_dir = script_dir.parent
repo_root = rag_engine_dir.parent
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))

from acts.catalog import get_default_catalog_path, load_catalog

MIRRORS_PATH = repo_root / "legal_corpus" / "sources" / "official_mirrors.json"


def _load_mirrors() -> dict[str, list[str]]:
    if not MIRRORS_PATH.is_file():
        return {}
    data = json.loads(MIRRORS_PATH.read_text(encoding="utf-8"))
    return {k: list(v) for k, v in data.get("mirrors", {}).items()}


def _sha256_bytes(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def _safe_filename(act_id: str) -> str:
    return f"{act_id}.pdf"


def _normalize_official_url(url: str) -> str:
    return url.replace("www.indiacode.gov.in", "www.indiacode.nic.in").replace(
        "indiacode.gov.in", "indiacode.nic.in"
    )


def _fetch_url(url: str, *, timeout: int = 30, insecure: bool = True) -> bytes:
    context = ssl._create_unverified_context() if insecure else None
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChatLaw-CorpusBot/1.0",
            "Accept": "application/pdf,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read()


def _discover_pdf_urls(handle_url: str, *, insecure: bool = True, timeout: int = 15) -> list[str]:
    normalized = _normalize_official_url(handle_url)
    if not normalized:
        return []
    try:
        html = _fetch_url(normalized, insecure=insecure, timeout=timeout).decode("utf-8", errors="ignore")
    except Exception:
        return []
    candidates: list[str] = []
    for match in re.finditer(r'href="(/bitstream/[^"]+\.pdf[^"]*)"', html, re.I):
        candidates.append(urljoin(normalized, match.group(1)))
    for match in re.finditer(r'(https?://[^"\']+\.pdf)', html, re.I):
        candidates.append(match.group(1))
    # De-dupe preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for url in candidates:
        norm = _normalize_official_url(url)
        if norm not in seen:
            seen.add(norm)
            ordered.append(norm)
    return ordered


def _is_pdf(content: bytes, url: str) -> bool:
    if content[:4] == b"%PDF":
        return True
    return url.lower().endswith(".pdf") and len(content) > 1024


def acquire_act(
    entry,
    law_files_dir: Path,
    *,
    force: bool = False,
    rate_limit_seconds: float = 1.0,
    insecure: bool = True,
) -> dict:
    out_path = law_files_dir / _safe_filename(entry.act_id)
    catalog_relative = f"Law_files/{out_path.name}"

    if out_path.is_file() and not force:
        file_hash = _sha256_bytes(out_path.read_bytes())
        return {
            "act_id": entry.act_id,
            "status": "skipped_existing",
            "source_file": catalog_relative,
            "sha256": file_hash,
            "path": str(out_path),
        }

    urls: list[str] = []
    mirrors = _load_mirrors().get(entry.act_id, [])
    urls.extend(mirrors)
    if entry.official_url:
        normalized = _normalize_official_url(entry.official_url)
        if normalized not in urls:
            urls.append(normalized)
        urls.extend(_discover_pdf_urls(entry.official_url, insecure=insecure, timeout=15))

    last_error = "no downloadable PDF URL discovered"
    for url in urls:
        try:
            content = _fetch_url(url, insecure=insecure)
            if not _is_pdf(content, url):
                last_error = f"URL did not return PDF content: {url}"
                continue
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(content)
            file_hash = _sha256_bytes(content)
            time.sleep(rate_limit_seconds)
            return {
                "act_id": entry.act_id,
                "status": "downloaded",
                "source_file": catalog_relative,
                "sha256": file_hash,
                "path": str(out_path),
                "official_url": url,
                "retrieval_date": date.today().isoformat(),
            }
        except Exception as exc:
            last_error = str(exc)

    return {"act_id": entry.act_id, "status": "error", "error": last_error, "official_url": entry.official_url}


def update_catalog_paths(catalog_path: Path, results: list[dict]) -> None:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    by_id = {item["act_id"]: item for item in data.get("acts", [])}
    for result in results:
        act_id = result.get("act_id")
        if act_id not in by_id:
            continue
        if result.get("source_file"):
            by_id[act_id]["source_file"] = result["source_file"]
        if result.get("retrieval_date"):
            by_id[act_id]["retrieval_date"] = result["retrieval_date"]
        if result.get("status") in {"downloaded", "skipped_existing"}:
            if by_id[act_id].get("ingestion_status") == "pending_source":
                pass  # remain pending until ingest pipeline completes
    catalog_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire official PDF sources for catalog acts")
    parser.add_argument("--stage", choices=["pilot", "stage_1", "all"], default="pilot")
    parser.add_argument("--act-id", action="append", dest="act_ids", help="Specific act_id(s)")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--rate-limit", type=float, default=1.0)
    parser.add_argument("--law-files", type=Path, default=repo_root / "Law_files")
    parser.add_argument("--insecure", action="store_true", default=True, help="Allow SSL verify skip for India Code")
    args = parser.parse_args()

    catalog_path = get_default_catalog_path()
    catalog = load_catalog()
    targets = list(catalog.all_entries())

    if args.act_ids:
        wanted = {a.upper() for a in args.act_ids}
        targets = [e for e in targets if e.act_id.upper() in wanted]
    elif args.stage == "pilot":
        targets = [e for e in targets if e.ingestion_stage == "pilot" and e.ingestion_status != "ingested"]
    elif args.stage == "stage_1":
        targets = [
            e for e in targets
            if e.ingestion_stage in {"pilot", "stage_1"} and e.ingestion_status != "ingested"
        ]

    results = []
    for entry in targets:
        print(f"Acquiring {entry.act_id} ...", flush=True)
        results.append(acquire_act(entry, args.law_files, force=args.force, rate_limit_seconds=args.rate_limit, insecure=args.insecure))

    update_catalog_paths(catalog_path, results)
    summary = {
        "attempted": len(results),
        "downloaded": sum(1 for r in results if r["status"] == "downloaded"),
        "skipped_existing": sum(1 for r in results if r["status"] == "skipped_existing"),
        "errors": [r for r in results if r["status"] in {"error", "not_pdf", "no_url"}],
    }
    report_path = rag_engine_dir / "data" / "metadata" / "acquire_sources_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if not summary["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
