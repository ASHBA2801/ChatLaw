import { describe, expect, it } from "vitest";
import { classifyCase } from "./classify";

describe("case intelligence classification", () => {
  it("classifies a tenancy question without making a legal conclusion", () => {
    const result = classifyCase("My landlord refuses to return my security deposit.", { city: "Coimbatore", state: "Tamil Nadu" });
    expect(result.legal_domain).toBe("Property");
    expect(result.case_category).toContain("Tenancy");
    expect(result.jurisdiction).toBe("Tamil Nadu");
    expect(result.limitations.length).toBeGreaterThan(0);
  });

  it("flags potentially urgent wording carefully", () => {
    expect(classifyCase("I may be arrested tomorrow").urgency).toBe("potentially_urgent");
  });
});