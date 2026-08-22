import { beforeEach, describe, expect, it, vi } from "vitest";

const prisma = vi.hoisted(() => ({
  conversation: {
    findFirst: vi.fn(),
    update: vi.fn(),
  },
  case: {
    findFirst: vi.fn(),
  },
}));

vi.mock("@/lib/db/client", () => ({ prisma }));

import { CaseAccessError } from "./errors";
import { resolveOwnedCaseConversation } from "./ask";

describe("resolveOwnedCaseConversation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("allows a conversation owned by the user for the same case", async () => {
    prisma.conversation.findFirst.mockResolvedValue({
      id: "conv-1",
      userId: "user-a",
      caseId: "case-1",
    });

    await expect(
      resolveOwnedCaseConversation({
        userId: "user-a",
        caseId: "case-1",
        conversationId: "conv-1",
      }),
    ).resolves.toBe("conv-1");
    expect(prisma.conversation.update).not.toHaveBeenCalled();
  });

  it("rejects a conversation tied to a different case", async () => {
    prisma.conversation.findFirst.mockResolvedValue({
      id: "conv-1",
      userId: "user-a",
      caseId: "case-other",
    });

    await expect(
      resolveOwnedCaseConversation({
        userId: "user-a",
        caseId: "case-1",
        conversationId: "conv-1",
      }),
    ).rejects.toMatchObject({ status: 404 });
  });

  it("rejects a conversation owned by another user", async () => {
    prisma.conversation.findFirst.mockResolvedValue({
      id: "conv-1",
      userId: "user-b",
      caseId: "case-1",
    });

    await expect(
      resolveOwnedCaseConversation({
        userId: "user-a",
        caseId: "case-1",
        conversationId: "conv-1",
      }),
    ).rejects.toBeInstanceOf(CaseAccessError);
  });

  it("rejects unknown conversation ids", async () => {
    prisma.conversation.findFirst.mockResolvedValue(null);

    await expect(
      resolveOwnedCaseConversation({
        userId: "user-a",
        caseId: "case-1",
        conversationId: "missing",
      }),
    ).rejects.toMatchObject({ status: 404 });
  });

  it("backfills userId for legacy case-scoped conversations", async () => {
    prisma.conversation.findFirst.mockResolvedValue({
      id: "conv-legacy",
      userId: null,
      caseId: "case-1",
    });
    prisma.conversation.update.mockResolvedValue({ id: "conv-legacy" });

    await expect(
      resolveOwnedCaseConversation({
        userId: "user-a",
        caseId: "case-1",
        conversationId: "conv-legacy",
      }),
    ).resolves.toBe("conv-legacy");

    expect(prisma.conversation.update).toHaveBeenCalledWith({
      where: { id: "conv-legacy" },
      data: { userId: "user-a" },
    });
  });
});
