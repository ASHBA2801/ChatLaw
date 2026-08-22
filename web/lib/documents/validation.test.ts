import { describe, expect, it } from "vitest";

import { addSection, createCustomSection, removeSection, updateSectionBody } from "./editor";
import { buildDocx } from "./export/docx";
import { buildPdf } from "./export/pdf";
import { sanitizeDocument, sanitizePlainText } from "./sanitize";
import { parseStatus } from "./status";
import { getTemplate, listTemplates } from "./templates";
import { activeClauses, validateValues } from "./validation";
import type { GeneratedDocumentPayload } from "./types";

function samplePayload(): GeneratedDocumentPayload {
  return {
    template_id: "nda",
    title: "Non-Disclosure Agreement",
    document_type: "Non-Disclosure Agreement",
    jurisdiction_country: "IN",
    jurisdiction_region: "Karnataka",
    sections: [
      { id: "title", title: "Title", body: "Agreement", required: true, number: null },
      { id: "term", title: "Term", body: "The term is 12 months.", required: true, number: 1 },
    ],
    signatures: [{ party_id: "disclosing", role: "Disclosing Party", name: "Acme", lines: ["DISCLOSING PARTY", "Name: Acme"] }],
    warnings: [{ code: "ai_generated", message: "Review this draft." }],
    citations: [],
    disclaimer: "Not legal advice.",
  };
}

describe("templates", () => {
  it("exposes only implemented templates", () => {
    expect(listTemplates().map((item) => item.id).sort()).toEqual([
      "affidavit",
      "authorization_letter",
      "complaint",
      "consumer_complaint",
      "employment_agreement",
      "legal_notice",
      "mou",
      "nda",
      "partnership_agreement",
      "rent_lease",
      "sale_agreement",
      "service_agreement",
    ]);
  });
});

describe("validation", () => {
  it("stops when required fields are missing", () => {
    const result = validateValues(getTemplate("nda"), { jurisdiction_country: "IN" });
    expect(result.canGenerate).toBe(false);
    expect(result.blocking.some((issue) => issue.fieldId === "disclosing_party_name")).toBe(true);
  });

  it("includes payment clauses only when an amount exists", () => {
    const template = getTemplate("service_agreement");
    const without = activeClauses(template, { fee_amount: "" });
    const withFee = activeClauses(template, { fee_amount: 25000 });
    expect(without.some((clause) => clause.id === "fees")).toBe(false);
    expect(withFee.some((clause) => clause.id === "fees")).toBe(true);
  });
});

describe("editor operations", () => {
  it("edits, adds, and removes clauses without regenerating the document", () => {
    const start = samplePayload();
    const edited = updateSectionBody(start, "term", "The term is 18 months.");
    expect(edited.sections[1].body).toContain("18 months");
    const extra = createCustomSection("Extra");
    const added = addSection(edited, extra, "term");
    expect(added.sections.map((section) => section.id)).toContain(extra.id);
    const removed = removeSection(added, extra.id);
    expect(removed.sections.map((section) => section.id)).not.toContain(extra.id);
  });
});

describe("sanitization", () => {
  it("neutralizes executable markup", () => {
    expect(sanitizePlainText('<script>alert(1)</script>Hello')).not.toContain("<script>");
    const clean = sanitizeDocument({
      ...samplePayload(),
      sections: [{ id: "x", title: "<b>Title</b>", body: "<img src=x onerror=alert(1)>", required: false }],
    });
    expect(clean.sections[0].body).not.toContain("<img");
  });
});

describe("status and export", () => {
  it("rejects unknown status values", () => {
    expect(() => parseStatus("published")).toThrow();
    expect(parseStatus("draft")).toBe("draft");
  });

  it("builds real PDF and DOCX bytes", async () => {
    const pdf = await buildPdf(samplePayload());
    const docx = await buildDocx(samplePayload());
    expect(pdf.byteLength).toBeGreaterThan(100);
    expect(docx.byteLength).toBeGreaterThan(100);
    expect(Buffer.from(pdf.subarray(0, 4)).toString()).toBe("%PDF");
  });
});
