import type { Citation, ChatResponse, ConversationSummary } from "@/lib/api/rag";
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

const LINE_NUMBER = /^\d{1,4}\.?$/;

function joinCitationLines(lines: string[]): string {
  let result = "";
  for (const line of lines) {
    if (!result) {
      result = line;
    } else if (result.endsWith("-")) {
      result = result.slice(0, -1) + line;
    } else {
      result += ` ${line}`;
    }
  }
  return result.replace(/\s+/g, " ").trim();
}

/** Turn PDF-style line breaks and margin numbers into readable paragraphs. */
export function formatCitationEvidence(raw: string): string[] {
  if (!raw.trim()) return [];

  const normalized = raw.replace(/\r\n/g, "\n").trim();
  const blocks = normalized.split(/\n\s*\n/);

  return blocks
    .map((block) => {
      const lines = block
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line && !LINE_NUMBER.test(line));
      return joinCitationLines(lines);
    })
    .filter(Boolean);
}

export function composeCitationText(citation: Citation): string {
  if (isCaseDocumentCitation(citation)) {
    return ["Case Document", citation.document, citation.page !== null ? `Page ${citation.page}` : null]
      .filter(Boolean)
      .join(" | ");
  }
  const jurisdiction =
    citation.jurisdiction_level === "CENTRAL"
      ? "Central"
      : citation.jurisdiction_level ?? null;
  return [
    citation.document,
    citation.section ? `Section ${citation.section}` : null,
    citation.subsection ? `Subsection ${citation.subsection}` : null,
    citation.clause ? `Clause ${citation.clause}` : null,
    citation.domain ? citation.domain.replace(/_/g, " ") : null,
    jurisdiction,
    citation.page !== null ? `Page ${citation.page}` : null,
  ]
    .filter(Boolean)
    .join(" | ");
}

export type CitationPanelState = {
  citation: ChatResponse["citations"][number];
};

export function groupConversationsByDate(items: ConversationSummary[]) {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday.getTime() - 86_400_000);
  const startOfWeek = new Date(startOfToday.getTime() - 7 * 86_400_000);

  const buckets: { label: string; items: ConversationSummary[] }[] = [
    { label: "Today", items: [] },
    { label: "Yesterday", items: [] },
    { label: "Past 7 days", items: [] },
    { label: "Earlier", items: [] },
  ];

  for (const item of items) {
    const updated = new Date(item.updated_at);
    if (updated >= startOfToday) buckets[0].items.push(item);
    else if (updated >= startOfYesterday) buckets[1].items.push(item);
    else if (updated >= startOfWeek) buckets[2].items.push(item);
    else buckets[3].items.push(item);
  }

  return buckets.filter((bucket) => bucket.items.length > 0);
}

export function citationTypeLabel(citation: Citation): string {
  if (isCaseDocumentCitation(citation)) return "Case doc";
  const type = citation.source?.source_type;
  if (type === "statute" || type === "act") return "Act";
  if (type === "judgment" || type === "case") return "Case";
  return citation.section ? "Section" : "Source";
}

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
