import { describe, expect, it } from "vitest";
import { detectCaseIntent } from "./intent";

describe("detectCaseIntent", () => {
  it("detects normal legal questions", () => {
    expect(detectCaseIntent("What is the punishment for theft?").requiresCases).toBe(false);
    expect(detectCaseIntent("Explain Section 303 of BNS.").requiresCases).toBe(false);
  });

  it("detects similar case requests", () => {
    expect(detectCaseIntent("Show me similar cases.").requiresCases).toBe(true);
    expect(detectCaseIntent("Find cases where consumers received refunds.").requiresCases).toBe(true);
  });

  it("detects case law research", () => {
    expect(detectCaseIntent("Research case law on Section 303.").intent).toBe("CASE_LAW_RESEARCH");
    expect(detectCaseIntent("Give me Supreme Court judgments about this.").requiresCases).toBe(true);
  });

  it("detects personal case queries without auto-showing cases unless in workspace", () => {
    const res = detectCaseIntent("I bought a defective phone and the seller refused a refund.");
    expect(res.intent).toBe("PERSONAL_CASE_QUERY");
    expect(res.requiresCases).toBe(false);

    const workspaceRes = detectCaseIntent("I bought a defective phone and the seller refused a refund.", true);
    expect(workspaceRes.requiresCases).toBe(true);
  });
});
