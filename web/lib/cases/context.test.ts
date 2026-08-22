import { describe, expect, it } from "vitest";
import { formatExtractedPages, splitExtractedPages, detectDocumentSignals } from "./metadata";
import { selectCaseExcerpts, tokenizeQuery } from "./context";

describe("extracted page markers", () => {
  it("round-trips page boundaries", () => {
    const text = formatExtractedPages([
      { page: 1, text: "Rental agreement" },
      { page: 4, text: "Security deposit of 50,000" },
    ]);
    expect(splitExtractedPages(text)).toEqual([
      { page: 1, text: "Rental agreement" },
      { page: 4, text: "Security deposit of 50,000" },
    ]);
  });

  it("detects dates and headings without claiming legal meaning", () => {
    const signals = detectDocumentSignals("SECURITY DEPOSIT\nNotice dated 20 Aug 2026 and 21/08/2026");
    expect(signals.detected_headings).toContain("SECURITY DEPOSIT");
    expect(signals.detected_dates.length).toBeGreaterThan(0);
  });
});

describe("case context selection", () => {
  it("returns only query-matching pages and caps the result", () => {
    const excerpts = selectCaseExcerpts([
      {
        id: "doc-1",
        fileName: "Rental Agreement.pdf",
        extractedText: formatExtractedPages([
          { page: 1, text: "Parties and recitals" },
          { page: 4, text: "The security deposit shall be refunded within 30 days." },
        ]),
      },
      {
        id: "doc-2",
        fileName: "Unrelated.pdf",
        extractedText: formatExtractedPages([{ page: 1, text: "Parking rules only" }]),
      },
    ], "What does my rental agreement say about the security deposit?", { pageLimit: 2 });
    expect(excerpts).toEqual([
      expect.objectContaining({ document_id: "doc-1", page: 4, file_name: "Rental Agreement.pdf" }),
    ]);
    expect(excerpts[0].text).toContain("security deposit");
  });

  it("does not invent pages when there is no overlap", () => {
    expect(selectCaseExcerpts([
      { id: "doc-1", fileName: "A.pdf", extractedText: formatExtractedPages([{ page: 1, text: "Hello" }]) },
    ], "termination clause")).toEqual([]);
  });

  it("tokenizes useful query terms", () => {
    expect(tokenizeQuery("What does the agreement say about termination?")).toEqual(
      expect.arrayContaining(["agreement", "say", "termination"]),
    );
  });
});
