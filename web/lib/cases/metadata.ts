const MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec";
const DATE_PATTERN = new RegExp(
  `\\b(?:\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}|\\d{1,2}\\s+(?:${MONTHS})\\s+\\d{4}|(?:${MONTHS})\\s+\\d{1,2},?\\s+\\d{4})\\b`,
  "gi",
);
const HEADING_PATTERN = /^(?:[A-Z][A-Z0-9 ,/()'&-]{8,}|Article\s+\d+|Clause\s+\d+|Section\s+\d+[A-Za-z]?)\s*$/gm;

function uniqueCapped(values: string[], limit: number): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const trimmed = value.replace(/\s+/g, " ").trim();
    if (!trimmed || seen.has(trimmed.toLowerCase())) continue;
    seen.add(trimmed.toLowerCase());
    result.push(trimmed.slice(0, 180));
    if (result.length >= limit) break;
  }
  return result;
}

export function detectDocumentSignals(text: string) {
  return {
    detected_dates: uniqueCapped(text.match(DATE_PATTERN) ?? [], 12),
    detected_headings: uniqueCapped(text.match(HEADING_PATTERN) ?? [], 16),
  };
}

export function formatExtractedPages(pages: Array<{ page: number; text: string }>): string {
  return pages
    .map((item) => `--- Page ${item.page} ---\n${item.text.trim()}`)
    .join("\n\n")
    .trim();
}

export function splitExtractedPages(text: string): Array<{ page: number; text: string }> {
  const chunks = text.split(/^--- Page (\d+) ---\s*/m);
  const pages: Array<{ page: number; text: string }> = [];
  for (let index = 1; index < chunks.length; index += 2) {
    const page = Number(chunks[index]);
    const body = (chunks[index + 1] || "").trim();
    if (Number.isInteger(page) && page > 0) {
      pages.push({ page, text: body });
    }
  }
  return pages;
}
