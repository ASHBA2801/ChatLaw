import type { CaseIntelligence, LocationInput, ResourceResult } from "@/lib/case-intelligence/types";

export interface CaseIntelligenceResponse { intelligence: CaseIntelligence; results: ResourceResult[]; providerStatus: "not_requested" | "location_required" | "ok" | "unavailable"; }

export async function requestCaseIntelligence(input: { query: string; resourceType?: "court" | "advocate"; location?: LocationInput | null; practiceArea?: string; radiusKm?: number }): Promise<CaseIntelligenceResponse> {
  const response = await fetch("/api/case-intelligence", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
  const payload = await response.json().catch(() => null) as CaseIntelligenceResponse | { error?: string } | null;
  if (!response.ok) throw new Error(payload && "error" in payload && payload.error ? payload.error : "Case intelligence is temporarily unavailable.");
  return payload as CaseIntelligenceResponse;
}