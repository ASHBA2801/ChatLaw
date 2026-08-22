import { describe, expect, it } from "vitest";

import {
  DEFAULT_LANGUAGE,
  formatLanguageLabel,
  getLanguage,
  getPinnedLanguages,
  isLanguageCode,
  LANGUAGES,
} from "@/lib/i18n/languages";
import {
  domainToDocumentTemplate,
  hasSimpleTermsSection,
  parseLegalAnswerSections,
} from "@/lib/chat/answerSections";

describe("language catalog", () => {
  it("includes English plus 22 Eighth Schedule languages", () => {
    expect(LANGUAGES).toHaveLength(23);
    expect(isLanguageCode("en")).toBe(true);
    expect(isLanguageCode("ta")).toBe(true);
    expect(isLanguageCode("hi")).toBe(true);
    expect(isLanguageCode("xx")).toBe(false);
    expect(getLanguage("te").nativeName).toBe("తెలుగు");
    expect(DEFAULT_LANGUAGE).toBe("en");
  });

  it("pins common languages and formats labels", () => {
    const pinned = getPinnedLanguages().map((lang) => lang.code);
    expect(pinned).toEqual(expect.arrayContaining(["en", "hi", "ta", "te", "kn", "ml", "mr", "bn", "gu", "pa"]));
    expect(formatLanguageLabel(getLanguage("ta"))).toBe("தமிழ் — Tamil");
    expect(formatLanguageLabel(getLanguage("en"))).toBe("English");
  });
});

describe("answer sections", () => {
  it("parses markdown section headings", () => {
    const sections = parseLegalAnswerSections(
      "## Short answer\nDeposit return depends on the agreement [1].\n\n## In simple terms\nYou may ask for the deposit back.\n",
    );
    expect(sections.map((s) => s.id)).toEqual(["short", "simple"]);
    expect(hasSimpleTermsSection(sections)).toBe(true);
  });

  it("maps interview domains to document templates", () => {
    expect(domainToDocumentTemplate("tenancy")).toBe("rent_lease");
    expect(domainToDocumentTemplate("employment")).toBe("service_agreement");
    expect(domainToDocumentTemplate("contract")).toBe("nda");
    expect(domainToDocumentTemplate("consumer")).toBe("consumer_complaint");
    expect(domainToDocumentTemplate("criminal")).toBe("complaint");
    expect(domainToDocumentTemplate("unknown")).toBe("legal_notice");
  });
});

describe("research query state", () => {
  it("builds research deep links from chat queries", () => {
    const q = encodeURIComponent("security deposit landlord");
    expect(`/research?q=${q}`).toBe("/research?q=security%20deposit%20landlord");
  });
});
