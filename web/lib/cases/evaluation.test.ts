import { describe, expect, it } from "vitest";
import { searchOfficialJudgments } from "./official-cases";
import benchmarkData from "../../../rag-engine/data/evaluation/case_retrieval_benchmark.json";

describe("Benchmark Evaluation Suite Across 10 Legal Domains", () => {
  it("evaluates recall, ranking, and domain isolation across all benchmark scenarios", () => {
    let r1Hits = 0;
    let r3Hits = 0;
    let totalRelevant = 0;
    let totalReturned = 0;
    let totalIrrelevantHits = 0;

    for (const item of benchmarkData) {
      const hits = searchOfficialJudgments(item.query, { limit: 5 });

      if (!item.is_relevant_query) {
        // Out-of-domain queries must return 0 results
        expect(hits).toHaveLength(0);
        continue;
      }

      totalRelevant++;
      totalReturned += hits.length;
      expect(hits.length).toBeGreaterThan(0);

      const hitIds = hits.map((h) => h.id);
      const expectedIds = item.expected_case_ids;

      if (expectedIds.includes(hitIds[0])) {
        r1Hits++;
      }
      if (hitIds.slice(0, 3).some((id) => expectedIds.includes(id))) {
        r3Hits++;
      }

      // Check prohibited domain isolation
      for (const h of hits) {
        if (item.prohibited_domains.includes(h.court_level) || item.prohibited_domains.includes(h.jurisdiction)) {
          totalIrrelevantHits++;
        }
      }
    }

    const recallAt1 = r1Hits / totalRelevant;
    const recallAt3 = r3Hits / totalRelevant;
    const irrelevantRate = totalIrrelevantHits / totalReturned;

    expect(recallAt1).toBeGreaterThanOrEqual(0.90);
    expect(recallAt3).toBe(1.0);
    expect(irrelevantRate).toBe(0.0);
  });
});
