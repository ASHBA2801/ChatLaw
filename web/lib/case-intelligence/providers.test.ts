import { describe, expect, it } from "vitest";

import { courtProvider, advocateProvider } from "./providers";
import { searchLandmarkCases, LANDMARK_CASES } from "@/lib/legal-data/landmarkCases";

describe("local court and advocate directories", () => {
  it("returns verified courts for Tamil Nadu cities without remote providers", async () => {
    const results = await courtProvider.search({
      location: { city: "Coimbatore", state: "Tamil Nadu", country: "India" },
      caseCategory: "Property / Tenancy",
      radiusKm: 100,
    });
    expect(results.length).toBeGreaterThan(0);
    expect(results.some((item) => item.name.toLowerCase().includes("coimbatore") || item.state === "Tamil Nadu")).toBe(
      true,
    );
    expect(results.every((item) => item.verification_status === "verified")).toBe(true);
    expect(results.every((item) => !item.official_url || item.official_url.startsWith("https://"))).toBe(true);
  });

  it("returns official advocate directories rather than invented lawyer profiles", async () => {
    const results = await advocateProvider.search({
      location: { city: "Chennai", state: "Tamil Nadu", country: "India" },
      practiceArea: "Civil",
      radiusKm: 100,
    });
    expect(results.length).toBeGreaterThan(0);
    expect(results.every((item) => /bar council|nalsa|ecourts|directory|legal aid/i.test(item.name + item.source_type))).toBe(
      true,
    );
  });
});

describe("landmark case catalog", () => {
  it("includes curated verified Supreme Court cases", () => {
    expect(LANDMARK_CASES.length).toBeGreaterThanOrEqual(10);
    expect(LANDMARK_CASES.every((item) => item.source_url.startsWith("https://"))).toBe(true);
  });

  it("finds privacy and FIR related cases by keyword", () => {
    const privacy = searchLandmarkCases("privacy Article 21");
    expect(privacy.some((item) => /puttaswamy/i.test(item.title))).toBe(true);
    const fir = searchLandmarkCases("FIR police cognizable");
    expect(fir.some((item) => /lalita kumari/i.test(item.title))).toBe(true);
  });
});
