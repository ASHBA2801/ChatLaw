import { describe, expect, it } from "vitest";

import { buildDocx } from "./export/docx";
import { buildPdf } from "./export/pdf";
import { getTemplate, listTemplates } from "./templates";
import type { GeneratedDocumentPayload } from "./types";

describe("document taxonomy and model categories", () => {
  it("covers all required Indian legal document categories", () => {
    const templates = listTemplates();
    const categories = new Set(templates.map((t) => t.category));
    expect(categories.has("agreement")).toBe(true);
    expect(categories.has("deed")).toBe(true);
    expect(categories.has("complaint")).toBe(true);
    expect(categories.has("notice")).toBe(true);
    expect(categories.has("affidavit")).toBe(true);
    expect(categories.has("application")).toBe(true);
  });

  it("ensures deeds have witness and schedule specifications", () => {
    const saleDeed = getTemplate("sale_deed");
    expect(saleDeed.category).toBe("deed");
    expect(saleDeed.source?.authority).toBeDefined();
    expect(saleDeed.executionRequirements?.length).toBeGreaterThan(0);
    expect(saleDeed.witnesses?.length).toBe(2);
    expect(saleDeed.schedules?.length).toBe(1);
    expect(saleDeed.schedules?.[0].boundariesFields?.north).toBe("boundary_north");
  });

  it("ensures Tamil Nadu rental agreement has bilingual and registration metadata", () => {
    const tnRental = getTemplate("rental_agreement_tamil_nadu");
    expect(tnRental.jurisdictionRegion).toBe("Tamil Nadu");
    expect(tnRental.language).toContain("Tamil");
    expect(tnRental.witnesses?.length).toBe(2);
    expect(tnRental.schedules?.length).toBe(1);
  });

  it("exports authentic A4 PDF and DOCX for Deeds and Notices with schedules and witnesses", async () => {
    const deedPayload: GeneratedDocumentPayload = {
      template_id: "sale_deed",
      title: "DEED OF ABSOLUTE SALE",
      document_type: "Deed of Absolute Sale",
      jurisdiction_country: "IN",
      jurisdiction_region: "Tamil Nadu",
      execution_requirements: [
        "To be printed on stamp paper of value prescribed by State Stamp Act",
        "Mandatory registration under Section 17 of the Registration Act, 1908",
      ],
      sections: [
        { id: "title", title: "DEED OF ABSOLUTE SALE", body: "This deed of absolute sale is made on this 21st day of August 2026...", required: true, number: null },
        { id: "recitals", title: "Recitals of Title", body: "WHEREAS the Vendor is the absolute owner of the property...", required: true, number: null },
        { id: "conveyance", title: "Grant and Conveyance", body: "The Vendor hereby conveys, transfers and assigns all right, title and interest...", required: true, number: 1 },
      ],
      signatures: [
        { party_id: "vendor", role: "Vendor", name: "Murugan S", lines: ["VENDOR", "Name: Murugan S", "Signature: ____________", "Date: 2026-08-21"] },
        { party_id: "witness_1", role: "Witness 1", name: "Karthik R", lines: ["WITNESS 1", "Name: Karthik R", "Address: 10 North St, Chennai", "Signature: ____________"] },
      ],
      schedules: [
        {
          id: "schedule_property",
          title: "SCHEDULE OF CONVEYED PROPERTY",
          description: "Plot No. 42, Gandhinagar, Adyar, Chennai - 600020",
          boundaries: {
            north: "Plot No. 41",
            south: "30-feet Road",
            east: "Plot No. 43",
            west: "Public Park",
          },
        },
      ],
      warnings: [{ code: "ai_generated", message: "Review this draft." }],
      citations: [],
      disclaimer: "Not legal advice.",
    };

    const pdfBytes = await buildPdf(deedPayload);
    expect(pdfBytes.byteLength).toBeGreaterThan(500);

    const docxBuffer = await buildDocx(deedPayload);
    expect(docxBuffer.byteLength).toBeGreaterThan(500);
  });
});
