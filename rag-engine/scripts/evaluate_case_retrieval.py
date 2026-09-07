#!/usr/bin/env python3
"""Deterministic offline evaluation of official Indian case-law retrieval.

Evaluates recall, MRR, and domain purity across benchmark queries
without making external API calls or spending Gemini tokens.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAG_ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(RAG_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_ENGINE_DIR))

from cases.retrieval import search_official_judgments, get_official_judgments

BENCHMARK_PATH = RAG_ENGINE_DIR / "data" / "evaluation" / "case_retrieval_benchmark.json"


def evaluate_case_retrieval() -> dict[str, float]:
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    catalog = {item["id"]: item for item in get_official_judgments()}

    r1_hits = 0
    r3_hits = 0
    r5_hits = 0
    rr_scores = []
    total_relevant_queries = 0
    total_returned_cases = 0
    total_irrelevant_cases = 0
    correctly_rejected_queries = 0
    total_irrelevant_queries = 0

    print("=" * 78)
    print("OFFICIAL CASE-LAW RETRIEVAL & RELEVANCE ENGINE — OFFLINE EVALUATION")
    print("Authoritative Indian Judgments Evaluation (DigiSCR / eCourts / High Courts)")
    print("=" * 78)

    for item in benchmarks:
        qid = item["id"]
        query = item["query"]
        expected_ids = set(item.get("expected_case_ids", []))
        prohibited_domains = set(item.get("prohibited_domains", []))
        is_rel = item.get("is_relevant_query", True)

        hits = search_official_judgments(query, limit=5, min_threshold=60)

        if not is_rel:
            total_irrelevant_queries += 1
            if len(hits) == 0:
                correctly_rejected_queries += 1
                status = "PASS (Correctly rejected with 0 cases)"
            else:
                status = f"FAIL (Returned {len(hits)} cases for irrelevant query)"
            print(f"[{qid}] {query[:50]}... -> {status}")
            continue

        total_relevant_queries += 1
        hit_ids = [h.id for h in hits]
        total_returned_cases += len(hits)

        # Check for prohibited domains
        for h in hits:
            case_domain = catalog.get(h.id, {}).get("domain", "")
            if case_domain in prohibited_domains:
                total_irrelevant_cases += 1

        # Calculate Recall@K
        hit_r1 = any(hid in expected_ids for hid in hit_ids[:1])
        hit_r3 = any(hid in expected_ids for hid in hit_ids[:3])
        hit_r5 = any(hid in expected_ids for hid in hit_ids[:5])

        if hit_r1:
            r1_hits += 1
        if hit_r3:
            r3_hits += 1
        if hit_r5:
            r5_hits += 1

        # Calculate Reciprocal Rank
        rank = 0
        for i, hid in enumerate(hit_ids, start=1):
            if hid in expected_ids:
                rank = i
                break
        rr = (1.0 / rank) if rank > 0 else 0.0
        rr_scores.append(rr)

        top_hit_title = hits[0].title if hits else "NONE"
        top_hit_score = f"{hits[0].relevance_score}%" if hits else "N/A"
        top_hit_court = hits[0].court if hits else "N/A"
        match_sym = "PASS" if hit_r3 else "FAIL"

        print(f"[{qid}] {match_sym} | Score: {top_hit_score} | Top: {top_hit_title} ({top_hit_court})")

    recall_at_1 = r1_hits / max(1, total_relevant_queries)
    recall_at_3 = r3_hits / max(1, total_relevant_queries)
    recall_at_5 = r5_hits / max(1, total_relevant_queries)
    mrr = sum(rr_scores) / max(1, len(rr_scores))
    irrelevant_rate = total_irrelevant_cases / max(1, total_returned_cases)
    rejection_rate = correctly_rejected_queries / max(1, total_irrelevant_queries)

    print("-" * 78)
    print(f"Total Queries Evaluated:    {len(benchmarks)}")
    print(f"Relevant Legal Queries:     {total_relevant_queries}")
    print(f"Irrelevant Queries:         {total_irrelevant_queries}")
    print(f"Recall@1:                   {recall_at_1:.2%}")
    print(f"Recall@3:                   {recall_at_3:.2%}")
    print(f"Recall@5:                   {recall_at_5:.2%}")
    print(f"Mean Reciprocal Rank (MRR): {mrr:.4f}")
    print(f"Irrelevant Case Rate:       {irrelevant_rate:.2%} (Target: 0.00%)")
    print(f"Out-of-Domain Rejection:    {rejection_rate:.2%} (Target: 100.00%)")
    print(f"External API / LLM Calls:   0 (Cost: $0.00)")
    print("=" * 78)

    return {
        "recall_at_1": recall_at_1,
        "recall_at_3": recall_at_3,
        "recall_at_5": recall_at_5,
        "mrr": mrr,
        "irrelevant_rate": irrelevant_rate,
        "rejection_rate": rejection_rate,
    }


if __name__ == "__main__":
    metrics = evaluate_case_retrieval()
    if metrics["recall_at_3"] < 0.80 or metrics["irrelevant_rate"] > 0.05:
        sys.exit(1)
    sys.exit(0)
