import { beforeEach, describe, expect, it, vi } from "vitest";

const prisma = vi.hoisted(() => ({
  caseDocument: { update: vi.fn() },
}));

vi.mock("@/lib/db/client", () => ({ prisma }));

const getOwnedCaseDocument = vi.hoisted(() => vi.fn());
vi.mock("./documents", () => ({ getOwnedCaseDocument }));

import { summarizeOwnedCaseDocument } from "./summarize";

describe("user-triggered document summary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
  });

  it("refuses to summarize without extracted text", async () => {
    getOwnedCaseDocument.mockResolvedValue({
      id: "doc-1",
      extractedTextStatus: "FAILED",
      extractedText: null,
    });
    await expect(summarizeOwnedCaseDocument("user-a", "case-1", "doc-1")).rejects.toMatchObject({ status: 422 });
  });

  it("stores an AI-generated summary after an explicit request", async () => {
    getOwnedCaseDocument.mockResolvedValue({
      id: "doc-1",
      fileName: "agreement.pdf",
      extractedTextStatus: "READY",
      extractedText: "Security deposit is 50,000.",
      metadata: {},
    });
    prisma.caseDocument.update.mockResolvedValue({
      id: "doc-1",
      metadata: { summary: "Parties are not fully stated.", summary_label: "AI-generated summary" },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ summary: "Parties are not fully stated.", label: "AI-generated summary", model: "mock" }),
    }));
    process.env.RAG_API_URL = "http://127.0.0.1:8000";
    process.env.RAG_API_SECRET = "test-secret";
    const updated = await summarizeOwnedCaseDocument("user-a", "case-1", "doc-1");
    const metadata = updated.metadata as { summary_label?: string };
    expect(metadata.summary_label).toBe("AI-generated summary");
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/summarize/document"), expect.any(Object));
  });

  it("surfaces summary service failure", async () => {
    getOwnedCaseDocument.mockResolvedValue({
      id: "doc-1",
      fileName: "agreement.pdf",
      extractedTextStatus: "READY",
      extractedText: "text",
      metadata: {},
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: "Document summary is unavailable" }),
    }));
    process.env.RAG_API_URL = "http://127.0.0.1:8000";
    process.env.RAG_API_SECRET = "test-secret";
    await expect(summarizeOwnedCaseDocument("user-a", "case-1", "doc-1")).rejects.toMatchObject({ status: 503 });
  });
});
