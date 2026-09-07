import { beforeEach, describe, expect, it, vi } from "vitest";
import { isCaseStatus } from "./status";

const prisma = vi.hoisted(() => ({
  case: {
    findMany: vi.fn(),
    findFirst: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    updateMany: vi.fn(),
  },
  caseTimelineEvent: { create: vi.fn() },
  $transaction: vi.fn(),
}));

vi.mock("@/lib/db/client", () => ({ prisma }));
vi.mock("./documents", () => ({
  publicCaseDocument: (document: { id: string }) => document,
}));

import { archiveOwnedCase, createOwnedCase, getOwnedCase, updateOwnedCase } from "./store";
import { CaseAccessError } from "./errors";

describe("case status validation", () => {
  it("accepts only supported statuses", () => {
    expect(isCaseStatus("ACTIVE")).toBe(true);
    expect(isCaseStatus("ARCHIVED")).toBe(true);
    expect(isCaseStatus("deleted")).toBe(false);
  });
});

describe("owned case store", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    prisma.$transaction.mockImplementation(async (fn: (tx: typeof prisma) => unknown) => fn(prisma));
    prisma.caseTimelineEvent.create.mockResolvedValue({});
  });

  it("creates a case for the session user", async () => {
    prisma.case.create.mockResolvedValue({ id: "case-1", userId: "user-a", title: "Deposit dispute" });
    const created = await createOwnedCase("user-a", { title: "Deposit dispute" });
    expect(created.title).toBe("Deposit dispute");
    expect(prisma.case.create).toHaveBeenCalledWith(expect.objectContaining({
      data: expect.objectContaining({ userId: "user-a", title: "Deposit dispute" }),
    }));
  });

  it("rejects missing titles", async () => {
    await expect(createOwnedCase("user-a", { title: "  " })).rejects.toMatchObject({ status: 422 });
  });

  it("hides another user's case", async () => {
    prisma.case.findFirst.mockResolvedValue(null);
    await expect(getOwnedCase("user-b", "case-1")).rejects.toBeInstanceOf(CaseAccessError);
  });

  it("updates only an owned case", async () => {
    prisma.case.findFirst.mockResolvedValue({ id: "case-1" });
    prisma.case.update.mockResolvedValue({ id: "case-1", status: "ON_HOLD" });
    await updateOwnedCase("user-a", "case-1", { status: "ON_HOLD" });
    expect(prisma.case.update).toHaveBeenCalled();
  });

  it("archives an owned case and rejects unknown ids", async () => {
    prisma.case.updateMany.mockResolvedValue({ count: 1 });
    await archiveOwnedCase("user-a", "case-1");
    prisma.case.updateMany.mockResolvedValue({ count: 0 });
    await expect(archiveOwnedCase("user-b", "case-1")).rejects.toMatchObject({ status: 404 });
  });
});
