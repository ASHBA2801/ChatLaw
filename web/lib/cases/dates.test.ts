import { beforeEach, describe, expect, it, vi } from "vitest";

const prisma = vi.hoisted(() => ({
  case: { findFirst: vi.fn() },
  caseImportantDate: {
    findMany: vi.fn(),
    findFirst: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    deleteMany: vi.fn(),
  },
  caseTimelineEvent: { create: vi.fn() },
  $transaction: vi.fn(),
}));

vi.mock("@/lib/db/client", () => ({ prisma }));

import { createImportantDate, deleteImportantDate } from "./dates";
import { addTimelineNote } from "./timeline";

describe("important dates and timeline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    prisma.$transaction.mockImplementation(async (fn: (tx: typeof prisma) => unknown) => fn(prisma));
    prisma.case.findFirst.mockResolvedValue({ id: "case-1" });
    prisma.caseTimelineEvent.create.mockResolvedValue({});
  });

  it("creates a date on an owned case", async () => {
    prisma.caseImportantDate.create.mockResolvedValue({
      id: "date-1",
      title: "Response deadline",
      date: new Date("2026-08-21"),
    });
    const created = await createImportantDate("user-a", "case-1", {
      title: "Response deadline",
      date: "2026-08-21",
      reminderPreference: "day_before",
    });
    expect(created.title).toBe("Response deadline");
  });

  it("rejects dates on another user's case", async () => {
    prisma.case.findFirst.mockResolvedValue(null);
    await expect(createImportantDate("user-b", "case-1", { title: "Hearing", date: "2026-08-21" }))
      .rejects.toMatchObject({ status: 404 });
  });

  it("deletes only dates on the owned case", async () => {
    prisma.caseImportantDate.deleteMany.mockResolvedValue({ count: 0 });
    await expect(deleteImportantDate("user-a", "case-1", "missing")).rejects.toMatchObject({ status: 404 });
  });

  it("adds a user timeline note", async () => {
    prisma.caseTimelineEvent.create.mockResolvedValue({ id: "ev-1", type: "USER_NOTE", title: "Called landlord" });
    const event = await addTimelineNote("user-a", "case-1", { title: "Called landlord" });
    expect(event.type).toBe("USER_NOTE");
  });
});
