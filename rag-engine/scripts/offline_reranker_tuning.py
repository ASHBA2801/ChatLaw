#!/usr/bin/env python3
"""Offline RAG-10C reranker analysis.

This script reads only JSON evaluation artifacts. It does not import the
embedding provider, connect to PostgreSQL, or make network requests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

FAILURES = {"RAG10-001", "RAG10-007", "RAG10-012", "RAG10-017", "RAG10-018"}
CONFIGS = {
    "A": (0.80, 0.10, 0.07, 0.03),
    "B": (0.75, 0.12, 0.08, 0.05),
    "C": (0.70, 0.10, 0.15, 0.05),
    "D": (0.85, 0.08, 0.05, 0.02),
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def matches(result: dict[str, Any], expected: list[dict[str, Any]]) -> bool:
    return any(result["document"] == item["document"] and result.get("section") == item.get("section") for item in expected)


def score(result: dict[str, Any], weights: tuple[float, float, float, float]) -> float:
    vector, keyword, section, document = weights
    return (
        float(result.get("vector_score") or result.get("similarity") or 0.0) * vector
        + float(result.get("keyword_score") or 0.0) * keyword
        + float(result.get("section_score") or 0.0) * section
        + float(result.get("document_score") or 0.0) * document
    )


def metric_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    legal = [item for item in results if item["relevant"]]
    ranks: list[int | None] = []
    for item in legal:
        rank = next((index for index, result in enumerate(item["retrieved"], 1) if matches(result, item["expected"])), None)
        ranks.append(rank)
    def recall(k: int) -> float:
        return sum(rank is not None and rank <= k for rank in ranks) / len(ranks)
    return {
        "recall_at_1": recall(1), "recall_at_3": recall(3),
        "recall_at_5": recall(5), "recall_at_8": recall(8),
        "mrr": mean(1 / rank if rank else 0.0 for rank in ranks),
        "irrelevant_accuracy": sum(item["no_context"] == (not item["relevant"]) for item in results) / len(results),
        "failed_at_8": [item["id"] for item, rank in zip(legal, ranks) if rank is None or rank > 8],
    }


def offline_config_report(report: dict[str, Any], weights: tuple[float, float, float, float]) -> dict[str, Any]:
    transformed: list[dict[str, Any]] = []
    for item in report["results"]:
        candidates = item.get("candidate_retrieved", [])
        ranked = sorted(
            (dict(candidate, rerank_score=score(candidate, weights)) for candidate in candidates),
            key=lambda candidate: (candidate["rerank_score"], candidate.get("similarity", 0.0)),
            reverse=True,
        )
        transformed.append(dict(item, retrieved=ranked[:8], no_context=item["no_context"]))
    return metric_report(transformed)


def failure_diagnostics(report: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics = []
    for item in report["results"]:
        if item["id"] not in FAILURES:
            continue
        candidates = item.get("candidate_retrieved", [])
        candidate_rank = next((index for index, candidate in enumerate(candidates, 1) if matches(candidate, item["expected"])), None)
        final_rank = next((index for index, result in enumerate(item["retrieved"], 1) if matches(result, item["expected"])), None)
        diagnostics.append({
            "id": item["id"], "question": item["question"], "expected": item["expected"],
            "candidate_rank": candidate_rank, "final_rank": final_rank,
            "cause": "candidate_generation" if candidate_rank is None else "reranking_or_selection",
            "top_candidates": candidates[:8], "final_results": item["retrieved"],
        })
    return diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "evaluation")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    directory = args.evaluation_dir
    baseline = load(directory / "retrieval_baseline.json")
    rag10b = load(directory / "retrieval_reranked.json")
    # D is the only stored RAG-10C artifact containing the complete scored
    # candidate pool. Reuse that pool for every offline weight experiment;
    # A-C contain only final results or null component scores.
    scored_candidates = load(directory / "retrieval_rag10c_D.json")
    result = {
        "api_calls_made": 0,
        "offline_only": True,
        "source_artifacts": ["retrieval_baseline.json", "retrieval_reranked.json"] + [f"retrieval_rag10c_{name}.json" for name in CONFIGS],
        "baseline": baseline["metrics"] | {"irrelevant_accuracy": baseline["irrelevant_query_detection"]["accuracy"]},
        "rag10b": rag10b["metrics"] | {"irrelevant_accuracy": rag10b["irrelevant_query_detection"]["accuracy"]},
        "configurations": {
            name: {"weights": dict(zip(("vector", "keyword", "section", "document"), weights)), "metrics": offline_config_report(scored_candidates, weights)}
            for name, weights in CONFIGS.items()
        },
        "failure_diagnostics": failure_diagnostics(scored_candidates),
        "note": "All calculations used stored candidate scores; no embeddings, database, or external services were accessed.",
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
