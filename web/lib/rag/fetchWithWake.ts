import "server-only";

/**
 * fetch() for calls to the RAG engine that survives the engine waking from sleep.
 *
 * On Railway the rag-engine service sleeps when idle. The first request after a
 * nap is refused while the container starts (a few seconds), which surfaced in
 * the app as "The legal research service is unavailable". Connection-level
 * failures mean the request never reached the engine, so it is safe to retry
 * them, POSTs included, until the engine is up.
 */

// The request was never delivered: safe to resend for any method.
const NOT_CONNECTED = new Set([
  "ECONNREFUSED",
  "ENOTFOUND",
  "EAI_AGAIN",
  "EHOSTUNREACH",
  "ENETUNREACH",
  "UND_ERR_CONNECT_TIMEOUT",
]);
// The connection dropped; the request may have been processed, so only resend reads.
const DROPPED = new Set(["ECONNRESET", "UND_ERR_SOCKET", "EPIPE"]);

const DEFAULT_WAKE_TIMEOUT_MS = 30_000;
const FIRST_DELAY_MS = 400;
const MAX_DELAY_MS = 4_000;

function errorCode(error: unknown): string | undefined {
  let current: unknown = error;
  for (let depth = 0; current && depth < 4; depth += 1) {
    const code = (current as { code?: unknown }).code;
    if (typeof code === "string") return code;
    current = (current as { cause?: unknown }).cause;
  }
  return undefined;
}

export function isRetryableConnectionError(error: unknown, method = "GET"): boolean {
  if (error instanceof DOMException && (error.name === "AbortError" || error.name === "TimeoutError")) return false;
  const code = errorCode(error);
  if (!code) return false;
  if (NOT_CONNECTED.has(code)) return true;
  return DROPPED.has(code) && ["GET", "HEAD"].includes(method.toUpperCase());
}

export interface WakeOptions {
  wakeTimeoutMs?: number;
  sleep?: (ms: number) => Promise<void>;
  fetchImpl?: typeof fetch;
}

const defaultSleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export async function fetchRagWithWake(
  input: string | URL,
  init: RequestInit = {},
  { wakeTimeoutMs = DEFAULT_WAKE_TIMEOUT_MS, sleep = defaultSleep, fetchImpl = fetch }: WakeOptions = {},
): Promise<Response> {
  const started = Date.now();
  let delay = FIRST_DELAY_MS;
  for (;;) {
    try {
      return await fetchImpl(input, init);
    } catch (error) {
      const elapsed = Date.now() - started;
      if (
        init.signal?.aborted ||
        !isRetryableConnectionError(error, init.method) ||
        elapsed + delay > wakeTimeoutMs
      ) {
        throw error;
      }
      await sleep(delay);
      delay = Math.min(delay * 2, MAX_DELAY_MS);
    }
  }
}
