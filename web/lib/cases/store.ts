import { prisma } from "@/lib/db/client";
import { publicCaseDocument } from "./documents";
import { CaseAccessError } from "./errors";
export { CaseAccessError } from "./errors";
import { isCaseStatus } from "./status";
export { isCaseStatus } from "./status";

function clean(value: unknown, max = 5000): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed ? trimmed.slice(0, max) : null;
}

export async function listOwnedCases(userId: string) {
  return prisma.case.findMany({
    where: { userId },
    orderBy: { updatedAt: "desc" },
    include: { _count: { select: { documents: { where: { deletedAt: null } }, timeline: true } } },
  });
}

export async function getOwnedCase(userId: string, caseId: string) {
  const item = await prisma.case.findFirst({ where: { id: caseId, userId }, include: { documents: { where: { deletedAt: null }, orderBy: { createdAt: "desc" } }, timeline: { orderBy: { occurredAt: "desc" } }, importantDates: { orderBy: { date: "asc" } } } });
  if (!item) throw new CaseAccessError(404);
  return item;
}

export async function createOwnedCase(userId: string, input: Record<string, unknown>) {
  const title = clean(input.title, 200);
  if (!title) throw new CaseAccessError(422, "A case title is required");
  return prisma.$transaction(async (tx) => {
    const item = await tx.case.create({ data: { userId, title, description: clean(input.description), category: clean(input.category, 160), subCategory: clean(input.subCategory, 160), jurisdiction: clean(input.jurisdiction, 160), city: clean(input.city, 120), state: clean(input.state, 120), country: clean(input.country, 120) } });
    await tx.caseTimelineEvent.create({ data: { caseId: item.id, type: "CASE_CREATED", title: "Case created" } });
    return item;
  });
}

export async function updateOwnedCase(userId: string, caseId: string, input: Record<string, unknown>) {
  const existing = await prisma.case.findFirst({ where: { id: caseId, userId }, select: { id: true } });
  if (!existing) throw new CaseAccessError(404);
  const status = input.status === undefined ? undefined : isCaseStatus(input.status) ? input.status : null;
  if (input.status !== undefined && !status) throw new CaseAccessError(422, "Invalid case status");
  return prisma.case.update({ where: { id: caseId }, data: { title: input.title === undefined ? undefined : clean(input.title, 200) || undefined, description: input.description === undefined ? undefined : clean(input.description), category: input.category === undefined ? undefined : clean(input.category, 160), subCategory: input.subCategory === undefined ? undefined : clean(input.subCategory, 160), jurisdiction: input.jurisdiction === undefined ? undefined : clean(input.jurisdiction, 160), city: input.city === undefined ? undefined : clean(input.city, 120), state: input.state === undefined ? undefined : clean(input.state, 120), country: input.country === undefined ? undefined : clean(input.country, 120), status: status || undefined, archivedAt: status === "ARCHIVED" ? new Date() : status ? null : undefined } });
}

export async function archiveOwnedCase(userId: string, caseId: string) {
  const result = await prisma.case.updateMany({ where: { id: caseId, userId }, data: { status: "ARCHIVED", archivedAt: new Date() } });
  if (!result.count) throw new CaseAccessError(404);
  await prisma.caseTimelineEvent.create({ data: { caseId, type: "CASE_ARCHIVED", title: "Case archived" } });
}

export function toPublicCase(item: Awaited<ReturnType<typeof getOwnedCase>>) {
  return {
    ...item,
    documents: item.documents.map(publicCaseDocument),
  };
}