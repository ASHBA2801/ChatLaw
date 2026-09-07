import "server-only";

export type ExtractedPdfPage = { page: number; text: string };

export type ExtractedPdf = {
  page_count: number;
  pages: ExtractedPdfPage[];
  metadata: Record<string, string>;
};

export class ExtractionError extends Error {
  constructor(
    message: string,
    public readonly status = 503,
  ) {
    super(message);
    this.name = "ExtractionError";
  }
}

export async function extractPdfBytes(bytes: Buffer): Promise<ExtractedPdf> {
  const baseUrl = process.env.RAG_API_URL?.replace(/\/$/, "");
  const secret = process.env.RAG_API_SECRET?.trim();
  if (!baseUrl || !secret) {
    throw new ExtractionError("Document extraction is not configured", 503);
  }
  const response = await fetch(`${baseUrl}/api/extract/pdf`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${secret}`,
      "Content-Type": "application/pdf",
    },
    body: new Uint8Array(bytes),
    cache: "no-store",
    signal: AbortSignal.timeout(90_000),
  });
  const payload = (await response.json().catch(() => null)) as ExtractedPdf | { detail?: string } | null;
  if (!response.ok) {
    const detail = payload && "detail" in payload ? payload.detail : null;
    throw new ExtractionError(
      typeof detail === "string" ? detail : "The PDF text could not be extracted",
      response.status === 422 ? 422 : 503,
    );
  }
  if (!payload || !("pages" in payload) || !Array.isArray(payload.pages)) {
    throw new ExtractionError("Extraction returned a malformed response", 503);
  }
  return payload;
}
