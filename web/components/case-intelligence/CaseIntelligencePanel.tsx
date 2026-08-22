"use client";

import { useState } from "react";
import type { CaseIntelligence, LocationInput, ResourceResult } from "@/lib/case-intelligence/types";
import { requestCaseIntelligence } from "@/lib/api/case-intelligence";

function ResourceList({ results, type }: { results: ResourceResult[]; type: "court" | "advocate" }) {
  if (!results.length) {
    return (
      <p className="rounded-xl border border-dashed border-[var(--line)] bg-[var(--background)] p-4 text-sm text-[var(--ink-muted)]">
        No verified {type === "court" ? "court information" : "advocate directories"} matched. Try another city/state or a wider radius.
      </p>
    );
  }
  return (
    <div className="space-y-3">
      {type === "advocate" ? (
        <p className="text-xs leading-5 text-[var(--ink-muted)]">
          Results are official bar-council and legal-aid directories — not personal endorsements of individual lawyers. ChatLaw does not invent advocate profiles.
        </p>
      ) : (
        <p className="text-xs leading-5 text-[var(--ink-muted)]">
          Court listings use official judiciary / eCourts sources. Confirm jurisdiction for your matter before filing.
        </p>
      )}
      {results.map((result) => (
        <article key={result.id} className="rounded-xl border border-[var(--line)] bg-white p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h4 className="font-semibold">{result.name}</h4>
              <p className="mt-1 text-sm text-[var(--ink-muted)]">
                {result.type === "court"
                  ? result.court_type || "Court/forum"
                  : result.practice_areas?.join(" · ") || "Practice areas unavailable"}
              </p>
            </div>
            {result.distance_km !== null && result.distance_km !== undefined ? (
              <span className="shrink-0 text-xs text-[var(--ink-muted)]">{result.distance_km.toFixed(1)} km</span>
            ) : null}
          </div>
          <p className="mt-3 text-sm">
            {[result.address, result.city, result.state].filter(Boolean).join(", ") || "Location unavailable"}
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            {result.source_type ? (
              <span className="rounded-full bg-[#eef5d0] px-2 py-1 text-[var(--forest)]">Source: {result.source_type}</span>
            ) : null}
            {result.verification_status === "verified" ? (
              <span className="rounded-full border border-[var(--line)] px-2 py-1">Verified official directory</span>
            ) : null}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {(result.profile_url || result.official_url) && (
              <a
                href={result.profile_url || result.official_url || "#"}
                target="_blank"
                rel="noreferrer"
                className="min-h-10 rounded-lg border border-[var(--line)] px-3 py-2 text-sm font-medium text-[var(--forest)]"
              >
                {type === "court" ? "Official website" : "Open directory"}
              </a>
            )}
            {result.phone ? (
              <a href={`tel:${result.phone}`} className="min-h-10 rounded-lg border border-[var(--line)] px-3 py-2 text-sm">
                Contact
              </a>
            ) : null}
          </div>
        </article>
      ))}
    </div>
  );
}

export default function CaseIntelligencePanel({
  query,
  initial,
  defaultLocation = "",
  defaultPracticeArea = "",
}: {
  query: string;
  initial?: CaseIntelligence | null;
  defaultLocation?: string;
  defaultPracticeArea?: string;
}) {
  const [intelligence, setIntelligence] = useState<CaseIntelligence | null>(initial || null);
  const [locationText, setLocationText] = useState(defaultLocation);
  const [practiceArea, setPracticeArea] = useState(defaultPracticeArea);
  const [radiusKm, setRadiusKm] = useState(25);
  const [resourceType, setResourceType] = useState<"court" | "advocate" | null>(null);
  const [results, setResults] = useState<ResourceResult[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load(nextType: "court" | "advocate") {
    const parts = locationText.split(",").map((part) => part.trim()).filter(Boolean);
    const location: LocationInput | null = parts.length ? { city: parts[0], state: parts[1], country: parts[2] || "India" } : null;
    setLoading(true); setResourceType(nextType); setStatus(null);
    try { const response = await requestCaseIntelligence({ query, resourceType: nextType, location, practiceArea: practiceArea || undefined, radiusKm }); setIntelligence(response.intelligence); setResults(response.results); setStatus(response.providerStatus); } catch (error) { setResults([]); setStatus(error instanceof Error ? error.message : "Provider unavailable"); } finally { setLoading(false); }
  }

  return <section className="mt-5 rounded-2xl border border-[var(--line)] bg-[#fbfcf8] p-4 sm:p-5" aria-label="Case intelligence"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="text-base font-semibold">Case intelligence</h3><p className="mt-1 text-sm text-[var(--ink-muted)]">A practical orientation layered on top of ChatLaw’s grounded answer.</p></div>{intelligence?.urgency === "potentially_urgent" && <span className="rounded-full bg-[#fff1df] px-3 py-1 text-xs font-semibold text-[#7b4b17]">May require prompt assistance</span>}</div>{intelligence && <div className="mt-4 grid gap-4 sm:grid-cols-2"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--ink-muted)]">Legal area</p><p className="mt-1 font-medium">{intelligence.case_category}</p></div><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--ink-muted)]">Jurisdiction</p><p className="mt-1 font-medium">{intelligence.jurisdiction || "Not specified"}</p></div><div className="sm:col-span-2"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--ink-muted)]">Potentially useful documents</p><ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-[var(--ink-muted)]">{intelligence.required_documents.map((item) => <li key={item}>{item}</li>)}</ul></div></div>}<div className="mt-5 grid gap-3 sm:grid-cols-[1fr_1fr_auto]"><label className="text-sm"><span className="mb-1 block font-medium">City and state</span><input value={locationText} onChange={(event) => setLocationText(event.target.value)} placeholder="e.g. Coimbatore, Tamil Nadu" className="h-11 w-full rounded-lg border border-[var(--line)] bg-white px-3 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]" /></label><label className="text-sm"><span className="mb-1 block font-medium">Practice area</span><input value={practiceArea} onChange={(event) => setPracticeArea(event.target.value)} placeholder="Optional for advocates" className="h-11 w-full rounded-lg border border-[var(--line)] bg-white px-3 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]" /></label><label className="text-sm"><span className="mb-1 block font-medium">Radius</span><select value={radiusKm} onChange={(event) => setRadiusKm(Number(event.target.value))} className="h-11 w-full rounded-lg border border-[var(--line)] bg-white px-3"><option value={10}>10 km</option><option value={25}>25 km</option><option value={50}>50 km</option><option value={100}>100 km</option></select></label></div><div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={() => void load("court")} disabled={loading} className="min-h-11 rounded-lg bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-50">Find relevant courts</button><button type="button" onClick={() => void load("advocate")} disabled={loading} className="min-h-11 rounded-lg border border-[var(--forest)] px-4 text-sm font-semibold text-[var(--forest)] disabled:opacity-50">Find nearby advocates</button></div>{loading && <p className="mt-4 text-sm text-[var(--ink-muted)]" role="status">Checking provider information…</p>}{status === "location_required" && <p className="mt-4 text-sm text-[#7b4b17]">Add your city and state to search nearby resources.</p>}{status === "unavailable" && <p className="mt-4 text-sm text-[#7b4b17]">Location services are temporarily unavailable. Your legal answer remains available.</p>}{resourceType && !loading && status === "ok" && <div className="mt-5"><div className="mb-3 flex items-center justify-between"><h4 className="font-semibold">{resourceType === "court" ? "Potentially relevant courts" : "Nearby advocates"}</h4><span className="text-xs text-[var(--ink-muted)]">List view · map provider not configured</span></div><ResourceList results={results} type={resourceType} /></div>}{intelligence && <p className="mt-5 text-xs leading-5 text-[var(--ink-muted)]">{intelligence.limitations.join(" ")}</p>}</section>;
}