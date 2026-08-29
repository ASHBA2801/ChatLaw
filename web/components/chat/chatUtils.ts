import type { Citation, ChatResponse } from "@/lib/api/rag";
import { isCaseDocumentCitation } from "@/lib/api/rag";

export function formatRelativeDate(value: string): string {
  const time = new Date(value).getTime();
  if (Number.isNaN(time)) return "Unknown activity";
  const diff = Date.now() - time;
  if (diff < 60_000) return "Just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  if (diff < 604_800_000) return `${Math.floor(diff / 86_400_000)}d ago`;
  return new Date(value).toLocaleDateString();
}

export function composeCitationText(citation: Citation): string {
  if (isCaseDocumentCitation(citation)) {
    return ["Case Document", citation.document, citation.page !== null ? `Page ${citation.page}` : null]
      .filter(Boolean)
      .join(" | ");
  }
  return [
    citation.document,
    citation.section ? `Section ${citation.section}` : null,
    citation.subsection ? `Subsection ${citation.subsection}` : null,
    citation.clause ? `Clause ${citation.clause}` : null,
    citation.page !== null ? `Page ${citation.page}` : null,
  ]
    .filter(Boolean)
    .join(" | ");
}

export type CitationPanelState = {
  citation: ChatResponse["citations"][number];
};

const conversationBootPromises = new Map<string, Promise<void>>();

/** Dedupe conversation boot across React Strict Mode remounts. */
export function runConversationBoot(key: string, task: () => Promise<void>): Promise<void> {
  const existing = conversationBootPromises.get(key);
  if (existing) return existing;

  const promise = task().finally(() => {
    if (conversationBootPromises.get(key) === promise) {
      conversationBootPromises.delete(key);
    }
  });
  conversationBootPromises.set(key, promise);
  return promise;
}
