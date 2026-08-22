import { Prisma } from "@/lib/generated/prisma/client";
import { prisma } from "@/lib/db/client";
import { CaseAccessError } from "./errors";
import { detectDocumentSignals, splitExtractedPages } from "./metadata";

export const CASE_CONTEXT_PAGE_LIMIT = 4;
export const CASE_CONTEXT_PAGE_CHARS = 1500;

export type CaseContextExcerpt = {
  document_id: string;
  file_name: string;
  page: number;
  text: string;
};

const STOPWORDS = new Set([
  "the", "and", "for", "that", "this", "with", "from", "have", "what", "does",
  "about", "which", "your", "their", "there", "were", "been", "will", "into",
]);

export function tokenizeQuery(query: string): string[] {
  const seen = new Set<string>();
  const tokens: string[] = [];
  for (const match of query.toLowerCase().match(/[a-z0-9]{3,}/g) ?? []) {
    if (STOPWORDS.has(match) || seen.has(match)) continue;
    seen.add(match);
    tokens.push(match);
  }
  return tokens;
}

export function scorePage(text: string, tokens: string[]): number {
  if (tokens.length === 0) return 0;
  const haystack = text.toLowerCase();
  return tokens.reduce((score, token) => score + (haystack.includes(token) ? 1 : 0), 0);
}

export function selectCaseExcerpts(
  documents: Array<{ id: string; fileName: string; extractedText: string | null }>,
  query: string,
  options?: { pageLimit?: number; pageChars?: number },
): CaseContextExcerpt[] {
  const pageLimit = options?.pageLimit ?? CASE_CONTEXT_PAGE_LIMIT;
  const pageChars = options?.pageChars ?? CASE_CONTEXT_PAGE_CHARS;
  const tokens = tokenizeQuery(query);
  const scored: Array<CaseContextExcerpt & { score: number }> = [];
  for (const document of documents) {
    if (!document.extractedText) continue;
    for (const page of splitExtractedPages(document.extractedText)) {
      const score = scorePage(page.text, tokens);
      if (score <= 0) continue;
      scored.push({
        document_id: document.id,
        file_name: document.fileName,
        page: page.page,
        text: page.text.slice(0, pageChars),
        score,
      });
    }
  }
  scored.sort((left, right) => right.score - left.score || left.page - right.page);
  const unique = new Map<string, CaseContextExcerpt>();
  for (const item of scored) {
    const key = `${item.document_id}:${item.page}`;
    if (unique.has(key)) continue;
    unique.set(key, {
      document_id: item.document_id,
      file_name: item.file_name,
      page: item.page,
      text: item.text,
    });
    if (unique.size >= pageLimit) break;
  }
  return [...unique.values()];
}

export async function loadAuthorizedCaseContext(userId: string, caseId: string, query: string) {
  const owned = await prisma.case.findFirst({
    where: { id: caseId, userId },
    select: {
      id: true,
      documents: {
        where: { deletedAt: null, extractedTextStatus: "READY", extractedText: { not: null } },
        select: { id: true, fileName: true, extractedText: true },
      },
    },
  });
  if (!owned) throw new CaseAccessError(404);
  return selectCaseExcerpts(owned.documents, query);
}

export function caseContextJson(excerpts: CaseContextExcerpt[]): Prisma.InputJsonValue {
  return excerpts as unknown as Prisma.InputJsonValue;
}

export function describeDetectedSignals(text: string) {
  return detectDocumentSignals(text);
}
