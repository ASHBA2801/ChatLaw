"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { CheckIcon, CopyIcon, DownloadIcon, ExternalIcon, MailIcon, PrintIcon } from "@/components/filings/FilingIcons";
import { cleanAddresses, composeUrl, isEmail, type MailClient } from "@/lib/filings/mail";
import { FILING_STATUSES, kindLabel, type FilingStatus } from "@/lib/filings/types";
import { isSafeExternalUrl } from "@/lib/urls/safeUrl";

export type FilingView = {
  id: string;
  caseId: string;
  kind: string;
  forum: string;
  title: string;
  subject: string;
  body: string;
  emailBody: string;
  to: string[];
  cc: string[];
  status: FilingStatus;
  warnings: string[];
  placeholders: string[];
  citations: Array<{ id: number; label: string; act_title: string; law_key: string; source_url: string | null }>;
  filing: {
    channel?: string;
    portal_url?: string | null;
    portal_label?: string | null;
    helpline?: string | null;
    caveat?: string | null;
    notes?: string | null;
    disclaimer?: string | null;
  };
  recipientName: string | null;
  language: string;
  createdAt: string;
};

const STATUS_LABEL: Record<FilingStatus, string> = { DRAFT: "Draft", FINAL: "Final — ready to file", SENT: "Sent by email", FILED: "Filed / handed in" };
const FIELD = "h-10 w-full rounded-sm border border-[var(--line)] bg-[var(--surface)] px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)]";

function AddressInput({ id, label, values, onChange }: { id: string; label: string; values: string[]; onChange: (next: string[]) => void }) {
  const [draft, setDraft] = useState("");
  function add() {
    const next = cleanAddresses([...values, draft]);
    if (isEmail(draft)) setDraft("");
    onChange(next);
  }
  return (
    <div>
      <label htmlFor={id} className="text-xs font-semibold text-[var(--ink-muted)]">{label}</label>
      <div className="mt-1 flex flex-wrap items-center gap-1.5">
        {values.map((value) => (
          <span key={value} className="inline-flex items-center gap-1 rounded-full bg-[var(--fill)] py-1 pl-3 pr-1 text-sm">
            {value}
            <button type="button" onClick={() => onChange(values.filter((v) => v !== value))} className="inline-flex h-7 w-7 items-center justify-center rounded-full text-[var(--ink-muted)] hover:bg-[var(--line)]" aria-label={`Remove ${value}`}>×</button>
          </span>
        ))}
        <input id={id} value={draft} onChange={(e) => setDraft(e.target.value)} onBlur={() => draft && add()}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); add(); } }}
          placeholder={values.length ? "Add another" : "name@office.gov.in"} type="email"
          className="h-10 min-w-[12rem] flex-1 rounded-sm border border-[var(--line)] bg-[var(--surface)] px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)]" />
      </div>
    </div>
  );
}

export default function FilingDocument({ filing }: { filing: FilingView }) {
  const router = useRouter();
  const [body, setBody] = useState(filing.body);
  const [subject, setSubject] = useState(filing.subject);
  const [coverNote, setCoverNote] = useState(filing.emailBody);
  const [to, setTo] = useState(filing.to);
  const [cc, setCc] = useState(filing.cc);
  const [status, setStatus] = useState<FilingStatus>(filing.status);
  const [editing, setEditing] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [opened, setOpened] = useState<MailClient | null>(null);

  const placeholders = useMemo(() => [...new Set(body.match(/\[[A-Z][A-Z0-9 ,./'&()-]{2,80}\]/g) ?? [])], [body]);
  const isPortal = filing.filing.channel === "portal";
  const isCourt = filing.forum === "court";
  const portalUrl = isSafeExternalUrl(filing.filing.portal_url);

  async function save(extra: Record<string, unknown> = {}) {
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(`/api/cases/${filing.caseId}/filings/${filing.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body, subject, emailBody: coverNote, to, cc, ...extra }),
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error(payload?.error || "The document could not be saved.");
      setDirty(false);
      setMessage("Saved.");
      router.refresh();
      return true;
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : "The document could not be saved.");
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(next: FilingStatus) {
    const previous = status;
    setStatus(next);
    if (!(await save({ status: next }))) setStatus(previous);
  }

  async function copyText() {
    try {
      await navigator.clipboard.writeText(body);
      setMessage("The complete document is copied. Paste it into the email or portal.");
    } catch {
      setError("Copying is blocked in this browser. Select the text and copy it instead.");
    }
  }

  function openMail(client: MailClient) {
    const fullBody = `${coverNote.trim()}\n\n${"-".repeat(40)}\n\n${body}`;
    const { url, truncated } = composeUrl(client, { to, cc, subject, fullBody, coverNote });
    if (dirty) void save();
    setOpened(client);
    setMessage(truncated
      ? "The document is too long for an email link, so the email has the covering note only. Download the Word file or print to PDF and attach it before sending."
      : "Your mail app has the email ready. Check it and press Send — ChatLaw does not send anything.");
    if (client === "default") window.location.href = url;
    else window.open(url, "_blank", "noopener,noreferrer");
  }

  async function remove() {
    if (!window.confirm("Delete this document? This cannot be undone.")) return;
    const response = await fetch(`/api/cases/${filing.caseId}/filings/${filing.id}`, { method: "DELETE" });
    if (response.ok) router.push(`/cases/${filing.caseId}`);
    else setError("The document could not be deleted.");
  }

  return (
    <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2 print:hidden">
          <button type="button" onClick={() => window.print()} className="btn-primary btn-sm"><PrintIcon className="h-4 w-4" /> Print</button>
          <a href={`/api/cases/${filing.caseId}/filings/${filing.id}/export`} className="btn-secondary btn-sm" onClick={() => dirty && void save()}>
            <DownloadIcon className="h-4 w-4" /> Word (.docx)
          </a>
          <button type="button" onClick={() => void copyText()} className="btn-secondary btn-sm"><CopyIcon className="h-4 w-4" /> Copy text</button>
          <button type="button" onClick={() => setEditing((v) => !v)} className="btn-secondary btn-sm" aria-pressed={editing}>{editing ? "Done editing" : "Edit text"}</button>
          {dirty && <button type="button" onClick={() => void save()} disabled={saving} className="btn-secondary btn-sm">{saving ? "Saving…" : "Save changes"}</button>}
        </div>
        <p className="mt-2 text-xs text-[var(--ink-muted)] print:hidden">To save as PDF, choose Print and then &ldquo;Save as PDF&rdquo;.</p>

        {placeholders.length > 0 && (
          <div className="mt-4 rounded-lg border border-[var(--caution-line)] bg-[var(--caution-bg)] p-3 text-sm text-[var(--caution)] print:hidden" role="note">
            <p className="font-semibold">Fill in {placeholders.length} missing detail{placeholders.length === 1 ? "" : "s"} before filing</p>
            <p className="mt-1">{placeholders.join(" · ")}</p>
            <p className="mt-1 text-xs">Use &ldquo;Edit text&rdquo; to replace them, or add the facts to the case and draft again.</p>
          </div>
        )}

        {editing ? (
          <label className="mt-4 block print:hidden">
            <span className="sr-only">Document text</span>
            <textarea value={body} onChange={(e) => { setBody(e.target.value); setDirty(true); }} rows={32}
              className="filing-sheet w-full rounded-lg border border-[var(--line-strong)] bg-[var(--surface)] p-4 text-[15px] leading-7 outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)]" />
          </label>
        ) : null}
        <article
          lang={filing.language}
          className={`filing-sheet filing-print-root mx-auto mt-4 max-w-[794px] rounded-lg border border-[var(--line)] bg-white p-6 text-[15px] leading-7 text-neutral-900 shadow-sm sm:p-12 ${editing ? "hidden print:block" : ""}`}
        >
          {body}
          {filing.filing.disclaimer && (
            <p style={{ fontFamily: "var(--font-ui)" }} className="mt-10 border-t border-neutral-200 pt-3 text-[11px] leading-5 text-neutral-500 print:hidden">{filing.filing.disclaimer}</p>
          )}
        </article>
      </div>

      <aside className="space-y-5 print:hidden">
        <section className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4">
          <h2 className="text-base font-semibold">{isCourt ? "File it" : isPortal ? "Lodge it" : "Send it"}</h2>
          <p className="mt-1 text-xs leading-5 text-[var(--ink-muted)]">
            {isCourt
              ? "Court documents are filed in person or on the e-filing portal, usually through an advocate. Print it, or email it to your advocate."
              : isPortal
                ? "This office takes complaints on its portal. Copy the text, open the portal and paste it in; attach the printed PDF if asked."
                : "ChatLaw opens your own mail app with everything filled in. Nothing is sent until you press Send."}
          </p>

          {portalUrl && (
            <a href={portalUrl} target="_blank" rel="noreferrer" className={`${isPortal || isCourt ? "btn-primary" : "btn-secondary"} btn-sm mt-3 w-full`}>
              {filing.filing.portal_label || "Open the official portal"} <ExternalIcon className="h-4 w-4" />
            </a>
          )}
          {filing.filing.helpline && (
            <p className="mt-2 text-sm">Helpline: <a className="font-semibold text-[var(--accent)]" href={`tel:${filing.filing.helpline}`}>{filing.filing.helpline}</a></p>
          )}

          <div className="mt-4 space-y-3 border-t border-[var(--line)] pt-4">
            <AddressInput id="filing-to" label="To" values={to} onChange={(next) => { setTo(next); setDirty(true); }} />
            <AddressInput id="filing-cc" label="Cc (optional)" values={cc} onChange={(next) => { setCc(next); setDirty(true); }} />
            <label className="block text-xs font-semibold text-[var(--ink-muted)]">Subject
              <input value={subject} onChange={(e) => { setSubject(e.target.value); setDirty(true); }} className={`${FIELD} mt-1 font-normal text-[var(--foreground)]`} maxLength={600} />
            </label>
            <label className="block text-xs font-semibold text-[var(--ink-muted)]">Covering note
              <textarea value={coverNote} onChange={(e) => { setCoverNote(e.target.value); setDirty(true); }} rows={5}
                className="mt-1 w-full rounded-sm border border-[var(--line)] bg-[var(--surface)] px-3 py-2 text-sm font-normal text-[var(--foreground)] outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus)]" />
            </label>
            {!to.length && !isCourt && !isPortal && <p className="text-xs text-[var(--caution)]">Add the office&rsquo;s email address in To.</p>}
            <div className="grid gap-2">
              <button type="button" onClick={() => openMail("gmail")} className={`${isPortal || isCourt ? "btn-secondary" : "btn-primary"} btn-sm`}>
                <MailIcon className="h-4 w-4" /> Open in Gmail
              </button>
              <div className="grid grid-cols-2 gap-2">
                <button type="button" onClick={() => openMail("outlook")} className="btn-secondary btn-sm">Outlook</button>
                <button type="button" onClick={() => openMail("default")} className="btn-secondary btn-sm">Mail app</button>
              </div>
            </div>
            {opened && status !== "SENT" && (
              <button type="button" onClick={() => void changeStatus("SENT")} className="btn-secondary btn-sm w-full">
                <CheckIcon className="h-4 w-4" /> I sent it — mark as sent
              </button>
            )}
          </div>
          <div aria-live="polite" className="mt-3">
            {message && <p className="text-sm text-[var(--ink-muted)]" role="status">{message}</p>}
            {error && <p className="text-sm text-[var(--warn)]" role="alert">{error}</p>}
          </div>
        </section>

        <section className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4">
          <label className="block text-sm font-semibold">Status
            <select value={status} onChange={(e) => void changeStatus(e.target.value as FilingStatus)} className={`${FIELD} mt-1 font-normal`}>
              {FILING_STATUSES.map((value) => <option key={value} value={value}>{STATUS_LABEL[value]}</option>)}
            </select>
          </label>
          <p className="mt-3 text-xs text-[var(--ink-muted)]">{kindLabel(filing.kind)}{filing.recipientName ? ` · ${filing.recipientName}` : ""}</p>
          {filing.filing.caveat && <p className="mt-3 text-xs leading-5 text-[var(--caution)]">{filing.filing.caveat}</p>}
          {filing.filing.notes && (
            <div className="mt-3 border-t border-[var(--line)] pt-3">
              <p className="text-xs font-semibold text-[var(--ink-muted)]">Filing notes</p>
              <p className="mt-1 text-xs leading-5">{filing.filing.notes}</p>
            </div>
          )}
        </section>

        {(filing.citations.length > 0 || filing.warnings.length > 0) && (
          <section className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4">
            {filing.citations.length > 0 && (
              <>
                <h2 className="text-sm font-semibold">Law cited (checked against the statute text)</h2>
                <ul className="mt-2 space-y-1 text-sm">
                  {filing.citations.map((c) => (
                    <li key={c.law_key}><Link className="text-[var(--accent)] underline-offset-2 hover:underline" href={`/research?q=${encodeURIComponent(c.label)}`}>{c.label}</Link></li>
                  ))}
                </ul>
              </>
            )}
            {filing.warnings.length > 0 && (
              <>
                <h2 className={`text-sm font-semibold ${filing.citations.length ? "mt-4" : ""}`}>Check before filing</h2>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-xs leading-5 text-[var(--ink-muted)]">
                  {filing.warnings.map((w) => <li key={w}>{w}</li>)}
                </ul>
              </>
            )}
          </section>
        )}

        <div className="flex flex-wrap gap-2">
          <Link href={`/cases/${filing.caseId}`} className="btn-secondary btn-sm">Back to case</Link>
          <button type="button" onClick={() => void remove()} className="min-h-10 px-2 text-sm text-[var(--warn)] underline">Delete</button>
        </div>
      </aside>
    </div>
  );
}
