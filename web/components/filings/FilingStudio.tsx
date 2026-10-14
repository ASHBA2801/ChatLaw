"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import OfficePanel from "@/components/filings/OfficePanel";
import { PinIcon, ScalesIcon, ShieldIcon } from "@/components/filings/FilingIcons";
import {
  AUTHORITY_KINDS,
  COURT_KINDS,
  kindLabel,
  type Complainant,
  type FilingAnalysis,
  type FilingKind,
  type FilingLocation,
  type FilingProfile,
  type Recommendation,
  type Severity,
} from "@/lib/filings/types";

type SavedFiling = {
  id: string;
  kind: string;
  forum: string;
  title: string;
  subject: string;
  status: string;
  createdAt: string;
};

export type FilingWorkspace = {
  facts: string;
  factsChanged: boolean;
  profile: FilingProfile;
  location: FilingLocation;
  filings: SavedFiling[];
};

const FIELD =
  "mt-1 h-11 w-full rounded-sm border border-[var(--line)] bg-[var(--surface)] px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)]";

export const DOCUMENT_LANGUAGES = [
  ["en", "English"], ["hi", "Hindi — हिन्दी"], ["ta", "Tamil — தமிழ்"], ["te", "Telugu — తెలుగు"],
  ["kn", "Kannada — ಕನ್ನಡ"], ["ml", "Malayalam — മലയാളം"], ["mr", "Marathi — मराठी"], ["bn", "Bengali — বাংলা"],
  ["gu", "Gujarati — ગુજરાતી"], ["pa", "Punjabi — ਪੰਜਾਬੀ"], ["or", "Odia — ଓଡ଼ିଆ"], ["ur", "Urdu — اردو"],
] as const;

const SEVERITY_STYLE: Record<Severity, { label: string; className: string }> = {
  low: { label: "Low", className: "bg-[var(--fill)] text-[var(--ink-muted)]" },
  moderate: { label: "Moderate", className: "bg-[var(--accent-soft)] text-[var(--accent)]" },
  serious: { label: "Serious", className: "bg-[var(--caution-bg)] text-[var(--caution)]" },
  grave: { label: "Grave", className: "bg-[var(--warn-bg)] text-[var(--warn)]" },
};

const PRIORITY_LABEL: Record<Recommendation["priority"], string> = {
  primary: "Recommended",
  escalation: "If no action",
  optional: "Also possible",
};

const STATUS_LABEL: Record<string, string> = { DRAFT: "Draft", FINAL: "Final", SENT: "Sent", FILED: "Filed" };

async function postJson<T>(url: string, body: unknown, method = "POST"): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new Error(payload?.error || "Something went wrong. Please try again.");
  return payload as T;
}

function locationText(location: FilingLocation) {
  return [location.locality, location.city, location.district, location.state, location.pincode]
    .filter(Boolean)
    .join(", ");
}

function DetailsForm({
  caseId,
  complainant,
  location,
  language,
  onSaved,
  onCancel,
}: {
  caseId: string;
  complainant: Complainant;
  location: FilingLocation;
  language: string;
  onSaved: (next: { complainant: Complainant; location: FilingLocation; language: string }) => void;
  onCancel?: () => void;
}) {
  const [person, setPerson] = useState<Complainant>(complainant);
  const [place, setPlace] = useState<FilingLocation>(location);
  const [lang, setLang] = useState(language);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof Complainant>(key: K, value: string) {
    setPerson((current) => ({ ...current, [key]: value }));
  }
  function setLoc<K extends keyof FilingLocation>(key: K, value: string) {
    // A typed place replaces any earlier GPS fix; coordinates are found again on save.
    setPlace((current) => ({ ...current, [key]: value, latitude: null, longitude: null }));
  }

  async function applyPlace(body: Record<string, unknown>) {
    const { place: found } = await postJson<{ place: Record<string, unknown> }>(`/api/cases/${caseId}/filings/geocode`, body);
    const str = (v: unknown) => (typeof v === "string" && v ? v : null);
    return {
      locality: str(found.locality),
      city: str(found.city),
      district: str(found.district),
      state: str(found.state),
      pincode: str(found.pincode),
      latitude: typeof found.latitude === "number" ? found.latitude : null,
      longitude: typeof found.longitude === "number" ? found.longitude : null,
    } satisfies FilingLocation;
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setError("This browser cannot share its location. Type your area instead.");
      return;
    }
    setStatus("Finding your location…");
    setError(null);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const found = await applyPlace({ latitude: position.coords.latitude, longitude: position.coords.longitude });
          setPlace({ ...found, latitude: position.coords.latitude, longitude: position.coords.longitude });
          setStatus("Location found. Check the district and state, then save.");
        } catch (problem) {
          setStatus(null);
          setError(problem instanceof Error ? problem.message : "The location could not be found.");
        }
      },
      () => {
        setStatus(null);
        setError("Location permission was not given. Type your area instead.");
      },
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 300000 },
    );
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      let nextPlace = place;
      if ((nextPlace.latitude == null || nextPlace.longitude == null) && locationText(nextPlace)) {
        setStatus("Locating your area…");
        try {
          const found = await applyPlace({ query: locationText(nextPlace) });
          nextPlace = {
            ...nextPlace,
            latitude: found.latitude,
            longitude: found.longitude,
            district: nextPlace.district || found.district,
            state: nextPlace.state || found.state,
          };
        } catch {
          // Keep the typed place; nearby search will ask for a clearer location.
        }
      }
      const result = await postJson<{ location: FilingLocation }>(
        `/api/cases/${caseId}/filings/profile`,
        { complainant: person, location: nextPlace, language: lang },
        "PATCH",
      );
      setStatus(null);
      onSaved({ complainant: person, location: result.location, language: lang });
    } catch (problem) {
      setStatus(null);
      setError(problem instanceof Error ? problem.message : "Your details could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} className="mt-4 grid gap-4">
      <fieldset className="grid gap-3 sm:grid-cols-2">
        <legend className="mb-2 text-sm font-semibold">Who is making the complaint</legend>
        <label className="text-sm font-medium sm:col-span-2">Full name
          <input value={person.name ?? ""} onChange={(e) => set("name", e.target.value)} className={FIELD} autoComplete="name" maxLength={200} />
        </label>
        <div className="grid grid-cols-[7rem_1fr] gap-2 sm:col-span-2">
          <label className="text-sm font-medium">Relation
            <select value={person.relation ?? "S/o"} onChange={(e) => set("relation", e.target.value)} className={FIELD}>
              <option value="S/o">Son of</option>
              <option value="D/o">Daughter of</option>
              <option value="W/o">Wife of</option>
              <option value="H/o">Husband of</option>
              <option value="C/o">Care of</option>
            </select>
          </label>
          <label className="text-sm font-medium">Father / mother / spouse name
            <input value={person.relation_name ?? ""} onChange={(e) => set("relation_name", e.target.value)} className={FIELD} maxLength={200} />
          </label>
        </div>
        <label className="text-sm font-medium">Age
          <input value={person.age ?? ""} onChange={(e) => set("age", e.target.value)} className={FIELD} inputMode="numeric" maxLength={3} />
        </label>
        <label className="text-sm font-medium">Occupation
          <input value={person.occupation ?? ""} onChange={(e) => set("occupation", e.target.value)} className={FIELD} maxLength={120} />
        </label>
        <label className="text-sm font-medium sm:col-span-2">Postal address
          <textarea value={person.address ?? ""} onChange={(e) => set("address", e.target.value)} rows={2} maxLength={600}
            className="mt-1 w-full rounded-sm border border-[var(--line)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)]" autoComplete="street-address" />
        </label>
        <label className="text-sm font-medium">Mobile
          <input value={person.phone ?? ""} onChange={(e) => set("phone", e.target.value)} className={FIELD} inputMode="tel" autoComplete="tel" maxLength={40} />
        </label>
        <label className="text-sm font-medium">Email
          <input value={person.email ?? ""} onChange={(e) => set("email", e.target.value)} className={FIELD} type="email" autoComplete="email" maxLength={200} />
        </label>
      </fieldset>

      <fieldset className="grid gap-3 border-t border-[var(--line)] pt-4 sm:grid-cols-2">
        <legend className="mb-2 flex w-full flex-wrap items-center justify-between gap-2 text-sm font-semibold">
          <span>Where it happened / where you live</span>
        </legend>
        <div className="sm:col-span-2">
          <button type="button" onClick={useMyLocation} className="btn-secondary btn-sm">
            <PinIcon className="h-4 w-4" /> Use my current location
          </button>
          <p className="mt-1 text-xs text-[var(--ink-muted)]">Used only to find the nearest police stations, courts and offices.</p>
        </div>
        <label className="text-sm font-medium">Area / locality
          <input value={place.locality ?? ""} onChange={(e) => setLoc("locality", e.target.value)} className={FIELD} maxLength={160} placeholder="e.g. Gandhipuram" />
        </label>
        <label className="text-sm font-medium">City / town
          <input value={place.city ?? ""} onChange={(e) => setLoc("city", e.target.value)} className={FIELD} maxLength={120} />
        </label>
        <label className="text-sm font-medium">District
          <input value={place.district ?? ""} onChange={(e) => setLoc("district", e.target.value)} className={FIELD} maxLength={160} />
        </label>
        <label className="text-sm font-medium">State
          <input value={place.state ?? ""} onChange={(e) => setLoc("state", e.target.value)} className={FIELD} maxLength={120} />
        </label>
        <label className="text-sm font-medium">PIN code
          <input value={place.pincode ?? ""} onChange={(e) => setLoc("pincode", e.target.value)} className={FIELD} inputMode="numeric" maxLength={6} />
        </label>
        <label className="text-sm font-medium">Language of the document
          <select value={lang} onChange={(e) => setLang(e.target.value)} className={FIELD}>
            {DOCUMENT_LANGUAGES.map(([code, label]) => <option key={code} value={code}>{label}</option>)}
          </select>
        </label>
      </fieldset>

      <div aria-live="polite">
        {status && <p className="text-sm text-[var(--ink-muted)]" role="status">{status}</p>}
        {error && <p className="text-sm text-[var(--warn)]" role="alert">{error}</p>}
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={busy} className="btn-primary">{busy ? "Saving…" : "Save details"}</button>
        {onCancel && <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>}
      </div>
    </form>
  );
}

function AnalysisView({ analysis }: { analysis: FilingAnalysis }) {
  const severity = SEVERITY_STYLE[analysis.severity] ?? SEVERITY_STYLE.moderate;
  return (
    <div className="mt-4 grid gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${severity.className}`}>Severity: {severity.label}</span>
        <span className="rounded-full bg-[var(--fill)] px-3 py-1 text-xs font-semibold text-[var(--foreground)]">{analysis.category}</span>
      </div>
      <p className="text-sm leading-6">{analysis.summary}</p>
      {analysis.severity_reason && <p className="text-sm text-[var(--ink-muted)]">{analysis.severity_reason}</p>}
      {analysis.urgent_steps.length > 0 && (
        <div className="rounded-lg border border-[var(--caution-line)] bg-[var(--caution-bg)] p-3 text-sm text-[var(--caution)]" role="note">
          <p className="font-semibold">Do this first</p>
          <ul className="mt-1 list-disc space-y-1 pl-5">{analysis.urgent_steps.map((step) => <li key={step}>{step}</li>)}</ul>
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-2">
        {analysis.provisions.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-[var(--ink-muted)]">Provisions found in the statute text</p>
            <ul className="mt-2 space-y-1 text-sm">
              {analysis.provisions.slice(0, 8).map((p) => (
                <li key={p.law_key}>
                  <Link href={`/research?q=${encodeURIComponent(p.label)}`} className="text-[var(--accent)] underline-offset-2 hover:underline">{p.label}</Link>
                </li>
              ))}
            </ul>
          </div>
        )}
        {analysis.missing_information.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-[var(--ink-muted)]">A stronger complaint would also say</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[var(--ink-muted)]">
              {analysis.missing_information.map((item) => <li key={item}>{item}</li>)}
            </ul>
            <p className="mt-2 text-xs text-[var(--ink-muted)]">Add these to the case description, then analyse again. Missing details appear as [BLANKS] in the draft.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function FilingStudio({ caseId, initial }: { caseId: string; initial: FilingWorkspace }) {
  const [complainant, setComplainant] = useState<Complainant>(initial.profile.complainant ?? {});
  const [location, setLocation] = useState<FilingLocation>(initial.location);
  const [language, setLanguage] = useState(initial.profile.language ?? "en");
  const [editingDetails, setEditingDetails] = useState(!initial.profile.complainant?.name);
  const [analysis, setAnalysis] = useState<FilingAnalysis | null>(initial.profile.analysis ?? null);
  // The facts the current analysis was made from; the case description can change below.
  const [analyzedFor, setAnalyzedFor] = useState<string | null>(initial.factsChanged ? null : initial.facts);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forum, setForum] = useState<"authority" | "court">("authority");
  const [kind, setKind] = useState<FilingKind | null>(null);

  const hasFacts = initial.facts.trim().length >= 20;
  const stale = Boolean(analysis) && analyzedFor !== initial.facts;
  const recommendations = new Map((analysis?.recommendations ?? []).map((r) => [r.kind, r]));

  async function analyze() {
    setAnalyzing(true);
    setError(null);
    try {
      const result = await postJson<{ analysis: FilingAnalysis }>(`/api/cases/${caseId}/filings/analyze`, {});
      setAnalysis(result.analysis);
      setAnalyzedFor(initial.facts);
      const primary = result.analysis.recommendations.find((r) => r.priority === "primary");
      if (primary && COURT_KINDS.some((k) => k.id === primary.kind) && !result.analysis.recommendations.some((r) => r.priority === "primary" && AUTHORITY_KINDS.some((k) => k.id === r.kind))) {
        setForum("court");
      }
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : "The case could not be analysed.");
    } finally {
      setAnalyzing(false);
    }
  }

  const kinds = forum === "authority" ? AUTHORITY_KINDS : COURT_KINDS;
  const sortedKinds = [...kinds].sort((a, b) => {
    const order = { primary: 0, escalation: 1, optional: 2 } as const;
    const ra = recommendations.get(a.id);
    const rb = recommendations.get(b.id);
    return (ra ? order[ra.priority] : 3) - (rb ? order[rb.priority] : 3);
  });

  return (
    <section className="mt-8 rounded-xl border border-[var(--line)] bg-[var(--surface)] p-5 shadow-[var(--shadow-soft)] sm:p-6" aria-labelledby="filing-studio-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="filing-studio-title" className="text-xl font-semibold">Complaints and petitions</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--ink-muted)]">
            Draft a written complaint for the police or a government office, or a petition for a court, from the facts in this case.
            ChatLaw finds where to send it; you review, print or email it yourself.
          </p>
        </div>
      </div>

      {/* Step 1 — details */}
      <div className="mt-6 border-t border-[var(--line)] pt-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-base font-semibold">1. Your details</h3>
          {!editingDetails && <button type="button" onClick={() => setEditingDetails(true)} className="btn-secondary btn-sm">Edit</button>}
        </div>
        {editingDetails ? (
          <DetailsForm
            caseId={caseId}
            complainant={complainant}
            location={location}
            language={language}
            onSaved={(next) => {
              setComplainant(next.complainant);
              setLocation(next.location);
              setLanguage(next.language);
              setEditingDetails(false);
            }}
            onCancel={complainant.name ? () => setEditingDetails(false) : undefined}
          />
        ) : (
          <dl className="mt-3 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
            <div><dt className="text-xs text-[var(--ink-muted)]">Complainant</dt><dd>{complainant.name}{complainant.phone ? ` · ${complainant.phone}` : ""}</dd></div>
            <div><dt className="text-xs text-[var(--ink-muted)]">Location</dt><dd className="flex items-center gap-1"><PinIcon className="h-4 w-4 text-[var(--ink-muted)]" />{locationText(location) || "Not set"}{location.latitude != null ? "" : locationText(location) ? " (approximate)" : ""}</dd></div>
          </dl>
        )}
      </div>

      {/* Step 2 — analysis */}
      <div className="mt-6 border-t border-[var(--line)] pt-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-base font-semibold">2. Understand the matter</h3>
          <button type="button" onClick={() => void analyze()} disabled={analyzing || !hasFacts} className={analysis ? "btn-secondary btn-sm" : "btn-primary btn-sm"}>
            {analyzing ? "Reading the case…" : analysis ? "Analyse again" : "Analyse this case"}
          </button>
        </div>
        {!hasFacts && (
          <p className="mt-3 text-sm text-[var(--ink-muted)]">
            Write what happened in the case description below — dates, places, the people involved and any loss — then analyse the case.
          </p>
        )}
        {stale && analysis && (
          <p className="mt-3 text-sm text-[var(--caution)]">The case has changed since the last analysis. Analyse again so the drafts use the latest facts.</p>
        )}
        {error && <p className="mt-3 text-sm text-[var(--warn)]" role="alert">{error}</p>}
        {analyzing && <p className="mt-3 text-sm text-[var(--ink-muted)]" role="status">Reading the facts and searching the statute text…</p>}
        {analysis && !analyzing && <AnalysisView analysis={analysis} />}
      </div>

      {/* Step 3 — where to file */}
      <div className="mt-6 border-t border-[var(--line)] pt-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-base font-semibold">3. Where to file</h3>
          <div className="inline-flex rounded-lg bg-[var(--fill)] p-1" role="tablist" aria-label="Authorities or courts">
            {(["authority", "court"] as const).map((value) => (
              <button
                key={value}
                type="button"
                role="tab"
                aria-selected={forum === value}
                onClick={() => { setForum(value); setKind(null); }}
                className={`inline-flex min-h-10 items-center gap-2 rounded-md px-4 text-sm font-semibold ${forum === value ? "bg-[var(--surface)] text-[var(--foreground)] shadow-sm" : "text-[var(--ink-muted)]"}`}
              >
                {value === "authority" ? <ShieldIcon className="h-4 w-4" /> : <ScalesIcon className="h-4 w-4" />}
                {value === "authority" ? "Police & offices" : "Courts"}
              </button>
            ))}
          </div>
        </div>
        {!analysis && <p className="mt-2 text-sm text-[var(--ink-muted)]">Analyse the case to see which offices and courts fit it. You can still choose any of them.</p>}
        <ul className="mt-4 grid list-none gap-2 sm:grid-cols-2 lg:grid-cols-3" role="list">
          {sortedKinds.map((item) => {
            const rec = recommendations.get(item.id);
            const active = kind === item.id;
            return (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => setKind(active ? null : item.id)}
                  aria-pressed={active}
                  disabled={!hasFacts}
                  className={`flex h-full w-full flex-col items-start gap-1 rounded-lg border p-3 text-left transition-colors disabled:opacity-50 ${active ? "border-[var(--accent)] bg-[var(--accent-soft)]" : "border-[var(--line)] hover:border-[var(--accent)]"}`}
                >
                  <span className="flex w-full items-center justify-between gap-2">
                    <span className="text-sm font-semibold">{item.label}</span>
                    {rec && (
                      <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${rec.priority === "primary" ? "bg-[var(--accent)] text-[var(--on-accent)]" : "bg-[var(--fill)] text-[var(--ink-muted)]"}`}>
                        {PRIORITY_LABEL[rec.priority]}
                      </span>
                    )}
                  </span>
                  {rec && <span className="text-xs leading-5 text-[var(--ink-muted)]">{rec.reason}</span>}
                </button>
              </li>
            );
          })}
        </ul>

        {kind && (
          <OfficePanel
            key={kind}
            caseId={caseId}
            kind={kind}
            language={language}
            hasLocation={Boolean(location.state || location.district || location.latitude != null)}
            complainantReady={Boolean(complainant.name)}
            onClose={() => setKind(null)}
          />
        )}
      </div>

      {initial.filings.length > 0 && (
        <div className="mt-6 border-t border-[var(--line)] pt-5">
          <h3 className="text-base font-semibold">Drafted documents</h3>
          <ul className="mt-3 divide-y divide-[var(--line)]">
            {initial.filings.map((filing) => (
              <li key={filing.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium" title={filing.title}>{filing.title}</p>
                  <p className="mt-0.5 text-xs text-[var(--ink-muted)]">
                    {kindLabel(filing.kind)} · {STATUS_LABEL[filing.status] ?? filing.status} · {new Date(filing.createdAt).toLocaleDateString("en-IN")}
                  </p>
                </div>
                <Link href={`/cases/${caseId}/filings/${filing.id}`} className="btn-secondary btn-sm">Open</Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
