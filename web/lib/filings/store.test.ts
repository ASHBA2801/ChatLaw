import { beforeEach, describe, expect, it, vi } from "vitest";

const prisma = vi.hoisted(() => ({
  case: { findFirst: vi.fn(), update: vi.fn() },
  caseFiling: { create: vi.fn(), findFirst: vi.fn(), update: vi.fn(), findMany: vi.fn(), deleteMany: vi.fn() },
  caseTimelineEvent: { create: vi.fn() },
  $transaction: vi.fn(),
}));
const filingRequest = vi.hoisted(() => vi.fn());

vi.mock("@/lib/db/client", () => ({ prisma }));
vi.mock("./rag", () => ({ filingRequest }));

import { CaseAccessError } from "@/lib/cases/errors";
import { buildCaseFacts, draftCaseFiling, getOwnedFiling, updateOwnedFiling } from "./store";

const baseCase = {
  id: "case-1",
  userId: "user-a",
  title: "UPI fraud",
  description: "On 3 October 2026 a caller took Rs 45,000 from my account through UPI.",
  category: null,
  locality: "Peelamedu", city: "Coimbatore", district: "Coimbatore", state: "Tamil Nadu", pincode: "641004",
  latitude: 11.02, longitude: 76.99,
  filingProfile: { complainant: { name: "R. Kumar" }, analysis: { summary: "UPI fraud", provisions: [] } },
  timeline: [{ occurredAt: new Date("2026-10-05"), title: "Went to police", description: "They refused to register" }],
  importantDates: [],
  documents: [
    { fileName: "statement.pdf", metadata: { summary: "Bank statement showing debit of Rs 45,000" }, extractedText: "raw" },
    { fileName: "sms.pdf", metadata: {}, extractedText: "OTP   message\n\nfrom  bank" },
  ],
};

const draft = {
  forum: "authority",
  title: "Complaint regarding online fraud",
  subject: "Online fraud of Rs 45,000",
  addressee: "To\nThe SHO",
  text: "To\nThe SHO\n\nSubject: Online fraud",
  sections: [],
  citations: [],
  warnings: [],
  placeholders: [],
  enclosures: ["Bank statement"],
  filing: { channel: "email" },
  email: { cover_note: "Sir, please find my complaint." },
  model_used: true,
  template: { kind: "police_station" },
  disclaimer: "Informational only",
};

describe("filing facts", () => {
  it("combines the description, notes and document summaries", () => {
    const facts = buildCaseFacts(baseCase as never);
    expect(facts).toContain("Rs 45,000 from my account");
    expect(facts).toContain("2026-10-05: Went to police — They refused to register");
    expect(facts).toContain('From the document "statement.pdf":\nBank statement showing debit');
    // Unsummarised documents fall back to their extracted text, whitespace collapsed.
    expect(facts).toContain("OTP message from bank");
  });
});

describe("filing store", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    prisma.$transaction.mockImplementation(async (fn: (tx: typeof prisma) => unknown) => fn(prisma));
    prisma.caseTimelineEvent.create.mockResolvedValue({});
  });

  it("drafts with the saved analysis and complainant, and keeps only valid recipient emails", async () => {
    prisma.case.findFirst.mockResolvedValue(baseCase);
    filingRequest.mockResolvedValue(draft);
    prisma.caseFiling.create.mockImplementation(async ({ data }: { data: unknown }) => ({ id: "filing-1", ...(data as object) }));

    const filing = await draftCaseFiling("user-a", "case-1", {
      kind: "police_station",
      recipient: { name: "Peelamedu Police Station", email: "ps@tnpolice.gov.in" },
      to: ["PS@tnpolice.gov.in", "not-an-email"],
    });

    expect(prisma.case.findFirst).toHaveBeenCalledWith(expect.objectContaining({ where: { id: "case-1", userId: "user-a" } }));
    const [path, body] = filingRequest.mock.calls[0];
    expect(path).toBe("draft");
    expect(body.analysis.summary).toBe("UPI fraud");
    expect(body.complainant.name).toBe("R. Kumar");
    expect(body.location.district).toBe("Coimbatore");
    expect(filing.recipients).toEqual({ to: ["ps@tnpolice.gov.in"], recipient: expect.objectContaining({ name: "Peelamedu Police Station" }) });
    expect(prisma.caseTimelineEvent.create).toHaveBeenCalledWith({
      data: expect.objectContaining({ caseId: "case-1", type: "FILING_DRAFTED", title: "Drafted: Local police station" }),
    });
  });

  it("refuses to draft for another user's case or an unknown office", async () => {
    prisma.case.findFirst.mockResolvedValue(null);
    await expect(draftCaseFiling("user-b", "case-1", { kind: "police_station" })).rejects.toBeInstanceOf(CaseAccessError);
    await expect(draftCaseFiling("user-a", "case-1", { kind: "astrologer" })).rejects.toMatchObject({ status: 422 });
    expect(filingRequest).not.toHaveBeenCalled();
  });

  it("scopes filing reads to the owner", async () => {
    prisma.caseFiling.findFirst.mockResolvedValue(null);
    await expect(getOwnedFiling("user-b", "case-1", "filing-1")).rejects.toMatchObject({ status: 404 });
    expect(prisma.caseFiling.findFirst).toHaveBeenCalledWith({ where: { id: "filing-1", caseId: "case-1", userId: "user-b" } });
  });

  it("records a timeline event when a filing is marked sent", async () => {
    prisma.caseFiling.findFirst.mockResolvedValue({ id: "filing-1", kind: "collector", status: "DRAFT", subject: "Land", recipients: { to: [] }, sentAt: null });
    prisma.caseFiling.update.mockResolvedValue({ id: "filing-1", status: "SENT" });
    await updateOwnedFiling("user-a", "case-1", "filing-1", { status: "SENT", to: ["collr@nic.in"] });
    const update = prisma.caseFiling.update.mock.calls[0][0];
    expect(update.data.status).toBe("SENT");
    expect(update.data.sentAt).toBeInstanceOf(Date);
    expect(update.data.recipients).toEqual({ to: ["collr@nic.in"] });
    expect(prisma.caseTimelineEvent.create).toHaveBeenCalledWith({
      data: expect.objectContaining({ type: "FILING_SENT", title: "Sent: District Collector" }),
    });
  });
});

describe("filing profile", () => {
  it("accepts geocoded locations with missing parts", async () => {
    const { profileSchema } = await import("./store");
    const parsed = profileSchema.safeParse({
      complainant: { name: "R. Kumar", email: "" },
      location: { locality: "Peelamedu", city: null, district: "Coimbatore", state: "Tamil Nadu", pincode: null, latitude: 11.02, longitude: 76.99 },
    });
    expect(parsed.success).toBe(true);
    expect(parsed.data?.location?.city).toBeUndefined();
    expect(parsed.data?.complainant?.email).toBeUndefined();
  });
});
