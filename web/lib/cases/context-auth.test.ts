import { beforeEach, describe, expect, it, vi } from "vitest";

const prisma = vi.hoisted(() => ({
  case: { findFirst: vi.fn() },
}));

vi.mock("@/lib/db/client", () => ({ prisma }));

import { CaseAccessError } from "./errors";
import { loadAuthorizedCaseContext } from "./context";
import { formatExtractedPages } from "./metadata";

describe("authorized case context", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns excerpts only for the owning user's ready documents", async () => {
    prisma.case.findFirst.mockResolvedValue({
      id: "case-1",
      documents: [{
        id: "doc-1",
        fileName: "Rental Agreement.pdf",
        extractedText: formatExtractedPages([{ page: 4, text: "Security deposit of 50000" }]),
      }],
    });
    const excerpts = await loadAuthorizedCaseContext("user-a", "case-1", "security deposit");
    expect(excerpts[0]).toMatchObject({ document_id: "doc-1", page: 4 });
  });

  it("does not load another user's case documents", async () => {
    prisma.case.findFirst.mockResolvedValue(null);
    await expect(loadAuthorizedCaseContext("user-b", "case-1", "deposit")).rejects.toBeInstanceOf(CaseAccessError);
  });
});
