import "server-only";

import { CaseAccessError } from "@/lib/cases/errors";
import { fetchRagWithWake } from "@/lib/rag/fetchWithWake";

/** Calls to the rag-engine filing agent (/api/complaints/*). */
export async function filingRequest<T>(path: string, body?: unknown, timeoutMs = 120_000): Promise<T> {
  const baseUrl = process.env.RAG_API_URL?.replace(/\/$/, "");
  const secret = process.env.RAG_API_SECRET?.trim();
  if (!baseUrl || !secret) {
    throw new CaseAccessError(503, "The filing assistant is not configured.");
  }
  const response = await fetchRagWithWake(`${baseUrl}/api/complaints/${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${secret}`,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
    signal: AbortSignal.timeout(timeoutMs),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : null;
    throw new CaseAccessError(
      response.status >= 500 ? 503 : response.status === 404 ? 404 : 422,
      detail || "The filing assistant could not complete this request.",
    );
  }
  return payload as T;
}
