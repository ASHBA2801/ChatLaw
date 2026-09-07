#!/usr/bin/env python3
"""Orchestrate ingest -> chunk -> embed for catalog acts with available PDFs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent
rag_engine_dir = script_dir.parent
repo_root = rag_engine_dir.parent
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))

from acts.catalog import load_catalog


def _run(cmd: list[str]) -> None:
    print(">", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=rag_engine_dir, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run corpus ingestion gate for acts with PDFs")
    parser.add_argument("--stage", choices=["pilot", "stage_1", "all"], default="pilot")
    parser.add_argument("--act-id", action="append", dest="act_ids")
    parser.add_argument("--execute-embed", action="store_true")
    parser.add_argument("--skip-acquire", action="store_true")
    args = parser.parse_args()

    if not args.skip_acquire:
        acquire_cmd = [sys.executable, str(script_dir / "acquire_sources.py"), "--stage", args.stage]
        if args.act_ids:
            for act_id in args.act_ids:
                acquire_cmd.extend(["--act-id", act_id])
        _run(acquire_cmd)

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

    law_files = repo_root / "Law_files"
    ready = []
    for entry in targets:
        pdf = law_files / f"{entry.act_id}.pdf"
        if pdf.is_file():
            ready.append(entry.act_id)

    report = {"stage": args.stage, "ready_act_ids": ready, "ingested": [], "errors": []}
    if not ready:
        print(json.dumps(report, indent=2))
        return 1

    _run([sys.executable, str(script_dir / "ingest_pdfs.py")])
    _run([sys.executable, str(script_dir / "chunk_documents.py")])

    if args.execute_embed:
        for act_id in ready:
            try:
                _run([
                    sys.executable,
                    str(script_dir / "embed_chunks.py"),
                    "--document",
                    act_id,
                    "--execute",
                ])
                report["ingested"].append(act_id)
            except subprocess.CalledProcessError as exc:
                report["errors"].append({"act_id": act_id, "error": str(exc)})
    else:
        _run([sys.executable, str(script_dir / "embed_chunks.py"), "--dry-run"])

    out = rag_engine_dir / "data" / "metadata" / "ingestion_gate_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
