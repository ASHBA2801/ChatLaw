import type { Citation } from "@/lib/api/rag";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * The RAG engine expands each "[n]" marker into "[n] <Act> — Section x — Page y"
 * so plain-text clients still see the source. The answer card already renders
 * "[n]" as a tappable chip that opens that source, so the spelled-out label is
 * repeated noise — on a phone it can double the length of an answer.
 */
export function stripRenderedCitationLabels(answer: string, citations: Citation[]): string {
  let text = answer;
  for (const citation of citations) {
    if (!citation.document) continue;
    const title = escapeRegExp(citation.document);
    const label = new RegExp(
      String.raw`\[${citation.id}\]\s+(?:Case Document\s+—\s+)?${title}(?:\s+—\s+(?:Section|Page|Subsection)\s+[^\s—\[\]]+?(?=\s|[.,;:](?:\s|$)|$))*`,
      "g",
    );
    text = text.replace(label, `[${citation.id}]`);
  }
  return text;
}
