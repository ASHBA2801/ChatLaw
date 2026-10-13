import { ragRequest, RagApiError } from "@/lib/api/rag";

export type CourtLevel = "SUPREME_COURT" | "HIGH_COURT" | "DISTRICT_COURT" | "TRIBUNAL";

export const COURT_LEVELS: { value: CourtLevel; label: string }[] = [
  { value: "SUPREME_COURT", label: "Supreme Court" },
  { value: "HIGH_COURT", label: "High Courts" },
  { value: "DISTRICT_COURT", label: "District Courts" },
  { value: "TRIBUNAL", label: "Tribunals" },
];

export interface Provision {
  law_key: string;
  act_id: string;
  act_title: string;
  short_title: string;
  section: string | null;
  label: string;
  text: string;
  chapter: string | null;
  page_number: number | null;
  source_url: string | null;
  similarity: number | null;
  matched_by: "reference" | "semantic";
  translated_from: string | null;
}

export interface LawResponse {
  query: string;
  law_keys: string[];
  provisions: Provision[];
  notes: string[];
}

export interface Articulation {
  overview: string;
  elements: string[];
  key_points: string[];
  consequences: string[];
  exceptions: string[];
  related_provisions: string[];
  practical_steps: string[];
  case_search_topic: string | null;
  sources: string[];
}

export interface ArticulateResponse {
  query: string;
  articulation: Articulation | null;
  error: string | null;
}

export interface JudgmentSummary {
  facts: string | null;
  issues: string[];
  arguments: string[];
  held: string | null;
  ratio: string | null;
  provisions_applied: string[];
  outcome: string | null;
  significance: string | null;
}

export interface ResearchCase {
  id: string;
  title: string;
  court: string;
  court_level: CourtLevel;
  jurisdiction: string;
  judgment_date: string | null;
  case_number: string | null;
  citation: string | null;
  petitioner: string | null;
  respondent: string | null;
  source_url: string;
  source_authority: string;
  summary: string;
  holding: string;
  relevance: string;
  law_keys: string[];
  is_landmark: boolean;
  origin: "CURATED" | "SEED" | "DISCOVERED";
  verification: { status: string; reason: string | null; verified_at: string | null } | null;
  predecessor_provision: string | null;
  provisions: string[];
  detailed_summary: JudgmentSummary | null;
  similarity?: number | null;
  is_new?: boolean;
}

export interface CasesResponse {
  query: string;
  law_keys: string[];
  cases: ResearchCase[];
  source: "library" | "official_search" | "mixed" | "none";
  discovery_ran: boolean;
  proposed: number;
  verified: number;
  message: string | null;
}

export interface ActSummary {
  act_id: string;
  title: string | null;
  short_title: string | null;
  domain: string | null;
  section_count: number;
  case_count: number;
}

export interface SectionSummary {
  section: string;
  preview: string;
  case_count: number;
  lookup_status: "FOUND" | "NONE_FOUND" | "FAILED" | null;
}

// Searching official court sites and verifying each judgment can take a while.
const CASE_SEARCH_TIMEOUT_MS = 180_000;

function post<T>(path: string, body: unknown, timeoutMs?: number) {
  return ragRequest<T>(path, { method: "POST", body: JSON.stringify(body) }, timeoutMs);
}

export const researchLaw = (query: string) => post<LawResponse>("/api/research/law", { query });

export const articulateLaw = (query: string) => post<ArticulateResponse>("/api/research/articulate", { query });

export function researchCases(request: {
  query: string;
  law_keys?: string[];
  court_levels?: CourtLevel[];
  refresh?: boolean;
  limit?: number;
}) {
  return post<CasesResponse>("/api/research/cases", request, CASE_SEARCH_TIMEOUT_MS);
}

export async function summarizeJudgment(caseId: string): Promise<JudgmentSummary> {
  try {
    const response = await post<{ case_id: string; summary: JudgmentSummary }>(
      "/api/research/judgment-summary",
      { case_id: caseId },
      CASE_SEARCH_TIMEOUT_MS,
    );
    return response.summary;
  } catch (error) {
    if (error instanceof RagApiError && error.status === 404) {
      throw new RagApiError("A detailed summary could not be produced from the official judgment text.", 404);
    }
    throw error;
  }
}

export const listActs = () => ragRequest<{ acts: ActSummary[] }>("/api/research/acts");

export const listSections = (actId: string) =>
  ragRequest<{ act_id: string; sections: SectionSummary[] }>(`/api/research/acts/${encodeURIComponent(actId)}/sections`);

export const lawCases = (lawKey: string) =>
  ragRequest<{ law_key: string; cases: ResearchCase[] }>(`/api/research/law-cases?law_key=${encodeURIComponent(lawKey)}`);

export function courtLevelLabel(level: string): string {
  return COURT_LEVELS.find((item) => item.value === level)?.label.replace(/s$/, "") ?? level;
}

export function formatJudgmentDate(value: string | null): string {
  if (!value) return "Date not recorded";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export function lawKeyLabel(lawKey: string, actNames: Record<string, string> = {}): string {
  const [actId, section] = lawKey.split(":");
  const name = actNames[actId] ?? actId;
  if (!section) return name;
  return actId === "CONSTITUTION" ? `Article ${section}, ${name}` : `Section ${section}, ${name}`;
}
