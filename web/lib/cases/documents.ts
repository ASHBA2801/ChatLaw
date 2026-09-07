import { createHash } from "node:crypto";
import { PDFDocument } from "pdf-lib";
import { Prisma } from "@/lib/generated/prisma/client";
import { prisma } from "@/lib/db/client";
import { auditCaseAction } from "./audit";
import { CaseAccessError } from "./errors";
import { extractPdfBytes, ExtractionError } from "./extraction";
import { validateCaseFile as validateFile } from "./file-validation";
import { detectDocumentSignals, formatExtractedPages } from "./metadata";
import { caseStorageKey, getCaseStorage, type StorageAdapter } from "./storage";

export function validateCaseFile(file: File) {
  try {
    validateFile(file);
  } catch (error) {
    throw new CaseAccessError(422, error instanceof Error ? error.message : "Invalid file");
  }
}

export type CaseDocumentDeps = {
  storage?: StorageAdapter;
  extractPdf?: typeof extractPdfBytes;
};

type JsonRecord = Record<string, unknown>;

function asJson(value: JsonRecord): Prisma.InputJsonValue {
  return value as Prisma.InputJsonValue;
}

function safeFileName(name: string): string {
  return name.replace(/[^\w .()\-]/gu, "_").slice(0, 255);
}

async function readPdfPageCount(bytes: Buffer): Promise<number> {
  try {
    return (await PDFDocument.load(bytes, { ignoreEncryption: false })).getPageCount();
  } catch {
    throw new CaseAccessError(422, "The PDF could not be read. It may be encrypted or malformed.");
  }
}

async function persistExtraction(
  documentId: string,
  caseId: string,
  bytes: Buffer,
  extractPdf: typeof extractPdfBytes,
) {
  try {
    const extracted = await extractPdf(bytes);
    const extractedText = formatExtractedPages(extracted.pages);
    const signals = detectDocumentSignals(extractedText);
    await prisma.caseDocument.update({
      where: { id: documentId },
      data: {
        extractedTextStatus: extractedText ? "READY" : "FAILED",
        extractedText: extractedText || null,
        pageCount: extracted.page_count,
        metadata: asJson({
          extraction: extractedText ? "deterministic_pdf_text" : "empty_text_layer",
          pdf_metadata: extracted.metadata,
          ...signals,
          ...(extractedText ? {} : { error: "No extractable text was found. The file may be scanned." }),
        }),
      },
    });
    if (extractedText) {
      await prisma.caseTimelineEvent.create({
        data: { caseId, type: "DOCUMENT_PROCESSED", title: "Document processed" },
      });
    }
  } catch (error) {
    const message = error instanceof ExtractionError ? error.message : "Text extraction failed";
    await prisma.caseDocument.update({
      where: { id: documentId },
      data: {
        extractedTextStatus: "FAILED",
        extractedText: null,
        metadata: asJson({ extraction: "failed", error: message }),
      },
    });
  }
}

export async function addCaseDocument(
  userId: string,
  caseId: string,
  file: File,
  deps: CaseDocumentDeps = {},
) {
  validateCaseFile(file);
  const ownedCase = await prisma.case.findFirst({
    where: { id: caseId, userId },
    select: { id: true },
  });
  if (!ownedCase) throw new CaseAccessError(404);

  const bytes = Buffer.from(await file.arrayBuffer());
  if (!bytes.subarray(0, 5).toString("latin1").startsWith("%PDF")) {
    throw new CaseAccessError(422, "The file is not a valid PDF.");
  }
  const checksum = createHash("sha256").update(bytes).digest("hex");
  const duplicate = await prisma.caseDocument.findFirst({
    where: { userId, checksum, deletedAt: null },
    select: { id: true, caseId: true },
  });
  if (duplicate) {
    throw new CaseAccessError(409, "This document has already been added to your workspace.");
  }

  const pageCount = await readPdfPageCount(bytes);
  const storage = deps.storage ?? getCaseStorage();
  const storageKey = caseStorageKey(userId, caseId, checksum);
  const fileName = safeFileName(file.name);
  await storage.put(storageKey, bytes);

  let document;
  try {
    document = await prisma.$transaction(async (tx) => {
      const created = await tx.caseDocument.create({
        data: {
          caseId,
          userId,
          fileName,
          fileType: "application/pdf",
          fileSize: bytes.length,
          storageKey,
          checksum,
          extractedTextStatus: "PROCESSING",
          pageCount,
          metadata: asJson({ extraction: "processing" }),
        },
      });
      await tx.caseTimelineEvent.create({
        data: { caseId, type: "DOCUMENT_UPLOADED", title: `${fileName.slice(0, 180)} uploaded` },
      });
      return created;
    });
  } catch (error) {
    await storage.delete(storageKey).catch(() => undefined);
    throw error;
  }

  auditCaseAction("document_uploaded", { userId, caseId, documentId: document.id });
  await persistExtraction(document.id, caseId, bytes, deps.extractPdf ?? extractPdfBytes);
  const refreshed = await prisma.caseDocument.findFirst({
    where: { id: document.id, userId, caseId },
  });
  return refreshed ?? document;
}

export async function getOwnedCaseDocument(userId: string, caseId: string, documentId: string) {
  const document = await prisma.caseDocument.findFirst({
    where: { id: documentId, caseId, userId, deletedAt: null },
  });
  if (!document) throw new CaseAccessError(404, "Document not found");
  return document;
}

export async function readOwnedCaseDocumentBytes(
  userId: string,
  caseId: string,
  documentId: string,
  deps: CaseDocumentDeps = {},
) {
  const document = await getOwnedCaseDocument(userId, caseId, documentId);
  const storage = deps.storage ?? getCaseStorage();
  try {
    const bytes = await storage.get(document.storageKey);
    auditCaseAction("document_viewed", { userId, caseId, documentId });
    return { document, bytes };
  } catch {
    throw new CaseAccessError(404, "The stored file is no longer available.");
  }
}

export async function renameCaseDocument(
  userId: string,
  caseId: string,
  documentId: string,
  fileName: string,
) {
  const nextName = safeFileName(fileName);
  if (!nextName.toLowerCase().endsWith(".pdf")) {
    throw new CaseAccessError(422, "The filename must end with .pdf.");
  }
  const result = await prisma.caseDocument.updateMany({
    where: { id: documentId, caseId, userId, deletedAt: null },
    data: { fileName: nextName },
  });
  if (!result.count) throw new CaseAccessError(404, "Document not found");
  return getOwnedCaseDocument(userId, caseId, documentId);
}

export async function retryCaseDocumentExtraction(
  userId: string,
  caseId: string,
  documentId: string,
  deps: CaseDocumentDeps = {},
) {
  const document = await getOwnedCaseDocument(userId, caseId, documentId);
  const storage = deps.storage ?? getCaseStorage();
  let bytes: Buffer;
  try {
    bytes = await storage.get(document.storageKey);
  } catch {
    throw new CaseAccessError(404, "The stored file is no longer available.");
  }
  await prisma.caseDocument.update({
    where: { id: document.id },
    data: { extractedTextStatus: "PROCESSING", metadata: asJson({ extraction: "processing" }) },
  });
  await persistExtraction(document.id, caseId, bytes, deps.extractPdf ?? extractPdfBytes);
  return getOwnedCaseDocument(userId, caseId, documentId);
}

export async function deleteCaseDocument(
  userId: string,
  caseId: string,
  documentId: string,
  deps: CaseDocumentDeps = {},
) {
  const document = await getOwnedCaseDocument(userId, caseId, documentId);
  const result = await prisma.caseDocument.updateMany({
    where: { id: documentId, caseId, userId, deletedAt: null },
    data: {
      deletedAt: new Date(),
      extractedText: null,
      extractedTextStatus: "FAILED",
      checksum: `${document.checksum}:deleted:${document.id}`,
      metadata: asJson({ extraction: "deleted" }),
    },
  });
  if (!result.count) throw new CaseAccessError(404, "Document not found");
  const storage = deps.storage ?? getCaseStorage();
  await storage.delete(document.storageKey).catch(() => undefined);
  await prisma.caseTimelineEvent.create({
    data: { caseId, type: "DOCUMENT_DELETED", title: `${document.fileName.slice(0, 180)} deleted` },
  });
  auditCaseAction("document_deleted", { userId, caseId, documentId });
}

export function publicCaseDocument(document: {
  id: string;
  fileName: string;
  fileType: string;
  fileSize: number;
  checksum: string;
  extractedTextStatus: string;
  extractedText: string | null;
  pageCount: number | null;
  metadata: Prisma.JsonValue;
  createdAt: Date;
  updatedAt: Date;
}) {
  const metadata = document.metadata && typeof document.metadata === "object" && !Array.isArray(document.metadata)
    ? document.metadata as Record<string, unknown>
    : {};
  return {
    id: document.id,
    fileName: document.fileName,
    fileType: document.fileType,
    fileSize: document.fileSize,
    checksum: document.checksum,
    extractedTextStatus: document.extractedTextStatus,
    pageCount: document.pageCount,
    createdAt: document.createdAt,
    updatedAt: document.updatedAt,
    hasExtractedText: Boolean(document.extractedText),
    detectedDates: Array.isArray(metadata.detected_dates) ? metadata.detected_dates : [],
    detectedHeadings: Array.isArray(metadata.detected_headings) ? metadata.detected_headings : [],
    extractionError: typeof metadata.error === "string" ? metadata.error : null,
    summary: typeof metadata.summary === "string" ? metadata.summary : null,
    summaryLabel: typeof metadata.summary_label === "string" ? metadata.summary_label : null,
  };
}
