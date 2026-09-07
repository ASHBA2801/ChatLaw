import { describe, expect, it } from "vitest";
import { searchLandmarkCases } from "./landmarkCases";

describe("searchLandmarkCases with threshold", () => {
  it("returns relevant cases when query matches tokens", () => {
    const hits = searchLandmarkCases("constitutional basic structure");
    expect(hits.length).toBeGreaterThan(0);
    expect(hits[0].title).toBeDefined();
  });

  it("returns empty when query has no sufficient match (relevance threshold)", () => {
    const hits = searchLandmarkCases("xyzabc999 unrelated nonsense query");
    expect(hits).toHaveLength(0);
  });
});
