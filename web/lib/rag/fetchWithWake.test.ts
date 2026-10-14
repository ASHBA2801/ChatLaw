import { describe, expect, it, vi } from "vitest";

import { fetchRagWithWake, isRetryableConnectionError } from "./fetchWithWake";

function connectionError(code: string) {
  return Object.assign(new TypeError("fetch failed"), { cause: Object.assign(new Error(code), { code }) });
}

const noSleep = () => Promise.resolve();

describe("fetchRagWithWake", () => {
  it("retries a refused connection until the engine wakes", async () => {
    const ok = new Response("{}", { status: 200 });
    const fetchImpl = vi
      .fn()
      .mockRejectedValueOnce(connectionError("ECONNREFUSED"))
      .mockRejectedValueOnce(connectionError("ECONNREFUSED"))
      .mockResolvedValueOnce(ok);
    const response = await fetchRagWithWake("http://rag/api/chat", { method: "POST", body: "{}" }, { sleep: noSleep, fetchImpl });
    expect(response).toBe(ok);
    expect(fetchImpl).toHaveBeenCalledTimes(3);
  });

  it("does not resend a POST whose connection dropped mid-request", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(connectionError("ECONNRESET"));
    await expect(
      fetchRagWithWake("http://rag/api/chat", { method: "POST" }, { sleep: noSleep, fetchImpl }),
    ).rejects.toThrow("fetch failed");
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it("gives up after the wake window", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(connectionError("ECONNREFUSED"));
    await expect(
      fetchRagWithWake("http://rag/x", {}, { sleep: noSleep, fetchImpl, wakeTimeoutMs: 0 }),
    ).rejects.toThrow();
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it("never retries timeouts or unrelated errors", () => {
    expect(isRetryableConnectionError(new DOMException("t", "TimeoutError"))).toBe(false);
    expect(isRetryableConnectionError(new Error("boom"))).toBe(false);
    expect(isRetryableConnectionError(connectionError("ECONNRESET"), "GET")).toBe(true);
  });
});
