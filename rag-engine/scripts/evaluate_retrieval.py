#!/usr/bin/env python3
"""Reproducible baseline evaluation for the current vector retrieval pipeline."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

RAG_ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(RAG_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_ENGINE_DIR))
load_dotenv(RAG_ENGINE_DIR / ".env")

from embeddings.provider import create_embedding_provider
from retrieval.reranker import RerankWeights
from retrieval.vector_search import VectorSearcher, connect_from_environment

DEFAULT_DATASET = RAG_ENGINE_DIR / "data" / "evaluation" / "retrieval_questions.json"
DEFAULT_JSON = RAG_ENGINE_DIR / "data" / "evaluation" / "retrieval_reranked.json"
DEFAULT_TEXT = RAG_ENGINE_DIR / "data" / "evaluation" / "retrieval_reranked.txt"

DOCUMENT_ALIASES = {
    "BNS2023": "THE BHARATIYA NYAYA SANHITA, 2023",
    "BSA": "THE BHARATIYASAKSHYAADHINIYAM, 2023",
    "BNSS2023": "THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023",
}


def load_dataset(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("evaluation dataset must be a non-empty JSON array")
    return data


def validate_expected(connection: Any, questions: list[dict[str, Any]]) -> None:
    """Fail loudly if any expected document/section coordinate is absent."""
    cursor = connection.cursor()
    cursor.execute(
        'SELECT d."title", c."sectionNumber" FROM "legal_chunks" c '
        'JOIN "legal_documents" d ON d."id" = c."documentId" '
        'GROUP BY d."title", c."sectionNumber"'
    )
    available = {(str(title), section) for title, section in cursor.fetchall()}
    missing: list[str] = []
    for question in questions:
        for expected in question["expected"]:
            document = DOCUMENT_ALIASES.get(expected["document"], expected["document"])
            coordinate = (document, expected.get("section"))
            if coordinate not in available:
                missing.append(f'{question["id"]}: {document} / Section {expected.get("section") or "—"}')
    if missing:
        raise ValueError("Expected coordinates absent from indexed corpus:\n" + "\n".join(missing))


def coordinate(result: Any) -> dict[str, Any]:
    title = next((alias for alias, value in DOCUMENT_ALIASES.items() if value == result.document_title), result.document_title)
    return {
        "document": title, "section": result.section_number, "similarity": result.similarity,
        "vector_score": result.vector_score, "keyword_score": result.keyword_score,
        "section_score": result.section_score, "document_score": result.document_score,
        "rerank_score": result.rerank_score,
    }


def is_match(result: Any, expected: list[dict[str, Any]]) -> bool:
    return any(
        DOCUMENT_ALIASES.get(item["document"], item["document"]) == result.document_title
        and item.get("section") == result.section_number
        for item in expected
    )


def evaluate(questions: list[dict[str, Any]], searcher: VectorSearcher, top_k: int,
             *, candidate_top_k: int | None = None, weights: RerankWeights | None = None) -> dict[str, Any]:
    details = []
    latencies = []
    for question in questions:
        started = time.perf_counter()
        response = searcher.search(question["question"], top_k=top_k,
                       candidate_top_k=candidate_top_k, weights=weights)
        latency = time.perf_counter() - started
        latencies.append(latency)
        retrieved = [coordinate(result) for result in response.results]
        candidate_retrieved = [coordinate(result) for result in response.candidate_results]
        ranks = [index + 1 for index, result in enumerate(response.results) if is_match(result, question["expected"])]
        candidate_ranks = [index + 1 for index, result in enumerate(response.candidate_results) if is_match(result, question["expected"])]
        rr = 1.0 / ranks[0] if ranks else 0.0
        details.append({
            "id": question["id"], "question": question["question"], "category": question["category"],
            "expected": question["expected"], "relevant": question["relevant"], "retrieved": retrieved,
            "candidate_retrieved": candidate_retrieved,
            "candidate_rank": candidate_ranks[0] if candidate_ranks else None,
            "no_context": response.no_relevant_context, "latency_seconds": latency,
            "hit_at_1": bool(ranks and ranks[0] <= 1), "hit_at_3": bool(ranks and ranks[0] <= 3),
            "hit_at_5": bool(ranks and ranks[0] <= 5), "hit_at_8": bool(ranks and ranks[0] <= 8), "rr": rr,
        })

    legal = [item for item in details if item["relevant"]]
    irrelevant = [item for item in details if not item["relevant"]]
    def recall(k: int) -> float:
        return sum(item[f"hit_at_{k}"] for item in legal) / len(legal) if legal else 0.0
    predicted_no_context = [item for item in details if item["no_context"]]
    true_no_context = [item for item in irrelevant if item["no_context"]]
    no_context_precision = len(true_no_context) / len(predicted_no_context) if predicted_no_context else 0.0
    no_context_recall = len(true_no_context) / len(irrelevant) if irrelevant else 0.0
    no_context_accuracy = sum(item["no_context"] == (not item["relevant"]) for item in details) / len(details)
    return {
        "question_count": len(details), "category_distribution": dict(Counter(item["category"] for item in details)),
        "metrics": {"recall_at_1": recall(1), "recall_at_3": recall(3), "recall_at_5": recall(5), "recall_at_8": recall(8), "mrr": sum(item["rr"] for item in legal) / len(legal)},
        "irrelevant_query_detection": {"precision": no_context_precision, "recall": no_context_recall, "accuracy": no_context_accuracy},
        "latency": {"average_seconds": statistics.mean(latencies), "median_seconds": statistics.median(latencies)},
        "failed_recall_at_8": [item["id"] for item in legal if not item["hit_at_8"]],
        "incorrect_top_ranked": [item["id"] for item in legal if not item["hit_at_1"]],
        "results": details,
    }


def render_text(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    no_context = report["irrelevant_query_detection"]
    latency = report["latency"]
    lines = ["=" * 40, "CHATLAW RETRIEVAL RERANKED", "=" * 40, "", f'Questions: {report["question_count"]}', ""]
    lines += [f"Recall@{k}: {metrics[f'recall_at_{k}']:.4f}" for k in (1, 3, 5, 8)]
    lines += [f"\nMRR: {metrics['mrr']:.4f}", "", "Irrelevant Query Detection", f"Precision: {no_context['precision']:.4f}", f"Recall:    {no_context['recall']:.4f}", f"Accuracy:  {no_context['accuracy']:.4f}", "", f"Average latency: {latency['average_seconds']:.4f} s", f"Median latency: {latency['median_seconds']:.4f} s", "", "Per-question results", ""]
    for item in report["results"]:
        lines += [f'[{item["id"]}]', f'Question: {item["question"]}', "Expected: " + ", ".join(f'{x["document"]} / Section {x.get("section") or "—"}' for x in item["expected"]) or "None", "Retrieved:"]
        lines += [f'  {i}. {r["document"]} / Section {r["section"] or "—"} (similarity={r["similarity"]:.4f})' for i, r in enumerate(item["retrieved"], 1)] or ["  None"]
        lines += [f'Hit@1: {"YES" if item["hit_at_1"] else "NO"} | Hit@3: {"YES" if item["hit_at_3"] else "NO"} | Hit@5: {"YES" if item["hit_at_5"] else "NO"} | Hit@8: {"YES" if item["hit_at_8"] else "NO"}', f'RR: {item["rr"]:.4f}', ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--text-output", type=Path, default=DEFAULT_TEXT)
    parser.add_argument("--candidate-top-k", type=int, default=None)
    parser.add_argument("--vector-weight", type=float, default=None)
    parser.add_argument("--keyword-weight", type=float, default=None)
    parser.add_argument("--section-weight", type=float, default=None)
    parser.add_argument("--document-weight", type=float, default=None)
    parser.add_argument("--diagnostic", action="store_true")
    args = parser.parse_args()
    if args.top_k < 8:
        parser.error("--top-k must be at least 8 to calculate Recall@8")
    questions = load_dataset(args.dataset)
    connection = None
    try:
        connection = connect_from_environment()
        validate_expected(connection, questions)
        searcher = VectorSearcher(connection, create_embedding_provider())
        values = (args.vector_weight, args.keyword_weight, args.section_weight, args.document_weight)
        weights = RerankWeights(*values) if all(value is not None for value in values) else None
        report = evaluate(questions, searcher, args.top_k,
                  candidate_top_k=args.candidate_top_k, weights=weights)
        if args.diagnostic:
            for item in report["results"]:
                if item["relevant"] and item["id"] in {"RAG10-001", "RAG10-007", "RAG10-012", "RAG10-017", "RAG10-018"}:
                    print(json.dumps({key: item[key] for key in ("id", "question", "expected", "candidate_rank", "candidate_retrieved", "retrieved")}, indent=2))
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        args.text_output.write_text(render_text(report), encoding="utf-8")
        print(render_text(report).split("Per-question results", 1)[0])
        print(f"Reports written to {args.json_output} and {args.text_output}")
        return 0
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
