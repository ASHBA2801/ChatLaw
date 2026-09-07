import { describe, expect, it } from "vitest";
import { extractLegalIssues } from "./query-understanding";

describe("Deterministic Legal Issue Extraction", () => {
  it("extracts consumer dispute concepts accurately", () => {
    const q = "I bought a defective product from an e-commerce website and the seller refused to refund me.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("CONSUMER");
    expect(result.confidence).toBe("HIGH");
    expect(result.acts).toContain("Consumer Protection Act, 2019");
    expect(result.facts.some((f) => f.includes("defect"))).toBe(true);
    expect(result.facts.some((f) => f.includes("refund"))).toBe(true);
    expect(result.jurisdiction).toBeNull();
  });

  it("extracts workplace harassment and termination concepts", () => {
    const q = "My employer terminated me after I complained about workplace harassment.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("EMPLOYMENT");
    expect(result.confidence).toBe("HIGH");
    expect(result.facts.some((f) => f.includes("termination"))).toBe(true);
    expect(result.acts.some((a) => a.includes("Sexual Harassment"))).toBe(true);
  });

  it("extracts tenancy security deposit dispute concepts", () => {
    const q = "My landlord refuses to return my security deposit.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("PROPERTY");
    expect(result.confidence).toBe("HIGH");
    expect(result.acts).toContain("Transfer of Property Act, 1882");
    expect(result.facts.some((f) => f.includes("tenancy"))).toBe(true);
  });

  it("extracts breach of contract concepts", () => {
    const q = "The company breached the agreement and refused compensation.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("CONTRACT");
    expect(result.confidence).toBe("HIGH");
    expect(result.acts).toContain("Indian Contract Act, 1872");
  });

  it("extracts matrimonial and divorce concepts", () => {
    const q = "My spouse filed for divorce and I want to understand my rights.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("FAMILY");
    expect(result.confidence).toBe("HIGH");
    expect(result.facts.some((f) => f.includes("divorce"))).toBe(true);
  });

  it("extracts personal data and privacy concepts", () => {
    const q = "Someone used my personal information without permission.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("CYBER");
    expect(result.confidence).toBe("HIGH");
  });

  it("extracts trademark infringement concepts", () => {
    const q = "Another company is using my registered trademark.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("IP");
    expect(result.confidence).toBe("HIGH");
    expect(result.acts).toContain("Trade Marks Act, 1999");
  });

  it("extracts tax demand calculation error concepts", () => {
    const q = "I received a tax demand and believe the calculation is wrong.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("TAX");
    expect(result.confidence).toBe("HIGH");
  });

  it("extracts criminal theft accusation concepts", () => {
    const q = "I was accused of theft and want to know what courts have said about similar cases.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("CRIMINAL");
    expect(result.confidence).toBe("HIGH");
  });

  it("extracts environmental water pollution concepts", () => {
    const q = "A factory is polluting a nearby water source.";
    const result = extractLegalIssues(q);
    expect(result.domain).toBe("ENVIRONMENT");
    expect(result.confidence).toBe("HIGH");
    expect(result.acts).toContain("Water (Prevention and Control of Pollution) Act, 1974");
  });

  it("extracts explicit jurisdiction without inventing one when absent", () => {
    const withJurisdiction = extractLegalIssues("Can I challenge this property order in Tamil Nadu?");
    expect(withJurisdiction.jurisdiction).toBe("TAMIL_NADU");

    const withoutJurisdiction = extractLegalIssues("Can I challenge this property order?");
    expect(withoutJurisdiction.jurisdiction).toBeNull();
  });

  it("identifies irrelevant queries with UNKNOWN domain", () => {
    const irrelevant = extractLegalIssues("What is the recipe for biryani?");
    expect(irrelevant.domain).toBe("UNKNOWN");
    expect(irrelevant.confidence).toBe("NONE");
    expect(irrelevant.isDisputeScenario).toBe(false);
  });
});
