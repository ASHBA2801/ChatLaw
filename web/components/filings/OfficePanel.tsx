"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ExternalIcon, PinIcon } from "@/components/filings/FilingIcons";
import { cleanAddresses, isEmail } from "@/lib/filings/mail";
import { kindLabel, type AuthoritiesResponse, type FilingKind, type Recipient } from "@/lib/filings/types";
import { isSafeExternalUrl } from "@/lib/urls/safeUrl";

type Choice = { source: "office" | "nearby"; index: number } | null;

const SOURCE_LABEL: Record<string, string> = {
  curated: "Checked official directory",
  official_search: "Found on an official website",
  osm: "OpenStreetMap",
};

function ExternalLink({ href, children }: { href: string | null | undefined; children: React.ReactNode }) {
  const safe = isSafeExternalUrl(href ?? null);
  if (!safe) return null;
  return (
    <a href={safe} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-medium text-[var(--accent)] underline-offset-2 hover:underline">
      {children}
      <ExternalIcon className="h-3.5 w-3.5" />
    </a>
  );
}

export default function OfficePanel({
  caseId,
  kind,
  language,
  hasLocation,
  complainantReady,
  onClose,
}: {
  caseId: string;
  kind: FilingKind;
  language: string;
  hasLocation: boolean;
  complainantReady: boolean;
  onClose: () => void;
}) {
  const router = useRouter();
  const [data, setData] = useState<AuthoritiesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [choice, setChoice] = useState<Choice>(null);
  const [emails, setEmails] = useState<string[]>([]);
  const [manualEmail, setManualEmail] = useState("");
  const [instructions, setInstructions] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [radiusKm, setRadiusKm] = useState(10);

  const request = useCallback(async (options: { officeName?: string; refresh?: boolean; radius?: number }) => {
    const response = await fetch(`/api/cases/${caseId}/filings/authorities`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind, officeName: options.officeName, refresh: options.refresh, radiusKm: options.radius ?? radiusKm }),
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) throw new Error(payload?.error || "Offices could not be looked up.");
    return payload as AuthoritiesResponse;
  }, [caseId, kind, radiusKm]);

  const apply = useCallback((result: AuthoritiesResponse) => {
    setData(result);
    const firstOffice = result.offices.findIndex((o) => o.emails.length > 0);
    if (firstOffice >= 0) {
      setChoice({ source: "office", index: firstOffice });
      setEmails(result.offices[firstOffice].emails.filter((e) => e.verified).map((e) => e.address));
    } else if (result.nearby.length) {
      setChoice({ source: "nearby", index: 0 });
    } else if (result.offices.length) {
      setChoice({ source: "office", index: 0 });
    }
    setLoading(false);
  }, []);

  const fail = useCallback((problem: unknown) => {
    setError(problem instanceof Error ? problem.message : "Offices could not be looked up.");
    setLoading(false);
  }, []);

  async function load(options: { officeName?: string; refresh?: boolean; radius?: number } = {}) {
    setLoading(true);
    setError(null);
    try {
      apply(await request(options));
    } catch (problem) {
      fail(problem);
    }
  }

  useEffect(() => {
    // Look the office up once when the panel opens; later lookups are user-initiated.
    request({}).then(apply, fail);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind]);

  const recipient: Recipient | null = useMemo(() => {
    if (!data || !choice) return null;
    if (choice.source === "office") {
      const office = data.offices[choice.index];
      if (!office) return null;
      return {
        name: office.name,
        designation: office.designation,
        address: office.address,
        email: office.emails.find((e) => e.verified)?.address ?? null,
        phone: office.phone,
        source: office.source,
        source_url: office.source_url,
      };
    }
    const place = data.nearby[choice.index];
    if (!place) return null;
    return {
      name: place.name,
      designation: kind === "police_station" ? "The Station House Officer" : null,
      address: place.address,
      phone: place.phone,
      source: "osm",
    };
  }, [choice, data, kind]);

  function toggleEmail(address: string, on: boolean) {
    setEmails((current) => (on ? cleanAddresses([...current, address]) : current.filter((item) => item !== address)));
  }

  function addManual() {
    if (!isEmail(manualEmail)) {
      setError("That does not look like an email address.");
      return;
    }
    setError(null);
    toggleEmail(manualEmail.trim().toLowerCase(), true);
    setManualEmail("");
  }

  async function draft() {
    setDrafting(true);
    setError(null);
    try {
      const response = await fetch(`/api/cases/${caseId}/filings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, recipient, to: emails, language, instructions: instructions || undefined }),
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error(payload?.error || "The document could not be drafted.");
      router.push(`/cases/${caseId}/filings/${payload.filing.id}`);
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : "The document could not be drafted.");
      setDrafting(false);
    }
  }

  const spec = data?.spec;
  const allEmails = cleanAddresses([
    ...(data?.offices.flatMap((o) => o.emails.filter((e) => e.verified).map((e) => e.address)) ?? []),
    ...emails,
  ]);

  return (
    <div className="mt-5 rounded-xl border border-[var(--line-strong)] p-4 sm:p-5" aria-live="polite">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="text-base font-semibold">{kindLabel(kind)}</h4>
          {spec && <p className="mt-1 max-w-2xl text-sm text-[var(--ink-muted)]">{spec.description}</p>}
        </div>
        <button type="button" onClick={onClose} className="btn-secondary btn-sm">Close</button>
      </div>

      {spec?.caveat && (
        <p className="mt-3 rounded-lg border border-[var(--caution-line)] bg-[var(--caution-bg)] p-3 text-sm text-[var(--caution)]">{spec.caveat}</p>
      )}
      {spec?.helpline && <p className="mt-3 text-sm">Helpline: <a className="font-semibold text-[var(--accent)]" href={`tel:${spec.helpline}`}>{spec.helpline}</a></p>}

      {loading && (
        <p className="mt-4 text-sm text-[var(--ink-muted)]" role="status">
          {hasLocation ? "Finding the office near you and checking official websites for its contact details…" : "Looking up the office…"}
        </p>
      )}
      {error && <p className="mt-4 text-sm text-[var(--warn)]" role="alert">{error}</p>}

      {data && !loading && (
        <div className="mt-4 grid gap-5">
          {data.offices.length > 0 && (
            <fieldset>
              <legend className="text-sm font-semibold">Official contact</legend>
              <ul className="mt-2 space-y-2">
                {data.offices.map((office, index) => {
                  const selected = choice?.source === "office" && choice.index === index;
                  return (
                    <li key={`${office.name}-${index}`} className={`rounded-lg border p-3 ${selected ? "border-[var(--accent)]" : "border-[var(--line)]"}`}>
                      <label className="flex cursor-pointer items-start gap-3">
                        <input type="radio" name={`office-${kind}`} checked={selected} onChange={() => {
                          setChoice({ source: "office", index });
                          setEmails(office.emails.filter((e) => e.verified).map((e) => e.address));
                        }} className="mt-1 h-4 w-4 accent-[var(--accent)]" />
                        <span className="min-w-0 flex-1">
                          <span className="block text-sm font-semibold">{office.name}</span>
                          {office.designation && <span className="block text-xs text-[var(--ink-muted)]">{office.designation}</span>}
                          {office.address && <span className="mt-1 block text-sm">{office.address}</span>}
                          {office.phone && <span className="mt-1 block text-sm">Phone: {office.phone}</span>}
                          {office.notes && <span className="mt-1 block text-xs leading-5 text-[var(--ink-muted)]">{office.notes}</span>}
                          <span className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
                            <ExternalLink href={office.portal_url}>{spec?.portal_label || "Official portal"}</ExternalLink>
                            <ExternalLink href={office.website}>Website</ExternalLink>
                            <ExternalLink href={office.source_url}>Source</ExternalLink>
                          </span>
                          <span className="mt-1 block text-xs text-[var(--ink-muted)]">{SOURCE_LABEL[office.source] ?? office.source}</span>
                        </span>
                      </label>
                    </li>
                  );
                })}
              </ul>
            </fieldset>
          )}

          {data.nearby.length > 0 && (
            <fieldset>
              <legend className="text-sm font-semibold">Nearest {kind === "police_station" ? "police stations" : "courts"}</legend>
              {kind === "police_station" && (
                <p className="mt-1 text-xs text-[var(--ink-muted)]">The nearest station may not be the one with jurisdiction. Any station must register a Zero FIR and transfer it (Section 173(1) BNSS).</p>
              )}
              <ul className="mt-2 grid gap-2 sm:grid-cols-2">
                {data.nearby.map((place, index) => {
                  const selected = choice?.source === "nearby" && choice.index === index;
                  return (
                    <li key={place.id} className={`rounded-lg border p-3 ${selected ? "border-[var(--accent)]" : "border-[var(--line)]"}`}>
                      <label className="flex cursor-pointer items-start gap-3">
                        <input type="radio" name={`office-${kind}`} checked={selected} onChange={() => setChoice({ source: "nearby", index })} className="mt-1 h-4 w-4 accent-[var(--accent)]" />
                        <span className="min-w-0 flex-1">
                          <span className="flex items-start justify-between gap-2">
                            <span className="text-sm font-semibold">{place.name}</span>
                            <span className="shrink-0 text-xs text-[var(--ink-muted)]">{place.distance_km.toFixed(1)} km</span>
                          </span>
                          {place.kind_hint && <span className="block text-xs text-[var(--ink-muted)]">{place.kind_hint}</span>}
                          {place.address && <span className="mt-1 block text-xs">{place.address}</span>}
                          {place.phone && <a className="mt-1 block text-xs text-[var(--accent)]" href={`tel:${place.phone}`}>{place.phone}</a>}
                          <a className="mt-1 inline-flex items-center gap-1 text-xs text-[var(--accent)] underline-offset-2 hover:underline" target="_blank" rel="noreferrer"
                            href={`https://www.openstreetmap.org/?mlat=${place.latitude}&mlon=${place.longitude}#map=17/${place.latitude}/${place.longitude}`}>
                            <PinIcon className="h-3.5 w-3.5" /> Map
                          </a>
                        </span>
                      </label>
                      {selected && kind === "police_station" && (
                        <button type="button" onClick={() => void load({ officeName: place.name })} className="btn-secondary btn-sm mt-2">
                          Find this station&rsquo;s email
                        </button>
                      )}
                    </li>
                  );
                })}
              </ul>
              <label className="mt-2 inline-flex items-center gap-2 text-xs text-[var(--ink-muted)]">Search radius
                <select value={radiusKm} onChange={(e) => { const r = Number(e.target.value); setRadiusKm(r); void load({ radius: r }); }}
                  className="h-9 rounded-sm border border-[var(--line)] bg-[var(--surface)] px-2 text-xs">
                  {[5, 10, 25, 50].map((r) => <option key={r} value={r}>{r} km</option>)}
                </select>
              </label>
            </fieldset>
          )}

          {data.notes.map((note) => <p key={note} className="text-sm text-[var(--ink-muted)]">{note}</p>)}

          {spec?.channel !== "portal" && (
            <fieldset>
              <legend className="text-sm font-semibold">Send to (email)</legend>
              {allEmails.length === 0 ? (
                <p className="mt-1 text-sm text-[var(--ink-muted)]">No verified email yet. Add one you know, or leave it empty to print the document.</p>
              ) : (
                <ul className="mt-2 flex flex-wrap gap-2">
                  {allEmails.map((address) => (
                    <li key={address}>
                      <label className="inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-full border border-[var(--line)] px-3 text-sm">
                        <input type="checkbox" checked={emails.includes(address)} onChange={(e) => toggleEmail(address, e.target.checked)} className="h-4 w-4 accent-[var(--accent)]" />
                        {address}
                      </label>
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-2 flex max-w-md gap-2">
                <label className="sr-only" htmlFor={`manual-email-${kind}`}>Add an email address</label>
                <input id={`manual-email-${kind}`} value={manualEmail} onChange={(e) => setManualEmail(e.target.value)} type="email" placeholder="Add an email address"
                  onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addManual(); } }}
                  className="h-10 flex-1 rounded-sm border border-[var(--line)] bg-[var(--surface)] px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)]" />
                <button type="button" onClick={addManual} className="btn-secondary btn-sm">Add</button>
              </div>
            </fieldset>
          )}

          <label className="text-sm font-medium">Anything the draft should include or stress (optional)
            <textarea value={instructions} onChange={(e) => setInstructions(e.target.value)} rows={2} maxLength={2000}
              placeholder="e.g. Mention that I already complained at the station on 5 October."
              className="mt-1 w-full rounded-sm border border-[var(--line)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)]" />
          </label>

          {!complainantReady && <p className="text-sm text-[var(--caution)]">Add your name and address in step 1 so they appear in the document.</p>}

          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => void draft()} disabled={drafting} className="btn-primary">
              {drafting ? "Drafting…" : spec?.forum === "court" ? "Draft the petition" : "Write the complaint"}
            </button>
            <button type="button" onClick={() => void load({ refresh: true })} disabled={loading} className="btn-secondary btn-sm">Search official sites again</button>
            {drafting && <span className="text-sm text-[var(--ink-muted)]" role="status">Writing the document from your facts and the statute text…</span>}
          </div>
        </div>
      )}
    </div>
  );
}
