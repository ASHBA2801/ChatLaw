import { describe, expect, it } from "vitest";
import { getAuthConfiguration, safeCallbackUrl } from "./config";

describe("auth configuration", () => {
  it("requires a real secret before enabling Google", () => {
    const result = getAuthConfiguration({
      AUTH_SECRET: "replace-with-a-long-random-auth-secret-at-least-32-characters",
      AUTH_GOOGLE_ID: "client-id",
      AUTH_GOOGLE_SECRET: "client-secret",
    });
    expect(result.googleConfigured).toBe(false);
    expect(result.issues[0]).toContain("AUTH_SECRET");
  });

  it("enables Google only when all server credentials are present", () => {
    const result = getAuthConfiguration({
      AUTH_SECRET: "a".repeat(48),
      AUTH_GOOGLE_ID: "client-id",
      AUTH_GOOGLE_SECRET: "client-secret",
    });
    expect(result.googleConfigured).toBe(true);
    expect(result.issues).toEqual([]);
  });
});

describe("safe callback URLs", () => {
  it("accepts local paths and rejects external URLs", () => {
    expect(safeCallbackUrl("/cases/new")).toBe("/cases/new");
    expect(safeCallbackUrl("https://example.com")).toBe("/documents");
    expect(safeCallbackUrl("//example.com")).toBe("/documents");
  });
});