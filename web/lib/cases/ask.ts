import "server-only";

import { prisma } from "@/lib/db/client";
import { auditCaseAction } from "./audit";
import { loadAuthorizedCaseContext, type CaseContextExcerpt } from "./context";
import { CaseAccessError } from "./errors";
import { getOwnedCase } from "./store";

type RagChatPayload = {
  answer: string;
  has_context: boolean;
  no_relevant_context?: boolean;
  citations: unknown[];
  invalid_citations?: number[];
  retrieval: Record<string, unknown>;
  generation: Record<string, unknown>;
  total_latency_seconds?: number;
  conversation_id?: string;
  user_message?: unknown;
  assistant_message?: unknown;
};

async function ragRequest(path: string, body: unknown, method = "POST") {
  const baseUrl = process.env.RAG_API_URL?.replace(/\/$/, "");
  const secret = process.env.RAG_API_SECRET?.trim();
  if (!baseUrl || !secret) {
    throw new CaseAccessError(503, "Legal research is not configured.");
  }
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${secret}`,
    },
    body: method === "GET" ? undefined : JSON.stringify(body),
    cache: "no-store",
    signal: AbortSignal.timeout(90_000),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new CaseAccessError(
      response.status >= 500 ? 503 : response.status,
      typeof payload?.detail === "string" ? payload.detail : "Legal research request failed.",
    );
  }
  return payload;
}

/**
 * Ensure a client-supplied conversation belongs to this user and case.
 * Legacy rows with null userId are allowed only when caseId matches, then backfilled.
 */
export async function resolveOwnedCaseConversation(input: {
  userId: string;
  caseId: string;
  conversationId: string;
}): Promise<string> {
  const conversation = await prisma.conversation.findFirst({
    where: { id: input.conversationId },
    select: { id: true, userId: true, caseId: true },
  });

  if (!conversation || conversation.caseId !== input.caseId) {
    throw new CaseAccessError(404, "Conversation not found");
  }

  if (conversation.userId && conversation.userId !== input.userId) {
    throw new CaseAccessError(404, "Conversation not found");
  }

  if (!conversation.userId) {
    await prisma.conversation.update({
      where: { id: conversation.id },
      data: { userId: input.userId },
    });
  }

  return conversation.id;
}

export async function askAboutOwnedCase(input: {
  userId: string;
  caseId: string;
  message: string;
  conversationId?: string | null;
  language?: string | null;
}) {
  const item = await getOwnedCase(input.userId, input.caseId);
  const caseContext: CaseContextExcerpt[] = await loadAuthorizedCaseContext(
    input.userId,
    input.caseId,
    input.message,
  );
  auditCaseAction("case_context_accessed", {
    userId: input.userId,
    caseId: input.caseId,
  });

  let conversationId = input.conversationId?.trim() || "";
  if (conversationId) {
    conversationId = await resolveOwnedCaseConversation({
      userId: input.userId,
      caseId: item.id,
      conversationId,
    });
  } else {
    const created = await ragRequest("/api/conversations", {
      case_id: item.id,
      user_id: input.userId,
    });
    conversationId = created.id;
  }

  const payload = await ragRequest(
    `/api/conversations/${encodeURIComponent(conversationId)}/messages`,
    {
      message: input.message,
      language: input.language || "en",
      top_k: 8,
      min_similarity: 0.6,
      case_context: caseContext,
    },
  ) as RagChatPayload;

  return {
    ...payload,
    conversation_id: payload.conversation_id || conversationId,
    case_id: item.id,
    case_context_used: caseContext.length,
  };
}
