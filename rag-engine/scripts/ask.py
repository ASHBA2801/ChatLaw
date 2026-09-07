#!/usr/bin/env python3
"""RAG-06 grounded legal answer CLI."""

import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

rag_engine_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(rag_engine_dir))
load_dotenv(rag_engine_dir / ".env")

from embeddings.provider import create_embedding_provider
from generation.answer import answer_question
from generation.gemini import GeminiGenerator
from retrieval.vector_search import VectorSearcher, connect_from_environment, ensure_cosine_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask a grounded ChatLaw legal question")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--min-similarity", type=float, default=0.60)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.top_k <= 0:
        parser.error("--top-k must be positive")
    connection = None
    started = time.perf_counter()
    try:
        print("[CHAT] Query received", file=sys.stderr, flush=True)
        print("[CHAT] Retrieving context", file=sys.stderr, flush=True)
        provider = create_embedding_provider()
        connection = connect_from_environment()
        ensure_cosine_index(connection)
        retrieval = VectorSearcher(connection, provider).search(
            args.question, top_k=args.top_k, min_similarity=args.min_similarity, debug=args.debug)
        print("[CHAT] Context retrieved", file=sys.stderr, flush=True)
        generator = None if retrieval.no_relevant_context else GeminiGenerator()
        print("[CHAT] Building prompt", file=sys.stderr, flush=True)
        if generator:
            print("[CHAT] Generating answer", file=sys.stderr, flush=True)
        response = answer_question(
            args.question, retrieval,
            None if generator is None else generator.generate,
            top_k=args.top_k)
        if args.json:
            print(json.dumps(response.as_dict(), indent=2, ensure_ascii=False, default=str))
        else:
            print("=" * 50 + "\nCHATLAW\n" + "=" * 50)
            print(f"\nQuestion:\n{args.question}\n\nAnswer:\n{response.answer}")
            print("\nSources:")
            for citation in response.citations:
                location = f"Section {citation['section']}" if citation.get('section') else ""
                if citation.get('subsection'):
                    location += str(citation['subsection'])
                if citation.get('page') is not None:
                    location += f" · Page {citation['page']}"
                print(f"[{citation['id']}] {citation['document']}" + (f" · {location}" if location else ""))
                print(f"Evidence: {citation['evidence']}")
            print(f"\nRetrieval: {len(retrieval.results)} candidates, {len(response.citations)} sources used")
            print(f"Generation latency: {response.generation['latency_seconds']:.2f}s")
        print(f"[CHAT] Complete ({time.perf_counter() - started:.2f}s)", file=sys.stderr, flush=True)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())