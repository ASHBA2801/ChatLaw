#!/usr/bin/env python3
"""Research a section or legal question from the terminal.

Fetches the relevant provisions straight from the embedded statute corpus and,
optionally, the explanation and verified case law the Research tab shows.

  python scripts/research.py "Section 103 BNS"
  python scripts/research.py "IPC 498A cruelty" --explain --cases
  python scripts/research.py "security deposit not returned" --cases --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

RAG_ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(RAG_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_ENGINE_DIR))
load_dotenv(RAG_ENGINE_DIR / ".env")

from research.service import create_research_service  # noqa: E402
from retrieval.vector_search import close_pool  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query")
    parser.add_argument("--explain", action="store_true", help="Generate the plain-language explanation")
    parser.add_argument("--cases", action="store_true", help="Find verified case law (library first)")
    parser.add_argument("--refresh", action="store_true", help="Search official court sites even if cached")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    service = create_research_service()
    try:
        law = service.law(args.query, articulate=args.explain)
        cases = service.cases(args.query, law_keys=law.law_keys, refresh=args.refresh) if args.cases else None
        if args.json:
            print(json.dumps({
                "law_keys": law.law_keys,
                "notes": law.notes,
                "provisions": [{"label": p.label, "law_key": p.law_key, "similarity": p.similarity,
                                "matched_by": p.matched_by, "text": p.text} for p in law.provisions],
                "articulation": law.articulation,
                "cases": cases.cases if cases else None,
                "case_source": cases.source if cases else None,
            }, indent=2, ensure_ascii=False, default=str))
            return 0

        print(f"Law keys: {', '.join(law.law_keys) or '—'}")
        for note in law.notes:
            print(f"Note: {note}")
        for provision in law.provisions:
            score = f" ({provision.similarity:.2f})" if provision.similarity is not None else ""
            print(f"\n== {provision.label}{score} [{provision.matched_by}]\n{provision.text[:1500]}")
        if law.articulation:
            print(f"\n== Explanation\n{law.articulation['overview']}")
            for item in law.articulation["elements"]:
                print(f"  • {item}")
        elif args.explain and law.articulation_error:
            print(f"\nExplanation unavailable: {law.articulation_error}")
        if cases:
            print(f"\n== Case law ({cases.source})")
            if cases.message:
                print(cases.message)
            for case in cases.cases:
                print(f"\n{case['title']} — {case['court']}, {case['judgment_date'] or 'date not recorded'}")
                print(f"  {case['source_url']}")
                print(f"  {case['holding']}")
        return 0
    finally:
        service.close()
        close_pool()


if __name__ == "__main__":
    raise SystemExit(main())
