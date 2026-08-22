import type { DocumentSection, GeneratedDocumentPayload } from "./types";

export function sanitizePlainText(value: string): string {
  return value.replace(/\u0000/g, "").replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "").replace(/[<>]/g, (char) => (char === "<" ? "‹" : "›"));
}

export function sanitizeSection(section: DocumentSection): DocumentSection {
  return {
    ...section,
    title: sanitizePlainText(section.title),
    body: sanitizePlainText(section.body),
  };
}

export function sanitizeDocument(payload: GeneratedDocumentPayload): GeneratedDocumentPayload {
  return {
    ...payload,
    title: sanitizePlainText(payload.title),
    document_type: sanitizePlainText(payload.document_type),
    jurisdiction_country: sanitizePlainText(payload.jurisdiction_country),
    jurisdiction_region: sanitizePlainText(payload.jurisdiction_region),
    sections: payload.sections.map(sanitizeSection),
    warnings: payload.warnings.map((warning) => ({ ...warning, message: sanitizePlainText(warning.message) })),
    signatures: payload.signatures.map((block) => ({
      ...block,
      role: sanitizePlainText(block.role),
      name: sanitizePlainText(block.name),
      lines: block.lines.map(sanitizePlainText),
    })),
  };
}
