import { PDFDocument } from "pdf-lib";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CaseAccessError } from "./errors";
import { MemoryStorageAdapter, caseStorageKey } from "./storage";
import { validateCaseFile } from "./file-validation";

const prisma = vi.hoisted(() => ({
  case: { findFirst: vi.fn() },
  caseDocument: {
    findFirst: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    updateMany: vi.fn(),
  },
  caseTimelineEvent: { create: vi.fn() },
  $transaction: vi.fn(),
}));

vi.mock("@/lib/db/client", () => ({ prisma }));

const extractPdfBytes = vi.hoisted(() => vi.fn());
vi.mock("./extraction", () => ({
  extractPdfBytes,
  ExtractionError: class ExtractionError extends Error {
    status = 503;
  },
}));

import { addCaseDocument, deleteCaseDocument, getOwnedCaseDocument } from "./documents";

async function pdfFile(name = "agreement.pdf") {
  const pdf = await PDFDocument.create();
  pdf.addPage();
  const bytes = await pdf.save();
  return new File([Buffer.from(bytes)], name, { type: "application/pdf" });
}

describe("case document validation", () => {
  it("accepts PDF metadata and rejects unsupported formats", () => {
    expect(() => validateCaseFile(new File(["%PDF"], "agreement.pdf", { type: "application/pdf" }))).not.toThrow();
    expect(() => validateCaseFile(new File(["binary"], "script.exe", { type: "application/octet-stream" }))).toThrow("Only PDF");
  });

  it("rejects traversal-like names", () => {
    expect(() => validateCaseFile(new File(["%PDF"], "../private.pdf", { type: "application/pdf" }))).toThrow("filename");
  });
});

describe("owned case documents", () => {
  const storage = new MemoryStorageAdapter();

  beforeEach(() => {
    storage.files.clear();
    vi.clearAllMocks();
    prisma.$transaction.mockImplementation(async (fn: (tx: typeof prisma) => unknown) => fn(prisma));
    prisma.case.findFirst.mockResolvedValue({ id: "case-1" });
    prisma.caseDocument.findFirst.mockResolvedValue(null);
    prisma.caseDocument.create.mockImplementation(async ({ data }: { data: Record<string, unknown> }) => ({
      id: "doc-1",
      ...data,
    }));
    prisma.caseDocument.update.mockResolvedValue({ id: "doc-1" });
    prisma.caseTimelineEvent.create.mockResolvedValue({});
    extractPdfBytes.mockResolvedValue({
      page_count: 1,
      pages: [{ page: 1, text: "Security deposit terms" }],
      metadata: {},
    });
  });

  it("stores bytes, checksums, and extracted text for the owning user", async () => {
    const file = await pdfFile();
    const created = await addCaseDocument("user-a", "case-1", file, { storage, extractPdf: extractPdfBytes });
    expect(created.id).toBe("doc-1");
    const key = [...storage.files.keys()][0];
    expect(key).toMatch(/^case\/user-a\/case-1\/[a-f0-9]{64}\.pdf$/);
    expect(extractPdfBytes).toHaveBeenCalledOnce();
    expect(prisma.caseDocument.update).toHaveBeenCalled();
  });

  it("rejects another user's case", async () => {
    prisma.case.findFirst.mockResolvedValue(null);
    await expect(addCaseDocument("user-b", "case-1", await pdfFile(), { storage, extractPdf: extractPdfBytes }))
      .rejects.toMatchObject({ status: 404 });
  });

  it("rejects duplicate checksums", async () => {
    prisma.caseDocument.findFirst.mockResolvedValue({ id: "existing", caseId: "case-1" });
    await expect(addCaseDocument("user-a", "case-1", await pdfFile(), { storage, extractPdf: extractPdfBytes }))
      .rejects.toMatchObject({ status: 409 });
  });

  it("marks extraction failure without fabricating text", async () => {
    extractPdfBytes.mockRejectedValue(new Error("parser down"));
    await addCaseDocument("user-a", "case-1", await pdfFile(), { storage, extractPdf: extractPdfBytes });
    expect(prisma.caseDocument.update).toHaveBeenCalledWith(expect.objectContaining({
      data: expect.objectContaining({ extractedTextStatus: "FAILED", extractedText: null }),
    }));
  });

  it("requires ownership to read a document", async () => {
    prisma.caseDocument.findFirst.mockResolvedValue(null);
    await expect(getOwnedCaseDocument("user-b", "case-1", "doc-1")).rejects.toBeInstanceOf(CaseAccessError);
  });

  it("clears extracted text and storage on delete", async () => {
    const key = caseStorageKey("user-a", "case-1", "d".repeat(64));
    await storage.put(key, Buffer.from("%PDF"));
    prisma.caseDocument.findFirst.mockResolvedValue({
      id: "doc-1",
      caseId: "case-1",
      userId: "user-a",
      fileName: "agreement.pdf",
      storageKey: key,
      checksum: "d".repeat(64),
      deletedAt: null,
    });
    prisma.caseDocument.updateMany.mockResolvedValue({ count: 1 });
    await deleteCaseDocument("user-a", "case-1", "doc-1", { storage });
    expect(await storage.exists(key)).toBe(false);
    expect(prisma.caseDocument.updateMany).toHaveBeenCalledWith(expect.objectContaining({
      data: expect.objectContaining({ extractedText: null, deletedAt: expect.any(Date) }),
    }));
  });
});
