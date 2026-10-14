import { describe, expect, it } from "vitest";

import type { Citation } from "@/lib/api/rag";

import { stripRenderedCitationLabels } from "./citationText";

const citation = (id: number, document: string): Citation => ({
  id, document, section: null, page: null, chunk_id: `c${id}`,
});

describe("stripRenderedCitationLabels", () => {
  it("keeps the marker and sentence punctuation but drops the spelled-out source", () => {
    const answer =
      "Murder is punishable with death or life imprisonment [5] THE BHARATIYA NYAYA SANHITA, 2023 — Section 103 — Page 34. " +
      "A group of five or more [5] THE BHARATIYA NYAYA SANHITA, 2023 — Section 103(2) — Page 34 — Subsection (2), each member.";
    expect(stripRenderedCitationLabels(answer, [citation(5, "THE BHARATIYA NYAYA SANHITA, 2023")])).toBe(
      "Murder is punishable with death or life imprisonment [5]. A group of five or more [5], each member.",
    );
  });

  it("handles case documents and leaves unknown markers alone", () => {
    const answer = "The lease says so [2] Case Document — lease.pdf — Page 3, see also [9] Other Act.";
    expect(stripRenderedCitationLabels(answer, [citation(2, "lease.pdf")])).toBe(
      "The lease says so [2], see also [9] Other Act.",
    );
  });
});
