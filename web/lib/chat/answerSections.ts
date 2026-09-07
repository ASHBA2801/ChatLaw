export type AnswerSection = {
  id: string;
  title: string;
  body: string;
};

const SECTION_ALIASES: Array<{ id: string; match: RegExp }> = [
  { id: "short", match: /^short\s+answer$/i },
  { id: "means", match: /^what\s+this\s+means$/i },
  { id: "applies", match: /^how\s+this\s+applies$/i },
  { id: "points", match: /^important\s+points$/i },
  { id: "next", match: /^what\s+you\s+may\s+consider\s+next$/i },
  { id: "law", match: /^relevant\s+law$/i },
  { id: "simple", match: /^in\s+simple\s+terms$/i },
  { id: "answer", match: /^answer$/i },
  { id: "provisions", match: /^relevant\s+provision/i },
  { id: "limitations", match: /^limitations?$/i },
];

export function parseLegalAnswerSections(markdown: string): AnswerSection[] {
  const text = markdown.trim();
  if (!text) return [];

  const headingPattern = /^(#{1,3})\s+(.+)$/gm;
  const matches = [...text.matchAll(headingPattern)];
  if (matches.length === 0) {
    return [{ id: "body", title: "Answer", body: text }];
  }

  const sections: AnswerSection[] = [];
  for (let index = 0; index < matches.length; index += 1) {
    const match = matches[index];
    const start = (match.index ?? 0) + match[0].length;
    const end = index + 1 < matches.length ? (matches[index + 1].index ?? text.length) : text.length;
    const title = match[2].trim();
    const body = text.slice(start, end).trim();
    const alias = SECTION_ALIASES.find((item) => item.match.test(title));
    sections.push({
      id: alias?.id ?? `section-${index}`,
      title,
      body,
    });
  }
  return sections.filter((section) => section.body.length > 0);
}

export function hasSimpleTermsSection(sections: AnswerSection[]): boolean {
  return sections.some((section) => section.id === "simple");
}

export function domainToDocumentTemplate(domain: string | null | undefined): string | null {
  switch (domain) {
    case "tenancy":
      return "rent_lease";
    case "employment":
      return "service_agreement";
    case "contract":
      return "nda";
    case "consumer":
      return "consumer_complaint";
    case "criminal":
      return "complaint";
    case "family":
      return "affidavit";
    default:
      return null;
  }
}
