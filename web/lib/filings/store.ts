import "server-only";

import { createHash } from "node:crypto";
import { z } from "zod";

import { prisma } from "@/lib/db/client";
import { Prisma } from "@/lib/generated/prisma/client";
import { auditCaseAction } from "@/lib/cases/audit";
import { CaseAccessError } from "@/lib/cases/errors";
import { cleanAddresses } from "./mail";
import { filingRequest } from "./rag";
import {
  FILING_KINDS,
  FILING_STATUSES,
  kindLabel,
  type AuthoritiesResponse,
  type DraftResult,
  type FilingAnalysis,
  type FilingLocation,
  type FilingProfile,
} from "./types";

const MAX_FACTS = 24_000;
const DOC_CHARS = 3_000;

const optionalText = (max: number) => z.string().trim().max(max).nullish().transform((v) => v || undefined);

export const complainantSchema = z.object({
  name: optionalText(200),
  relation: optionalText(20),
  relation_name: optionalText(200),
  age: optionalText(10),
  occupation: optionalText(120),
  address: optionalText(600),
  phone: optionalText(40),
  email: optionalText(200),
  place: optionalText(120),
});

export const profileSchema = z.object({
  complainant: complainantSchema.optional(),
  location: z.object({
    locality: optionalText(160),
    city: optionalText(120),
    district: optionalText(160),
    state: optionalText(120),
    pincode: optionalText(12),
    latitude: z.number().finite().min(-90).max(90).nullable().optional(),
    longitude: z.number().finite().min(-180).max(180).nullable().optional(),
  }).optional(),
  language: z.string().trim().max(8).optional(),
});

export const draftSchema = z.object({
  kind: z.enum(FILING_KINDS as [string, ...string[]]),
  recipient: z.object({
    name: z.string().trim().min(1).max(300),
    designation: z.string().trim().max(300).nullable().optional(),
    address: z.string().trim().max(600).nullable().optional(),
    email: z.string().trim().max(200).nullable().optional(),
    phone: z.string().trim().max(120).nullable().optional(),
    source: z.string().trim().max(40).nullable().optional(),
    source_url: z.string().trim().max(1000).nullable().optional(),
  }).nullable().optional(),
  to: z.array(z.string().max(200)).max(10).optional(),
  cc: z.array(z.string().max(200)).max(10).optional(),
  instructions: z.string().trim().max(2000).optional(),
  language: z.string().trim().max(8).optional(),
});

export const updateSchema = z.object({
  title: z.string().trim().min(1).max(300).optional(),
  subject: z.string().trim().max(600).optional(),
  body: z.string().max(60_000).optional(),
  emailBody: z.string().max(60_000).optional(),
  to: z.array(z.string().max(200)).max(10).optional(),
  cc: z.array(z.string().max(200)).max(10).optional(),
  status: z.enum(FILING_STATUSES).optional(),
});

function asJson(value: unknown): Prisma.InputJsonValue {
  return JSON.parse(JSON.stringify(value ?? null)) as Prisma.InputJsonValue;
}

async function ownedCase(userId: string, caseId: string) {
  const item = await prisma.case.findFirst({
    where: { id: caseId, userId },
    include: {
      documents: { where: { deletedAt: null }, orderBy: { createdAt: "asc" } },
      timeline: { where: { type: "USER_NOTE" }, orderBy: { occurredAt: "asc" } },
      importantDates: { orderBy: { date: "asc" } },
    },
  });
  if (!item) throw new CaseAccessError(404);
  return item;
}

type OwnedCase = Awaited<ReturnType<typeof ownedCase>>;

function documentSummary(metadata: unknown): string | null {
  if (!metadata || typeof metadata !== "object") return null;
  const summary = (metadata as Record<string, unknown>).summary;
  return typeof summary === "string" && summary.trim() ? summary.trim() : null;
}

/** Everything the person has told us about the matter, as plain text for the agent. */
export function buildCaseFacts(item: Pick<OwnedCase, "title" | "description" | "category" | "timeline" | "importantDates" | "documents">): string {
  const parts: string[] = [];
  if (item.description?.trim()) parts.push(item.description.trim());
  const notes = item.timeline
    .map((event) => `- ${event.occurredAt.toISOString().slice(0, 10)}: ${event.title}${event.description ? ` — ${event.description}` : ""}`);
  if (notes.length) parts.push(`Notes:\n${notes.join("\n")}`);
  const dates = item.importantDates
    .map((d) => `- ${d.date.toISOString().slice(0, 10)}: ${d.title}${d.description ? ` — ${d.description}` : ""}`);
  if (dates.length) parts.push(`Important dates:\n${dates.join("\n")}`);
  for (const document of item.documents) {
    const summary = documentSummary(document.metadata);
    const text = summary || document.extractedText?.replace(/\s+/g, " ").trim().slice(0, DOC_CHARS);
    if (text) parts.push(`From the document "${document.fileName}":\n${text}`);
  }
  return parts.join("\n\n").slice(0, MAX_FACTS);
}

function hashFacts(facts: string) {
  return createHash("sha256").update(facts).digest("hex").slice(0, 32);
}

function readProfile(value: unknown): FilingProfile {
  return value && typeof value === "object" ? (value as FilingProfile) : {};
}

export function caseLocation(item: {
  locality: string | null; city: string | null; district: string | null; state: string | null;
  pincode: string | null; latitude: number | null; longitude: number | null;
}): FilingLocation {
  return {
    locality: item.locality, city: item.city, district: item.district, state: item.state,
    pincode: item.pincode, latitude: item.latitude, longitude: item.longitude,
  };
}

function compact<T extends object>(value: T): Partial<T> {
  return Object.fromEntries(Object.entries(value).filter(([, v]) => v !== null && v !== undefined && v !== "")) as Partial<T>;
}

export async function getFilingWorkspace(userId: string, caseId: string) {
  const item = await ownedCase(userId, caseId);
  const filings = await prisma.caseFiling.findMany({
    where: { caseId, userId },
    orderBy: { createdAt: "desc" },
    select: { id: true, kind: true, forum: true, title: true, subject: true, status: true, recipients: true, createdAt: true, updatedAt: true, sentAt: true },
  });
  const profile = readProfile(item.filingProfile);
  const facts = buildCaseFacts(item);
  return {
    facts,
    factsChanged: Boolean(profile.factsHash && profile.factsHash !== hashFacts(facts)),
    profile,
    location: caseLocation(item),
    filings,
  };
}

export async function saveFilingProfile(userId: string, caseId: string, input: unknown) {
  const parsed = profileSchema.safeParse(input);
  if (!parsed.success) throw new CaseAccessError(422, "Some of the details are not valid.");
  const item = await ownedCase(userId, caseId);
  const profile = readProfile(item.filingProfile);
  const { complainant, location, language } = parsed.data;
  const next: FilingProfile = {
    ...profile,
    complainant: complainant ? compact(complainant) : profile.complainant,
    language: language ?? profile.language,
  };
  const updated = await prisma.case.update({
    where: { id: caseId },
    data: {
      filingProfile: asJson(next),
      ...(location ? {
        locality: location.locality ?? null,
        city: location.city ?? item.city,
        district: location.district ?? null,
        state: location.state ?? item.state,
        pincode: location.pincode ?? null,
        latitude: location.latitude ?? null,
        longitude: location.longitude ?? null,
      } : {}),
    },
  });
  return { profile: next, location: caseLocation(updated) };
}

export async function analyzeCaseFacts(userId: string, caseId: string) {
  const item = await ownedCase(userId, caseId);
  const facts = buildCaseFacts(item);
  if (facts.length < 20) {
    throw new CaseAccessError(422, "Describe what happened in the case description (a few sentences) before drafting.");
  }
  const location = caseLocation(item);
  const analysis = await filingRequest<FilingAnalysis>("analyze", {
    facts,
    case_title: item.title,
    location: compact(location),
  });
  const profile: FilingProfile = {
    ...readProfile(item.filingProfile),
    analysis,
    analyzedAt: new Date().toISOString(),
    factsHash: hashFacts(facts),
  };
  await prisma.case.update({ where: { id: caseId }, data: { filingProfile: asJson(profile) } });
  auditCaseAction("filing_analysis", { userId, caseId });
  return { analysis, profile };
}

export async function lookupAuthorities(userId: string, caseId: string, input: unknown) {
  const parsed = z.object({
    kind: z.enum(FILING_KINDS as [string, ...string[]]),
    officeName: z.string().trim().max(200).optional(),
    radiusKm: z.number().finite().min(1).max(50).optional(),
    refresh: z.boolean().optional(),
  }).safeParse(input);
  if (!parsed.success) throw new CaseAccessError(422, "Choose an office or court.");
  const item = await ownedCase(userId, caseId);
  return filingRequest<AuthoritiesResponse>("authorities", {
    kind: parsed.data.kind,
    location: compact(caseLocation(item)),
    office_name: parsed.data.officeName,
    radius_km: parsed.data.radiusKm ?? 10,
    refresh: parsed.data.refresh ?? false,
  }, 150_000);
}

export async function geocodeForCase(userId: string, caseId: string, input: unknown) {
  const parsed = z.object({
    query: z.string().trim().min(2).max(300).optional(),
    latitude: z.number().finite().min(-90).max(90).optional(),
    longitude: z.number().finite().min(-180).max(180).optional(),
  }).safeParse(input);
  if (!parsed.success || (!parsed.data.query && parsed.data.latitude === undefined)) {
    throw new CaseAccessError(422, "Give a place name or allow location access.");
  }
  await ownedCase(userId, caseId);
  return filingRequest<{ place: Record<string, unknown> }>("geocode", parsed.data, 30_000);
}

export async function draftCaseFiling(userId: string, caseId: string, input: unknown) {
  const parsed = draftSchema.safeParse(input);
  if (!parsed.success) throw new CaseAccessError(422, "Choose an office or court to draft for.");
  const item = await ownedCase(userId, caseId);
  const facts = buildCaseFacts(item);
  if (facts.length < 20) {
    throw new CaseAccessError(422, "Describe what happened in the case description before drafting.");
  }
  const profile = readProfile(item.filingProfile);
  const { kind, recipient, instructions } = parsed.data;
  const language = parsed.data.language || profile.language || "en";
  const draft = await filingRequest<DraftResult>("draft", {
    kind,
    facts,
    analysis: profile.analysis ?? null,
    complainant: profile.complainant ?? null,
    recipient: recipient ?? null,
    location: compact(caseLocation(item)),
    language,
    instructions,
  }, 170_000);

  const to = cleanAddresses(parsed.data.to ?? (recipient?.email ? [recipient.email] : []));
  const filing = await prisma.$transaction(async (tx) => {
    const created = await tx.caseFiling.create({
      data: {
        caseId,
        userId,
        kind,
        forum: draft.forum,
        title: draft.title.slice(0, 300),
        subject: draft.subject.slice(0, 600),
        addressee: draft.addressee,
        body: draft.text,
        recipients: asJson({ to, recipient: recipient ?? null }),
        cc: asJson(cleanAddresses(parsed.data.cc)),
        sections: asJson(draft.sections),
        citations: asJson(draft.citations),
        warnings: asJson(draft.warnings),
        placeholders: asJson(draft.placeholders),
        filing: asJson({ ...draft.filing, enclosures: draft.enclosures, disclaimer: draft.disclaimer }),
        emailBody: draft.email.cover_note,
        language,
        generation: asJson({ model_used: draft.model_used, template: draft.template }),
      },
    });
    await tx.caseTimelineEvent.create({
      data: {
        caseId,
        type: "FILING_DRAFTED",
        title: `Drafted: ${kindLabel(kind)}`,
        description: draft.subject.slice(0, 500) || null,
      },
    });
    return created;
  });
  auditCaseAction("filing_drafted", { userId, caseId });
  return filing;
}

export async function getOwnedFiling(userId: string, caseId: string, filingId: string) {
  const filing = await prisma.caseFiling.findFirst({ where: { id: filingId, caseId, userId } });
  if (!filing) throw new CaseAccessError(404, "Document not found");
  return filing;
}

export async function updateOwnedFiling(userId: string, caseId: string, filingId: string, input: unknown) {
  const parsed = updateSchema.safeParse(input);
  if (!parsed.success) throw new CaseAccessError(422, "The changes could not be saved.");
  const existing = await getOwnedFiling(userId, caseId, filingId);
  const { to, cc, status, ...rest } = parsed.data;
  const recipients = (existing.recipients ?? {}) as Record<string, unknown>;
  const statusChanged = status && status !== existing.status;
  const updated = await prisma.caseFiling.update({
    where: { id: filingId },
    data: {
      ...rest,
      ...(to ? { recipients: asJson({ ...recipients, to: cleanAddresses(to) }) } : {}),
      ...(cc ? { cc: asJson(cleanAddresses(cc)) } : {}),
      ...(status ? { status, sentAt: status === "SENT" || status === "FILED" ? existing.sentAt ?? new Date() : existing.sentAt } : {}),
    },
  });
  if (statusChanged && (status === "SENT" || status === "FILED")) {
    await prisma.caseTimelineEvent.create({
      data: {
        caseId,
        type: status === "SENT" ? "FILING_SENT" : "FILING_FILED",
        title: `${status === "SENT" ? "Sent" : "Filed"}: ${kindLabel(existing.kind)}`,
        description: existing.subject.slice(0, 500) || null,
      },
    });
  }
  return updated;
}

export async function deleteOwnedFiling(userId: string, caseId: string, filingId: string) {
  const result = await prisma.caseFiling.deleteMany({ where: { id: filingId, caseId, userId } });
  if (!result.count) throw new CaseAccessError(404, "Document not found");
}
