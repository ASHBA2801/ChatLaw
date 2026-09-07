import { describe, expect, it } from "vitest";
import {
  numberToIndianWords,
  normalizeCurrency,
  normalizeLegalSections,
  normalizeLegalAbbreviations,
  normalizeTextForSpeech,
  stripCitationsAndTechnicalMarkers,
  stripMarkdownFormatting,
} from "./speechNormalizer";

describe("speechNormalizer - Indian numbering system", () => {
  it("converts numbers to Indian words correctly", () => {
    expect(numberToIndianWords(0)).toBe("zero");
    expect(numberToIndianWords(50)).toBe("fifty");
    expect(numberToIndianWords(500)).toBe("five hundred");
    expect(numberToIndianWords(1000)).toBe("one thousand");
    expect(numberToIndianWords(18000)).toBe("eighteen thousand");
    expect(numberToIndianWords(50000)).toBe("fifty thousand");
    expect(numberToIndianWords(100000)).toBe("one lakh");
    expect(numberToIndianWords(250000)).toBe("two lakh fifty thousand");
    expect(numberToIndianWords(10000000)).toBe("one crore");
    expect(numberToIndianWords(15000000)).toBe("one crore fifty lakh");
  });
});

describe("speechNormalizer - Currency normalization", () => {
  it("normalizes Rupee symbol and Rs abbreviations to words", () => {
    expect(normalizeCurrency("The monthly rent is ₹18,000.")).toBe(
      "The monthly rent is eighteen thousand rupees.",
    );
    expect(normalizeCurrency("Security deposit is Rs. 50,000.")).toBe(
      "Security deposit is fifty thousand rupees.",
    );
    expect(normalizeCurrency("A cheque of ₹2,50,000 was bounced.")).toBe(
      "A cheque of two lakh fifty thousand rupees was bounced.",
    );
    expect(normalizeCurrency("Rent is ₹18,000/mo.")).toBe(
      "Rent is eighteen thousand rupees per month.",
    );
    expect(normalizeCurrency("Compensation of ₹1 Lakh was awarded.")).toBe(
      "Compensation of one lakh rupees was awarded.",
    );
  });
});

describe("speechNormalizer - Legal sections and provisions", () => {
  it("expands parenthesized subsection notation for clear speech", () => {
    expect(normalizeLegalSections("Theft is under Section 303(2).")).toBe(
      "Theft is under Section 303, sub-section 2.",
    );
    expect(normalizeLegalSections("According to Section 303(2)(a).")).toBe(
      "According to Section 303, sub-section 2, clause a.",
    );
    expect(normalizeLegalSections("Notice under Sec. 138.")).toBe(
      "Notice under Section 138.",
    );
    expect(normalizeLegalSections("Protection under Article 21(1).")).toBe(
      "Protection under Article 21, clause 1.",
    );
    expect(normalizeLegalSections("Injunction under Order 39 Rule 1.")).toBe(
      "Injunction under Order 39, Rule 1.",
    );
  });
});

describe("speechNormalizer - Legal abbreviations", () => {
  it("expands statutory acronyms into authoritative names", () => {
    expect(normalizeLegalAbbreviations("punishable under BNS")).toBe(
      "punishable under Bharatiya Nyaya Sanhita",
    );
    expect(normalizeLegalAbbreviations("Procedure under BNSS")).toBe(
      "Procedure under Bharatiya Nagarik Suraksha Sanhita",
    );
    expect(normalizeLegalAbbreviations("Document evidence under BSA")).toBe(
      "Document evidence under Bharatiya Sakshya Adhiniyam",
    );
    expect(normalizeLegalAbbreviations("Section 138 NI Act")).toBe(
      "Section 138 Negotiable Instruments Act",
    );
    expect(normalizeLegalAbbreviations("Lodged an FIR at the station")).toBe(
      "Lodged an First Information Report at the station",
    );
    expect(normalizeLegalAbbreviations("Executed a GPA for property")).toBe(
      "Executed a General Power of Attorney for property",
    );
  });
});

describe("speechNormalizer - Markdown and citation stripping", () => {
  it("removes bracketed citations and markdown syntax", () => {
    const input = "### Punishment\n**Theft** is defined in [1] and [SOURCE 2]. Visit https://chatlaw.in";
    const cleaned = stripMarkdownFormatting(stripCitationsAndTechnicalMarkers(input));
    expect(cleaned).not.toContain("[1]");
    expect(cleaned).not.toContain("[SOURCE 2]");
    expect(cleaned).not.toContain("https://");
    expect(cleaned).not.toContain("###");
    expect(cleaned).not.toContain("**");
  });
});

describe("speechNormalizer - End-to-end legal speech normalization", () => {
  it("processes complex legal answers into clean, speech-friendly prose", () => {
    const rawAnswer = `### Legal Assessment
Theft is punishable under **Section 303(2)** of the **BNS** [1].
The accused must pay a fine of **₹50,000** along with compensation of **₹1 Lakh** [SOURCE 2].
Notice should be issued under **Sec. 138** of the **NI Act**.
For details, see https://official-gazette.gov.in`;

    const normalized = normalizeTextForSpeech(rawAnswer);

    expect(normalized).toContain("Section 303, sub-section 2");
    expect(normalized).toContain("Bharatiya Nyaya Sanhita");
    expect(normalized).toContain("fifty thousand rupees");
    expect(normalized).toContain("one lakh rupees");
    expect(normalized).toContain("Section 138 of the Negotiable Instruments Act");
    expect(normalized).not.toContain("[1]");
    expect(normalized).not.toContain("[SOURCE 2]");
    expect(normalized).not.toContain("https://");
    expect(normalized).not.toContain("###");
    expect(normalized).not.toContain("**");
  });

  it("handles empty or whitespace-only inputs gracefully", () => {
    expect(normalizeTextForSpeech("")).toBe("");
    expect(normalizeTextForSpeech("   ")).toBe("");
  });

  it("normalizes mixed native language text containing currency and section references", () => {
    const rawTamil = "வாடகை ₹18,000 மற்றும் BNS Section 303(2) [1].";
    const normalized = normalizeTextForSpeech(rawTamil);
    expect(normalized).toContain("eighteen thousand rupees");
    expect(normalized).toContain("Bharatiya Nyaya Sanhita");
    expect(normalized).toContain("Section 303, sub-section 2");
    expect(normalized).not.toContain("[1]");
  });
});
