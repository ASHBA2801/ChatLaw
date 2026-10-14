/**
 * Offices and courts the filing agent can draft for. Mirrors
 * rag-engine/complaints/taxonomy.py (labels only — caveats, portals and
 * recommendations come from the engine's responses).
 */

export const AUTHORITY_KINDS = [
  { id: "police_station", label: "Local police station", short: "Police station" },
  { id: "police_superior", label: "Commissioner / SP office", short: "SP / Commissioner" },
  { id: "collector", label: "District Collector", short: "Collector" },
  { id: "vigilance", label: "Vigilance / DVAC", short: "Vigilance (DVAC)" },
  { id: "cm_cell", label: "Chief Minister's cell", short: "CM cell" },
  { id: "cbi", label: "CBI", short: "CBI" },
  { id: "pmo", label: "PMO (CPGRAMS)", short: "PMO" },
  { id: "women_commission", label: "Commission for Women", short: "Women's commission" },
  { id: "human_rights", label: "Human Rights Commission", short: "Human rights" },
  { id: "cyber_crime", label: "Cyber crime", short: "Cyber crime" },
] as const;

export const COURT_KINDS = [
  { id: "magistrate", label: "Criminal — Judicial Magistrate", short: "Magistrate", subject: "criminal" },
  { id: "civil_court", label: "Civil — District civil court", short: "Civil court", subject: "civil" },
  { id: "family_court", label: "Family court", short: "Family court", subject: "family" },
  { id: "consumer_commission", label: "Consumer commission", short: "Consumer commission", subject: "consumer" },
  { id: "high_court", label: "High Court (Article 226)", short: "High Court", subject: "writ" },
  { id: "supreme_court", label: "Supreme Court (Article 32)", short: "Supreme Court", subject: "writ" },
] as const;

export type FilingKind = (typeof AUTHORITY_KINDS)[number]["id"] | (typeof COURT_KINDS)[number]["id"];
export const FILING_KINDS: readonly FilingKind[] = [...AUTHORITY_KINDS, ...COURT_KINDS].map((k) => k.id);

export function isFilingKind(value: unknown): value is FilingKind {
  return typeof value === "string" && (FILING_KINDS as readonly string[]).includes(value);
}

export function kindLabel(kind: string): string {
  return [...AUTHORITY_KINDS, ...COURT_KINDS].find((k) => k.id === kind)?.label ?? kind;
}

export type Severity = "low" | "moderate" | "serious" | "grave";

export interface Recommendation {
  kind: FilingKind;
  priority: "primary" | "escalation" | "optional";
  reason: string;
}

export interface ProvisionRef {
  id: number;
  law_key: string;
  label: string;
  act_title: string;
  section: string | null;
  text: string;
  source_url: string | null;
}

export interface FilingAnalysis {
  summary: string;
  category: string;
  severity: Severity;
  severity_reason: string | null;
  flags: Record<string, boolean>;
  court_subjects: string[];
  incident: Record<string, string | null>;
  accused: Array<Record<string, string | null>>;
  public_servants: Array<Record<string, string | null>>;
  amount_involved: string | null;
  wrongs: string[];
  missing_information: string[];
  law_search_queries: string[];
  provisions: ProvisionRef[];
  law_notes: string[];
  recommendations: Recommendation[];
  urgent_steps: string[];
  model_used: boolean;
}

export interface ContactEmail {
  address: string;
  label: string | null;
  source_url: string | null;
  verified: boolean;
}

export interface OfficeContact {
  kind: string;
  name: string;
  designation: string | null;
  address: string | null;
  phone: string | null;
  emails: ContactEmail[];
  website: string | null;
  portal_url: string | null;
  notes: string | null;
  source: "curated" | "official_search" | "osm";
  source_url: string | null;
  distance_km: number | null;
}

export interface NearbyOffice {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  address: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  kind_hint: string | null;
}

export interface KindSpec {
  id: FilingKind;
  forum: "authority" | "court";
  label: string;
  description: string;
  channel: "email" | "portal" | "in_person" | "efiling";
  portal_url: string | null;
  portal_label: string | null;
  helpline: string | null;
  caveat: string | null;
}

export interface AuthoritiesResponse {
  kind: FilingKind;
  spec: KindSpec;
  location: FilingLocation;
  offices: OfficeContact[];
  nearby: NearbyOffice[];
  status: string;
  cached: boolean;
  notes: string[];
}

export interface FilingLocation {
  locality?: string | null;
  city?: string | null;
  district?: string | null;
  state?: string | null;
  pincode?: string | null;
  latitude?: number | null;
  longitude?: number | null;
}

export interface Complainant {
  name?: string;
  relation?: string;
  relation_name?: string;
  age?: string;
  occupation?: string;
  address?: string;
  phone?: string;
  email?: string;
  place?: string;
}

export interface FilingProfile {
  complainant?: Complainant;
  analysis?: FilingAnalysis | null;
  analyzedAt?: string | null;
  factsHash?: string | null;
  language?: string;
}

export interface Recipient {
  name: string;
  designation?: string | null;
  address?: string | null;
  email?: string | null;
  phone?: string | null;
  source?: string | null;
  source_url?: string | null;
}

export interface DraftSection {
  heading: string;
  text: string;
  citation_ids?: number[];
}

export interface DraftResult {
  kind: FilingKind;
  forum: "authority" | "court";
  title: string;
  subject: string;
  addressee: string;
  sections: DraftSection[];
  enclosures: string[];
  text: string;
  citations: Array<{ id: number; label: string; act_title: string; law_key: string; source_url: string | null }>;
  placeholders: string[];
  warnings: string[];
  email: { subject: string; body: string; cover_note: string; full_text_fits: boolean };
  filing: {
    channel: KindSpec["channel"];
    portal_url: string | null;
    portal_label: string | null;
    helpline: string | null;
    caveat: string | null;
    notes: string | null;
  };
  template: Record<string, unknown>;
  language: string;
  model_used: boolean;
  disclaimer: string;
}

export const FILING_STATUSES = ["DRAFT", "FINAL", "SENT", "FILED"] as const;
export type FilingStatus = (typeof FILING_STATUSES)[number];
