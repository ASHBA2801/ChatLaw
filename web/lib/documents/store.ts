import "server-only";

import { Prisma } from "@/lib/generated/prisma/client";
import { prisma } from "@/lib/db/client";
import { DocumentAccessError } from "./errors";
import { sanitizeDocument } from "./sanitize";
import { parseStatus } from "./status";
import type { DocumentStatus, DocumentValues, GeneratedDocumentPayload } from "./types";

export { DocumentAccessError } from "./errors";

function generationRecord(
  payload: GeneratedDocumentPayload,
  extra?: Record<string, unknown> | null,
): Prisma.InputJsonValue {
  return {
    ...(extra ?? {}),
    signatures: payload.signatures,
    disclaimer: payload.disclaimer ?? null,
    model_used: payload.model_used ?? false,
  } as unknown as Prisma.InputJsonValue;
}

export async function listOwnedDocuments(userId: string) {
  return prisma.userDocument.findMany({
    where: { userId },
    orderBy: { updatedAt: "desc" },
    select: {
      id: true,
      title: true,
      templateId: true,
      documentType: true,
      jurisdictionCountry: true,
      jurisdictionRegion: true,
      status: true,
      currentVersionNumber: true,
      createdAt: true,
      updatedAt: true,
    },
  });
}

export async function getOwnedDocument(userId: string, documentId: string) {
  const document = await prisma.userDocument.findFirst({
    where: { id: documentId, userId },
    include: { versions: { orderBy: { versionNumber: "desc" } } },
  });
  if (!document) {
    throw new DocumentAccessError(404, "Document not found");
  }
  return document;
}

export async function createOwnedDocument(input: {
  userId: string;
  title: string;
  templateId: string;
  documentType: string;
  jurisdictionCountry: string;
  jurisdictionRegion: string | null;
  values: DocumentValues;
  payload: GeneratedDocumentPayload;
  generation?: Record<string, unknown> | null;
  conversationId?: string | null;
}) {
  const payload = sanitizeDocument(input.payload);
  return prisma.$transaction(async (tx) => {
    const document = await tx.userDocument.create({
      data: {
        userId: input.userId,
        conversationId: input.conversationId || null,
        title: payload.title,
        templateId: input.templateId,
        documentType: input.documentType,
        jurisdictionCountry: input.jurisdictionCountry,
        jurisdictionRegion: input.jurisdictionRegion,
        status: "draft",
        currentVersionNumber: 1,
      },
    });
    const version = await tx.userDocumentVersion.create({
      data: {
        documentId: document.id,
        versionNumber: 1,
        status: "draft",
        title: payload.title,
        input: input.values as unknown as Prisma.InputJsonValue,
        sections: payload.sections as unknown as Prisma.InputJsonValue,
        warnings: payload.warnings as unknown as Prisma.InputJsonValue,
        citations: payload.citations as unknown as Prisma.InputJsonValue,
        generation: generationRecord(payload, input.generation),
      },
    });
    return { document, version };
  });
}

export async function addOwnedVersion(input: {
  userId: string;
  documentId: string;
  values: DocumentValues;
  payload: GeneratedDocumentPayload;
  status?: DocumentStatus;
  generation?: Record<string, unknown> | null;
}) {
  const payload = sanitizeDocument(input.payload);
  return prisma.$transaction(async (tx) => {
    const document = await tx.userDocument.findFirst({ where: { id: input.documentId, userId: input.userId } });
    if (!document) {
      throw new DocumentAccessError(404, "Document not found");
    }
    const nextNumber = document.currentVersionNumber + 1;
    const status = input.status ?? parseStatus(document.status);
    const version = await tx.userDocumentVersion.create({
      data: {
        documentId: document.id,
        versionNumber: nextNumber,
        status,
        title: payload.title,
        input: input.values as unknown as Prisma.InputJsonValue,
        sections: payload.sections as unknown as Prisma.InputJsonValue,
        warnings: payload.warnings as unknown as Prisma.InputJsonValue,
        citations: payload.citations as unknown as Prisma.InputJsonValue,
        generation: generationRecord(payload, input.generation),
      },
    });
    const updated = await tx.userDocument.update({
      where: { id: document.id },
      data: {
        title: payload.title,
        status,
        currentVersionNumber: nextNumber,
        jurisdictionCountry: payload.jurisdiction_country,
        jurisdictionRegion: payload.jurisdiction_region,
      },
    });
    return { document: updated, version };
  });
}

export async function updateOwnedStatus(userId: string, documentId: string, status: DocumentStatus) {
  const result = await prisma.userDocument.updateMany({
    where: { id: documentId, userId },
    data: { status },
  });
  if (result.count === 0) {
    throw new DocumentAccessError(404, "Document not found");
  }
  return getOwnedDocument(userId, documentId);
}

export async function deleteOwnedDocument(userId: string, documentId: string) {
  const result = await prisma.userDocument.deleteMany({ where: { id: documentId, userId } });
  if (result.count === 0) {
    throw new DocumentAccessError(404, "Document not found");
  }
}

export function currentPayload(document: Awaited<ReturnType<typeof getOwnedDocument>>): {
  values: DocumentValues;
  payload: GeneratedDocumentPayload;
  versionNumber: number;
} {
  const version = document.versions.find((item) => item.versionNumber === document.currentVersionNumber) ?? document.versions[0];
  if (!version) {
    throw new DocumentAccessError(404, "Document version not found");
  }
  const payload: GeneratedDocumentPayload = {
    template_id: document.templateId,
    title: version.title,
    document_type: document.documentType,
    jurisdiction_country: document.jurisdictionCountry,
    jurisdiction_region: document.jurisdictionRegion ?? "",
    sections: version.sections as unknown as GeneratedDocumentPayload["sections"],
    signatures: ((version.generation as { signatures?: GeneratedDocumentPayload["signatures"] } | null)?.signatures) ?? [],
    warnings: version.warnings as unknown as GeneratedDocumentPayload["warnings"],
    citations: version.citations as unknown as GeneratedDocumentPayload["citations"],
    disclaimer: typeof (version.generation as { disclaimer?: string } | null)?.disclaimer === "string"
      ? (version.generation as { disclaimer: string }).disclaimer
      : undefined,
  };
  return {
    values: version.input as DocumentValues,
    payload,
    versionNumber: version.versionNumber,
  };
}
