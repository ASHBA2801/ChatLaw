import "server-only";

export class RagDocumentError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = "RagDocumentError";
    this.status = status;
    this.payload = payload;
  }
}

async function ragRequest(path: string, body: unknown) {
  const baseUrl = process.env.RAG_API_URL?.replace(/\/$/, "");
  const secret = process.env.RAG_API_SECRET?.trim();
  if (!baseUrl || !secret) {
    throw new RagDocumentError("RAG service is not configured", 503);
  }
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${secret}`,
    },
    body: JSON.stringify(body),
    cache: "no-store",
    signal: AbortSignal.timeout(90_000),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new RagDocumentError(
      typeof payload?.detail === "string" ? payload.detail : "Document generation failed",
      response.status,
      payload,
    );
  }
  return payload;
}

export function generateDraft(input: {
  template_id: string;
  values: Record<string, unknown>;
  use_model?: boolean;
  language?: string;
}) {
  return ragRequest("/api/documents/generate", input);
}

export function regenerateSection(input: {
  template_id: string;
  values: Record<string, unknown>;
  section_id: string;
  use_model?: boolean;
  instruction?: string;
}) {
  return ragRequest("/api/documents/regenerate", input);
}

export function reviseDocument(input: {
  template_id: string;
  values: Record<string, unknown>;
  sections: unknown[];
  instruction: string;
  target_section_ids?: string[];
  use_model?: boolean;
}) {
  return ragRequest("/api/documents/revise", input);
}

export function selectionEdit(input: {
  selected_text: string;
  action: string;
  surrounding_section: Record<string, unknown>;
  document_title: string;
  jurisdiction: string;
  custom_instruction?: string;
  language?: string;
  use_model?: boolean;
}) {
  return ragRequest("/api/documents/selection-edit", input);
}
