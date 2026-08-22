#!/usr/bin/env python3
"""RAG-05 semantic legal retrieval CLI (read-only database search)."""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

rag_engine_dir = Path(__file__).resolve().parents[1]
if str(rag_engine_dir) not in sys.path:
    sys.path.insert(0, str(rag_engine_dir))
load_dotenv(rag_engine_dir / ".env")

from embeddings.provider import create_embedding_provider
from retrieval.vector_search import VectorSearcher, connect_from_environment, ensure_cosine_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Search ChatLaw legal chunks semantically")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--min-similarity", type=float, default=None)
    parser.add_argument("--json", action="store_true", help="Print structured JSON")
    parser.add_argument("--debug", action="store_true", help="Print deterministic reranking signals")
    args = parser.parse_args()
    if args.top_k <= 0:
        parser.error("--top-k must be positive")

    connection = None
    try:
        provider = create_embedding_provider()
        connection = connect_from_environment()
        ensure_cosine_index(connection)
        response = VectorSearcher(connection, provider).search(
            args.query, top_k=args.top_k, min_similarity=args.min_similarity, debug=args.debug
        )
        if args.json:
            print(json.dumps(response.as_dict(), indent=2, ensure_ascii=False, default=str))
        else:
            print("=" * 50)
            print("CHATLAW LEGAL RETRIEVAL")
            print("=" * 50)
            print(f"\nQuery:\n{args.query}\n\nResults:")
            for index, result in enumerate(response.results, 1):
                print(f"\n[{index}] Similarity: {result.similarity:.4f}")
                print(f"Document: {result.document_title}")
                print(f"Section: {result.section_number or '—'}")
                print(f"Page: {result.page_number or '—'}")
                print(f"Chunk ID: {result.chunk_id}")
                print("-" * 50)
                print(result.content)
            if response.no_relevant_context:
                print("\nNo relevant legal context met the configured threshold.")
            print(f"\nResults returned: {len(response.results)}")
            print(f"Embedding dimension: {provider.info.dimension}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
