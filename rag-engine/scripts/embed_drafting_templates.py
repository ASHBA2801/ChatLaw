#!/usr/bin/env python3
"""Embed the complaint / petition formats used by the Cases tab filing agent.

Reads legal_corpus/drafting_templates/*.md, chunks each format by `##`
section, embeds every chunk with the configured provider (768-d) and upserts
into drafting_templates / drafting_template_chunks. Unchanged templates are
skipped, so the script is cheap to re-run after adding or editing a format.

  python scripts/embed_drafting_templates.py            # embed new / changed formats
  python scripts/embed_drafting_templates.py --dry-run  # parse and list, no API calls
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

RAG_ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(RAG_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_ENGINE_DIR))
load_dotenv(RAG_ENGINE_DIR / ".env")

from complaints.templates import load_templates, store_template  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="parse the templates without embedding")
    args = parser.parse_args()

    templates = load_templates()
    print(f"[TEMPLATES] {len(templates)} formats in legal_corpus/drafting_templates")
    if args.dry_run:
        for template in templates.values():
            print(f"  {template.kind:22} {template.forum:9} {len(template.sections):2} sections  {template.title}")
        return 0

    from embeddings.provider import create_embedding_provider
    from retrieval.vector_search import close_pool, connect_from_environment

    provider = create_embedding_provider()
    connection = connect_from_environment()
    total = 0
    try:
        for template in templates.values():
            written = store_template(connection, template, provider.embed)
            connection.commit()
            total += written
            state = f"{written} chunks embedded" if written else "unchanged"
            print(f"  {template.kind:22} {state}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
        close_pool()
    print(f"[TEMPLATES] done — {total} chunks embedded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
