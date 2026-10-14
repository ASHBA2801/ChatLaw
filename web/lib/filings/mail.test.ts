import { describe, expect, it } from "vitest";

import { ATTACH_REMINDER, cleanAddresses, composeUrl, MAILTO_LIMIT } from "./mail";

const draft = {
  to: ["SP-CBE@tnpolice.gov.in", "not an email", "sp-cbe@tnpolice.gov.in"],
  cc: ["dvac@nic.in"],
  subject: "Complaint regarding online fraud",
  fullBody: "Respected Sir,\n\nPlease find my complaint below.\n\n1. On 3 October 2026 ...",
  coverNote: "Respected Sir,\n\nPlease find my complaint attached.",
};

describe("filing email hand-off", () => {
  it("cleans and de-duplicates recipient addresses", () => {
    expect(cleanAddresses(["a@b.gov.in; c@d.nic.in", "A@B.gov.in", "bad@", ""])).toEqual(["a@b.gov.in", "c@d.nic.in"]);
  });

  it("builds a Gmail compose link with recipients, cc, subject and the full text", () => {
    const { url, truncated } = composeUrl("gmail", draft);
    const parsed = new URL(url);
    expect(parsed.hostname).toBe("mail.google.com");
    expect(parsed.searchParams.get("view")).toBe("cm");
    expect(parsed.searchParams.get("to")).toBe("sp-cbe@tnpolice.gov.in");
    expect(parsed.searchParams.get("cc")).toBe("dvac@nic.in");
    expect(parsed.searchParams.get("su")).toBe(draft.subject);
    expect(parsed.searchParams.get("body")).toContain("On 3 October 2026");
    expect(truncated).toBe(false);
  });

  it("builds Outlook and mailto links", () => {
    expect(composeUrl("outlook", draft).url).toMatch(/^https:\/\/outlook\.office\.com\/mail\/deeplink\/compose\?/);
    const mailto = composeUrl("default", draft).url;
    expect(mailto.startsWith("mailto:sp-cbe%40tnpolice.gov.in?subject=")).toBe(true);
    expect(decodeURIComponent(mailto)).toContain("cc=dvac@nic.in");
  });

  it("switches to the cover note when the complaint is too long for a compose link", () => {
    const long = { ...draft, fullBody: "x".repeat(MAILTO_LIMIT + 10) };
    const result = composeUrl("default", long);
    expect(result.truncated).toBe(true);
    expect(decodeURIComponent(result.url)).toContain(ATTACH_REMINDER);
    expect(composeUrl("gmail", long).truncated).toBe(false);
  });
});
