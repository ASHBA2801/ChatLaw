import { prisma } from "@/lib/db/client";
import { CaseAccessError } from "./errors";

const REMINDERS = new Set(["none", "day_of", "day_before"]);

function clean(value: unknown, max = 2000): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed ? trimmed.slice(0, max) : null;
}

function parseDate(value: unknown): Date {
  if (typeof value !== "string" || !value.trim()) {
    throw new CaseAccessError(422, "A date is required.");
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    throw new CaseAccessError(422, "The date could not be understood.");
  }
  return parsed;
}

async function requireOwnedCase(userId: string, caseId: string) {
  const owned = await prisma.case.findFirst({ where: { id: caseId, userId }, select: { id: true } });
  if (!owned) throw new CaseAccessError(404);
}

export async function listImportantDates(userId: string, caseId: string) {
  await requireOwnedCase(userId, caseId);
  return prisma.caseImportantDate.findMany({ where: { caseId }, orderBy: { date: "asc" } });
}

export async function createImportantDate(userId: string, caseId: string, input: Record<string, unknown>) {
  await requireOwnedCase(userId, caseId);
  const title = clean(input.title, 180);
  if (!title) throw new CaseAccessError(422, "A title is required.");
  const reminder = typeof input.reminderPreference === "string" && REMINDERS.has(input.reminderPreference)
    ? input.reminderPreference
    : "none";
  const item = await prisma.$transaction(async (tx) => {
    const created = await tx.caseImportantDate.create({
      data: {
        caseId,
        title,
        description: clean(input.description),
        date: parseDate(input.date),
        reminderPreference: reminder,
      },
    });
    await tx.caseTimelineEvent.create({
      data: {
        caseId,
        type: "IMPORTANT_DATE",
        title: `${title} added`,
        description: created.date.toISOString().slice(0, 10),
        occurredAt: created.date,
      },
    });
    return created;
  });
  return item;
}

export async function updateImportantDate(
  userId: string,
  caseId: string,
  dateId: string,
  input: Record<string, unknown>,
) {
  await requireOwnedCase(userId, caseId);
  const existing = await prisma.caseImportantDate.findFirst({ where: { id: dateId, caseId } });
  if (!existing) throw new CaseAccessError(404, "Date not found");
  const reminder = input.reminderPreference === undefined
    ? undefined
    : typeof input.reminderPreference === "string" && REMINDERS.has(input.reminderPreference)
      ? input.reminderPreference
      : null;
  if (input.reminderPreference !== undefined && !reminder) {
    throw new CaseAccessError(422, "Invalid reminder preference.");
  }
  return prisma.caseImportantDate.update({
    where: { id: dateId },
    data: {
      title: input.title === undefined ? undefined : clean(input.title, 180) || existing.title,
      description: input.description === undefined ? undefined : clean(input.description),
      date: input.date === undefined ? undefined : parseDate(input.date),
      reminderPreference: reminder,
    },
  });
}

export async function deleteImportantDate(userId: string, caseId: string, dateId: string) {
  await requireOwnedCase(userId, caseId);
  const result = await prisma.caseImportantDate.deleteMany({ where: { id: dateId, caseId } });
  if (!result.count) throw new CaseAccessError(404, "Date not found");
}
