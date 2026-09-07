import { describe, expect, it } from "vitest";
import { haversineDistanceKm, sortAndFilterByDistance } from "./distance";

describe("case intelligence distance", () => {
  it("calculates distance deterministically", () => {
    expect(haversineDistanceKm({ latitude: 0, longitude: 0 }, { latitude: 0, longitude: 1 })).toBeCloseTo(111.19, 1);
  });

  it("filters and sorts resources by radius", () => {
    const results = sortAndFilterByDistance([
      { id: "far", name: "Far", type: "court", latitude: 0, longitude: 2, source_url: null, source_type: "x", verification_status: "verified", retrieved_at: null },
      { id: "near", name: "Near", type: "court", latitude: 0, longitude: 0.1, source_url: null, source_type: "x", verification_status: "verified", retrieved_at: null },
    ], { latitude: 0, longitude: 0 }, 20);
    expect(results.map((item) => item.id)).toEqual(["near"]);
  });
});