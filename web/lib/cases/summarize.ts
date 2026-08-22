import "server-only";

import { Prisma } from "@/lib/generated/prisma/client";
import { prisma } from "@/lib/db/client";
import { auditCaseAction } from "./audit";
import { getOwnedCaseDocument } from "./documents";
import { CaseAccessError } from "./errors";

const MAX_SUMMARY_CHARS = 20_000;

export async function summarizeOwnedCaseDocument(userId: string, caseId: string, documentId: string) {
  const document = await getOwnedCaseDocument(userId, caseId, documentId);
  if (document.extractedTextStatus !== "READY" || !document.extractedText) {
    throw new CaseAccessError(422, "This document has no extracted text to summarize.");
  }
  const baseUrl = process.env.RAG_API_URL?.replace(/\/$/, "");
  const secret = process.env.RAG_API_SECRET?.trim();
  if (!baseUrl || !secret) {
    throw new CaseAccessError(503, "Document summary is not configured.");
  }
  auditCaseAction("summary_requested", { userId, caseId, documentId });
  const response = await fetch(`${baseUrl}/api/summarize/document`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${secret}`,
    },
    body: JSON.stringify({
      file_name: document.fileName,
      text: document.extractedText.slice(0, MAX_SUMMARY_CHARS),
    }),
    cache: "no-store",
    signal: AbortSignal.timeout(90_000),
  });
  const payload = await response.json().catch(() => null) as {
    summary?: string;
    label?: string;
    model?: string;
    detail?: string;
  } | null;
  if (!response.ok || !payload?.summary) {
    throw new CaseAccessError(
      response.status === 503 ? 503 : 502,
      typeof payload?.detail === "string" ? payload.detail : "Document summary failed.",
    );
  }
  const metadata = document.metadata && typeof document.metadata === "object" && !Array.isArray(document.metadata)
    ? { ...(document.metadata as Record<string, unknown>) }
    : {};
  metadata.summary = payload.summary;
  metadata.summary_label = payload.label || "AI-generated summary";
  metadata.summary_model = payload.model ?? null;
  const updated = await prisma.caseDocument.update({
    where: { id: document.id },
    data: { metadata: metadata as Prisma.InputJsonValue },
  });
  return updated;
}
