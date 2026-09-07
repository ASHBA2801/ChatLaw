import type { GeneratedDocumentPayload } from "./types";

export function formatDocumentText(payload: GeneratedDocumentPayload): string {
  const lines: string[] = [];
  lines.push(payload.title);
  lines.push("");
  if (payload.jurisdiction_region) {
    lines.push(`Jurisdiction: India — ${payload.jurisdiction_region}`);
    lines.push("");
  }
  for (const section of payload.sections) {
    const heading = section.number ? `${section.number}. ${section.title}` : section.title;
    lines.push(heading.toUpperCase());
    lines.push("");
    lines.push(section.body);
    if (section.legal_basis?.length) {
      lines.push("");
      lines.push("Legal basis:");
      for (const basis of section.legal_basis) {
        lines.push(`- ${basis.label}`);
      }
    }
    if (section.include_signature) {
      lines.push("");
      for (const block of payload.signatures) {
        lines.push("");
        for (const line of block.lines) lines.push(line);
      }
    }
    lines.push("");
  }
  if (payload.disclaimer) {
    lines.push("Disclaimer");
    lines.push(payload.disclaimer);
  }
  return lines.join("\n").trim() + "\n";
}
