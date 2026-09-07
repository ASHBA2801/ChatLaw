import { prisma } from "@/lib/db/client";
import { CaseAccessError } from "./errors";

function clean(value: unknown, max = 2000): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed ? trimmed.slice(0, max) : null;
}

export async function addTimelineNote(userId: string, caseId: string, input: Record<string, unknown>) {
  const owned = await prisma.case.findFirst({ where: { id: caseId, userId }, select: { id: true } });
  if (!owned) throw new CaseAccessError(404);
  const title = clean(input.title, 180);
  if (!title) throw new CaseAccessError(422, "A note title is required.");
  const occurredAt = typeof input.occurredAt === "string" && input.occurredAt.trim()
    ? new Date(input.occurredAt)
    : new Date();
  if (Number.isNaN(occurredAt.getTime())) {
    throw new CaseAccessError(422, "The event date could not be understood.");
  }
  return prisma.caseTimelineEvent.create({
    data: {
      caseId,
      type: "USER_NOTE",
      title,
      description: clean(input.description),
      occurredAt,
    },
  });
}
