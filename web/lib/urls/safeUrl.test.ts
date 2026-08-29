import { describe, expect, it } from "vitest";

import { isSafeExternalUrl } from "@/lib/urls/safeUrl";

describe("isSafeExternalUrl", () => {
  it("accepts http and https links", () => {
    expect(isSafeExternalUrl("https://indiankanoon.org/doc/257876/")).toBe(
      "https://indiankanoon.org/doc/257876/",
    );
    expect(isSafeExternalUrl("http://example.test/source")).toBe("http://example.test/source");
  });

  it("rejects unsafe or empty values", () => {
    expect(isSafeExternalUrl("javascript:alert(1)")).toBeNull();
    expect(isSafeExternalUrl("")).toBeNull();
    expect(isSafeExternalUrl(null)).toBeNull();
    expect(isSafeExternalUrl("#")).toBeNull();
  });
});
