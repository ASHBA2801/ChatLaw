import { describe, expect, it } from "vitest";
import { searchOfficialJudgments } from "./official-cases";

describe("Official Case-Law Retrieval and Relevance Engine", () => {
  it("retrieves consumer dispute judgments and excludes unrelated domains", () => {
    const query = "I bought a defective product from an e-commerce website and the seller refused to refund me.";
    const results = searchOfficialJudgments(query, { limit: 3 });

    expect(results.length).toBeGreaterThan(0);
    const top = results[0];
    expect(["SGS India Ltd. v. Dolphin International Ltd.", "Amazon Wholesale India Pvt. Ltd. v. Competition Commission of India", "Lucknow Development Authority v. M.K. Gupta"]).toContain(top.title);
    expect(top.relevance_score).toBeGreaterThanOrEqual(75);
    expect(top.official_source).toBe(true);
    expect(top.source_url).toMatch(/^https:\/\/(?:digiscr\.sci\.gov\.in|delhihighcourt\.nic\.in|judgments\.ecourts\.gov\.in)/);

    // Verify negative constraint: MUST NOT return criminal theft, matrimonial, or property cases
    const titles = results.map((r) => r.title);
    expect(titles).not.toContain("K.N. Mehra v. State of Rajasthan");
    expect(titles).not.toContain("Lalita Kumari v. Govt. of U.P.");
    expect(titles).not.toContain("Rajnesh v. Neha & Anr.");
    expect(titles).not.toContain("P.A. Thomas & Co. v. R.K. Associates");
  });

  it("retrieves tenancy security deposit refund cases and excludes other domains", () => {
    const query = "My landlord refuses to return my security deposit.";
    const results = searchOfficialJudgments(query, { limit: 3 });

    expect(results.length).toBeGreaterThan(0);
    const titles = results.map((r) => r.title);
    expect(titles.some((t) => t.includes("Thomas") || t.includes("Suresh Kumar"))).toBe(true);
    expect(titles).not.toContain("Cadila Health Care Ltd. v. Cadila Pharmaceuticals Ltd.");
    expect(titles).not.toContain("Aureliano Fernandes v. State of Goa & Ors.");
  });

  it("prioritizes relevant High Court judgments when query specifies jurisdiction", () => {
    const query = "Can I challenge the withholding of tenant security deposit in Tamil Nadu?";
    const results = searchOfficialJudgments(query, { limit: 3 });

    expect(results.length).toBeGreaterThan(0);
    // The Madras High Court judgment should be top-ranked due to jurisdiction match
    expect(results[0].title).toBe("P.A. Thomas & Co. v. R.K. Associates");
    expect(results[0].court).toBe("High Court of Judicature at Madras");
    expect(results[0].jurisdiction).toBe("TAMIL_NADU");
  });

  it("retrieves workplace sexual harassment precedents under POSH Act", () => {
    const query = "My employer terminated me after I complained about workplace harassment.";
    const results = searchOfficialJudgments(query, { limit: 3 });

    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toBe("Aureliano Fernandes v. State of Goa & Ors.");
    expect(results[0].relevance_score).toBeGreaterThanOrEqual(80);
    expect(results[0].relevant_law).toContain("Sexual Harassment");
  });

  it("retrieves breach of contract and compensation precedents", () => {
    const query = "The company breached the agreement and refused compensation.";
    const results = searchOfficialJudgments(query, { limit: 3 });

    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toBe("Kailash Nath Associates v. Delhi Development Authority");
    expect(results[0].relevant_law).toContain("Contract Act");
  });

  it("retrieves trademark infringement precedents", () => {
    const query = "Another company is using my registered trademark.";
    const results = searchOfficialJudgments(query, { limit: 3 });

    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toBe("Cadila Health Care Ltd. v. Cadila Pharmaceuticals Ltd.");
    expect(results[0].relevant_law).toContain("Trade Marks Act");
  });

  it("retrieves erroneous tax demand precedents", () => {
    const query = "I received a tax demand and believe the calculation is wrong.";
    const results = searchOfficialJudgments(query, { limit: 3 });

    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toBe("Union of India & Anr. v. Mohit Minerals Pvt. Ltd.");
    expect(results[0].relevance_score).toBeGreaterThanOrEqual(75);
  });

  it("retrieves environmental water pollution precedents", () => {
    const query = "A factory is polluting a nearby water source.";
    const results = searchOfficialJudgments(query, { limit: 3 });

    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toBe("Vellore Citizens Welfare Forum v. Union of India");
    expect(results[0].relevant_law).toContain("Water (Prevention and Control of Pollution) Act");
  });

  it("handles keyword trap queries by prioritizing underlying legal offence", () => {
    const query = "A theft occurred inside a high court building and the accused wants bail.";
    const results = searchOfficialJudgments(query, { limit: 3 });

    expect(results.length).toBeGreaterThan(0);
    // Should return criminal precedents on theft/FIR rather than constitutional court structure cases
    const titles = results.map((r) => r.title);
    expect(titles.some((t) => t.includes("Mehra") || t.includes("Lalita Kumari"))).toBe(true);
    expect(titles).not.toContain("Kesavananda Bharati v. State of Kerala");
  });

  it("enforces minimum relevance threshold and returns 0 cases for irrelevant queries", () => {
    const query = "What is the recipe for biryani?";
    const results = searchOfficialJudgments(query);
    expect(results).toHaveLength(0);
  });
});
