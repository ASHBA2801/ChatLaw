import type { DocumentSection, GeneratedDocumentPayload } from "./types";

export function updateSectionBody(
  document: GeneratedDocumentPayload,
  sectionId: string,
  body: string,
): GeneratedDocumentPayload {
  return {
    ...document,
    sections: document.sections.map((section) => (section.id === sectionId ? { ...section, body } : section)),
  };
}

export function removeSection(document: GeneratedDocumentPayload, sectionId: string): GeneratedDocumentPayload {
  return {
    ...document,
    sections: document.sections.filter((section) => section.id !== sectionId),
  };
}

export function addSection(
  document: GeneratedDocumentPayload,
  section: DocumentSection,
  afterId?: string,
): GeneratedDocumentPayload {
  const sections = [...document.sections];
  const index = afterId ? sections.findIndex((item) => item.id === afterId) : sections.length - 1;
  const insertAt = index >= 0 ? index + 1 : sections.length;
  sections.splice(insertAt, 0, section);
  return { ...document, sections };
}

export function replaceSection(
  document: GeneratedDocumentPayload,
  next: DocumentSection,
): GeneratedDocumentPayload {
  return {
    ...document,
    sections: document.sections.map((section) => (section.id === next.id ? { ...section, ...next } : section)),
  };
}

export function createCustomSection(title: string): DocumentSection {
  const id = `custom_${Date.now().toString(36)}`;
  return {
    id,
    title: title.trim() || "Additional clause",
    body: "[CLAUSE TEXT REQUIRED]",
    required: false,
    provision_class: "user_specific",
    review_required: true,
    citation_ids: [],
    legal_basis: [],
    number: null,
  };
}
