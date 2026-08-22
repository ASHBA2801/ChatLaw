"use client";

import { DragEvent, FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import CaseIntelligencePanel from "@/components/case-intelligence/CaseIntelligencePanel";
import CaseAssistant from "@/components/cases/CaseAssistant";
import { CASE_STATUSES } from "@/lib/cases/status";

const FIELD =
  "mt-1 h-11 w-full rounded-lg border border-[var(--line)] px-3 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]";
const AREA =
  "mt-1 w-full rounded-lg border border-[var(--line)] px-3 py-2 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]";

type PublicDocument = {
  id: string;
  fileName: string;
  fileSize: number;
  pageCount: number | null;
  extractedTextStatus: string;
  createdAt: string;
  hasExtractedText: boolean;
  detectedDates: unknown[];
  detectedHeadings: unknown[];
  extractionError: string | null;
  summary: string | null;
  summaryLabel: string | null;
};

type TimelineEvent = { id: string; title: string; description?: string | null; occurredAt: string };
type ImportantDate = { id: string; title: string; date: string; description: string | null; reminderPreference?: string | null };

type CaseItem = {
  id: string;
  title: string;
  description: string | null;
  category: string | null;
  subCategory: string | null;
  jurisdiction: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  status: string;
  documents: PublicDocument[];
  timeline: TimelineEvent[];
  importantDates: ImportantDate[];
};

function statusLabel(status: string) {
  if (status === "PROCESSING") return "Processing";
  if (status === "READY") return "Ready";
  if (status === "FAILED") return "Failed";
  if (status === "PENDING") return "Uploading";
  return status;
}

export default function CaseDetail({ item }: { item: CaseItem }) {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [documents, setDocuments] = useState(item.documents);
  const [dates, setDates] = useState(item.importantDates);
  const [timeline, setTimeline] = useState(item.timeline);
  const [overview, setOverview] = useState({
    title: item.title,
    description: item.description || "",
    category: item.category || "",
    subCategory: item.subCategory || "",
    status: item.status,
    city: item.city || "",
    state: item.state || "",
    country: item.country || "",
  });
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState<{
    document: PublicDocument;
    extractedText: string | null;
    blobUrl: string | null;
  } | null>(null);
  const [summarizingId, setSummarizingId] = useState<string | null>(null);
  const [note, setNote] = useState({ title: "", description: "" });
  const [dateForm, setDateForm] = useState({ title: "", date: "", description: "", reminderPreference: "none" });

  useEffect(() => () => {
    if (preview?.blobUrl) URL.revokeObjectURL(preview.blobUrl);
  }, [preview]);

  useEffect(() => {
    if (!preview) return;
    function onKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") setPreview(null);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [preview]);

  async function upload(file: File) {
    setUploading(true);
    setError("");
    setMessage("Uploading...");
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(`/api/cases/${item.id}/documents`, { method: "POST", body: form });
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.error || "Upload failed.");
      setMessage("");
    } else {
      setDocuments((current) => [payload.document, ...current]);
      setMessage(payload.document.extractedTextStatus === "READY" ? "Document ready." : "Document uploaded. Processing finished with a saved status.");
      router.refresh();
    }
    setUploading(false);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file) void upload(file);
  }

  function onDropZoneKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      input.current?.click();
    }
  }

  function shortName(name: string) {
    if (name.length <= 48) return name;
    const extension = name.includes(".") ? name.slice(name.lastIndexOf(".")) : "";
    return `${name.slice(0, 40)}…${extension}`;
  }

  async function remove(documentId: string) {
    if (!window.confirm("Delete this document from the case?")) return;
    const response = await fetch(`/api/cases/${item.id}/documents`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ documentId }),
    });
    if (response.ok) {
      setDocuments((current) => current.filter((doc) => doc.id !== documentId));
      setPreview(null);
    } else {
      setError("The document could not be deleted.");
    }
  }

  async function retry(documentId: string) {
    const response = await fetch(`/api/cases/${item.id}/documents/${documentId}/retry`, { method: "POST" });
    const payload = await response.json();
    if (response.ok) {
      setDocuments((current) => current.map((doc) => doc.id === documentId ? payload.document : doc));
    } else {
      setError(payload.error || "Retry failed.");
    }
  }

  async function summarize(documentId: string) {
    setSummarizingId(documentId);
    setError("");
    const response = await fetch(`/api/cases/${item.id}/documents/${documentId}/summarize`, { method: "POST" });
    const payload = await response.json();
    if (response.ok) {
      setDocuments((current) => current.map((doc) => doc.id === documentId ? payload.document : doc));
    } else {
      setError(payload.error || "Summary failed.");
    }
    setSummarizingId(null);
  }

  async function openPreview(document: PublicDocument) {
    if (preview?.blobUrl) URL.revokeObjectURL(preview.blobUrl);
    const [metaResponse, fileResponse] = await Promise.all([
      fetch(`/api/cases/${item.id}/documents/${document.id}`),
      fetch(`/api/cases/${item.id}/documents/${document.id}/download`),
    ]);
    if (!metaResponse.ok) {
      setError("The document could not be opened.");
      return;
    }
    const payload = await metaResponse.json();
    let blobUrl: string | null = null;
    if (fileResponse.ok) {
      blobUrl = URL.createObjectURL(await fileResponse.blob());
    }
    setPreview({
      document: payload.document,
      extractedText: payload.document.extractedText ?? null,
      blobUrl,
    });
  }

  async function saveOverview(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const response = await fetch(`/api/cases/${item.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(overview),
    });
    const payload = await response.json();
    if (!response.ok) setError(payload.error || "The case could not be updated.");
    else router.refresh();
    setSaving(false);
  }

  async function archiveCase() {
    if (!window.confirm("Archive this case? It will remain in your workspace as archived.")) return;
    const response = await fetch(`/api/cases/${item.id}`, { method: "DELETE" });
    if (response.ok) router.push("/cases");
    else setError("The case could not be archived.");
  }

  async function addDate(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(`/api/cases/${item.id}/dates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dateForm),
    });
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.error || "The date could not be added.");
      return;
    }
    setDates((current) => [...current, payload.date].sort((left, right) => left.date.localeCompare(right.date)));
    setDateForm({ title: "", date: "", description: "", reminderPreference: "none" });
    router.refresh();
  }

  async function removeDate(dateId: string) {
    const response = await fetch(`/api/cases/${item.id}/dates/${dateId}`, { method: "DELETE" });
    if (response.ok) setDates((current) => current.filter((itemDate) => itemDate.id !== dateId));
  }

  async function addNote(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(`/api/cases/${item.id}/timeline`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(note),
    });
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.error || "The note could not be added.");
      return;
    }
    setTimeline((current) => [payload.event, ...current]);
    setNote({ title: "", description: "" });
  }

  const intelligenceQuery = [item.title, item.description, item.category].filter(Boolean).join(". ");
  const defaultLocation = [item.city, item.state, item.country || "India"].filter(Boolean).join(", ");

  return (
    <div className="mt-8 grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
      <div className="space-y-6">
        <section className="rounded-2xl border border-[var(--line)] bg-white p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <h2 className="text-lg font-semibold">Overview</h2>
            <span className="rounded-full bg-[#eef5d0] px-3 py-1 text-xs font-semibold text-[var(--forest)]">{overview.status.replace("_", " ")}</span>
          </div>
          <form onSubmit={saveOverview} className="mt-4 grid gap-3">
            <label className="text-sm font-medium">Title
              <input value={overview.title} onChange={(event) => setOverview((current) => ({ ...current, title: event.target.value }))} className={FIELD} maxLength={200} />
            </label>
            <label className="text-sm font-medium">Case description
              <textarea value={overview.description} onChange={(event) => setOverview((current) => ({ ...current, description: event.target.value }))} rows={4} className={AREA} maxLength={4000} />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm font-medium">Category
                <input value={overview.category} onChange={(event) => setOverview((current) => ({ ...current, category: event.target.value }))} className={FIELD} maxLength={120} />
              </label>
              <label className="text-sm font-medium">Status
                <select value={overview.status} onChange={(event) => setOverview((current) => ({ ...current, status: event.target.value }))} className={FIELD}>
                  {CASE_STATUSES.map((status) => <option key={status} value={status}>{status.replace("_", " ")}</option>)}
                </select>
              </label>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="submit" disabled={saving} className="min-h-11 rounded-lg bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Saving..." : "Save changes"}</button>
              <button type="button" onClick={() => void archiveCase()} className="min-h-11 rounded-lg border border-[var(--line)] px-4 text-sm font-medium">Archive case</button>
              <Link href={`/chat?caseId=${item.id}`} className="inline-flex min-h-11 items-center rounded-lg border border-[var(--line)] px-4 text-sm font-medium text-[var(--forest)]">
                Open full chat
              </Link>
            </div>
          </form>
        </section>

        <section className="rounded-2xl border border-[var(--line)] bg-white p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Documents</h2>
              <p className="mt-1 text-sm text-[var(--ink-muted)]">Private PDFs associated with this case.</p>
            </div>
            <button type="button" onClick={() => input.current?.click()} disabled={uploading} className="min-h-10 rounded-lg bg-[var(--forest)] px-4 text-sm font-semibold text-white">
              {uploading ? "Uploading..." : "Upload Document"}
            </button>
            <input ref={input} type="file" accept="application/pdf,.pdf" className="sr-only" onChange={(event) => { const file = event.target.files?.[0]; if (file) void upload(file); event.currentTarget.value = ""; }} />
          </div>
          <div
            role="button"
            tabIndex={0}
            aria-label="Upload a PDF document"
            onDragOver={(event) => { event.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onKeyDown={onDropZoneKeyDown}
            className={`mt-4 rounded-xl border border-dashed px-4 py-6 text-center text-sm transition-colors duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)] ${dragOver ? "border-[var(--forest)] bg-[#eef5d0]" : "border-[var(--line)] text-[var(--ink-muted)]"}`}
          >
            Drag & drop a PDF here, or press Enter to choose a file.
          </div>
          <div aria-live="polite">
            {message && <p className="mt-4 rounded-lg bg-[#eef5d0] p-3 text-sm" role="status">{message}</p>}
            {error && <p className="mt-4 text-sm text-[#935a1e]" role="alert">{error}</p>}
          </div>
          {documents.length === 0 ? (
            <div className="mt-5 rounded-xl border border-dashed border-[var(--line)] p-5 text-center">
              <p className="text-sm text-[var(--ink-muted)]">No documents have been added to this case yet.</p>
              <button type="button" onClick={() => input.current?.click()} disabled={uploading} className="mt-4 min-h-11 rounded-lg bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-50">
                Upload Document
              </button>
            </div>
          ) : (
            <ul className="mt-5 divide-y divide-[var(--line)]">
              {documents.map((doc) => (
                <li key={doc.id} className="flex flex-wrap items-start justify-between gap-3 py-4 first:pt-0">
                  <div className="min-w-0">
                    <p className="truncate font-medium" title={doc.fileName}>{shortName(doc.fileName)}</p>
                    <p className="mt-1 text-xs text-[var(--ink-muted)]">
                      {(doc.fileSize / 1024).toFixed(0)} KB · {doc.pageCount ?? "?"} pages · {statusLabel(doc.extractedTextStatus)}
                    </p>
                    {(doc.extractedTextStatus === "PROCESSING" || doc.extractedTextStatus === "PENDING") && (
                      <div className="mt-2 h-2 w-40 max-w-full overflow-hidden rounded-full bg-[var(--line)]" role="progressbar" aria-valuetext="Processing document" aria-label="Processing document">
                        <div className="h-full w-2/3 bg-[var(--forest)] transition-all duration-200" />
                      </div>
                    )}
                    {doc.extractionError && doc.extractedTextStatus === "FAILED" && (
                      <p className="mt-2 text-xs text-[#935a1e]">{doc.extractionError}</p>
                    )}
                    {doc.summary && (
                      <p className="mt-2 max-w-xl text-xs text-[var(--ink-muted)]">
                        <span className="font-semibold text-[var(--foreground)]">{doc.summaryLabel || "AI-generated summary"}</span>
                        {" — "}
                        {doc.summary.slice(0, 180)}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button type="button" onClick={() => void openPreview(doc)} className="min-h-11 rounded-lg border border-[var(--line)] px-3 text-sm">View</button>
                    <a className="inline-flex min-h-11 items-center rounded-lg border border-[var(--line)] px-3 text-sm" href={`/api/cases/${item.id}/documents/${doc.id}/download`}>Download</a>
                    {doc.extractedTextStatus === "READY" && (
                      <button type="button" onClick={() => void summarize(doc.id)} disabled={summarizingId === doc.id} className="min-h-11 rounded-lg border border-[var(--forest)] px-3 text-sm font-medium text-[var(--forest)] disabled:opacity-50">
                        {summarizingId === doc.id ? "Summarizing..." : "Summarize Document"}
                      </button>
                    )}
                    {doc.extractedTextStatus === "FAILED" && (
                      <button type="button" onClick={() => void retry(doc.id)} className="min-h-11 rounded-lg border border-[var(--line)] px-3 text-sm">Retry</button>
                    )}
                    <button type="button" onClick={() => void remove(doc.id)} className="min-h-11 text-sm text-[#935a1e] underline">Delete</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <CaseAssistant caseId={item.id} />
      </div>

      <aside className="space-y-6">
        <section className="rounded-2xl border border-[var(--line)] bg-white p-5">
          <h2 className="text-lg font-semibold">Timeline</h2>
          {timeline.length === 0 ? (
            <p className="mt-4 rounded-xl border border-dashed border-[var(--line)] p-4 text-sm text-[var(--ink-muted)]">
              No timeline events yet. Uploads and notes appear here automatically.
            </p>
          ) : (
            <ol className="mt-4 space-y-4">
              {timeline.map((event) => (
                <li key={event.id} className="border-l border-[var(--line)] pl-4">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">{new Date(event.occurredAt).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</p>
                  <p className="mt-1 text-sm font-medium">{event.title}</p>
                  {event.description && <p className="mt-1 text-xs text-[var(--ink-muted)]">{event.description}</p>}
                </li>
              ))}
            </ol>
          )}
          <form onSubmit={addNote} className="mt-4 space-y-2">
            <label className="text-sm font-medium">Add a note
              <input value={note.title} onChange={(event) => setNote((current) => ({ ...current, title: event.target.value }))} placeholder="Note title" className={FIELD} maxLength={200} />
            </label>
            <label className="sr-only" htmlFor={`case-note-${item.id}`}>Note details</label>
            <textarea id={`case-note-${item.id}`} value={note.description} onChange={(event) => setNote((current) => ({ ...current, description: event.target.value }))} placeholder="Optional details" rows={2} className={`${AREA} text-sm`} maxLength={2000} />
            <button type="submit" disabled={!note.title.trim()} className="min-h-11 rounded-lg border border-[var(--forest)] px-3 text-sm font-semibold text-[var(--forest)] disabled:opacity-50">Add note</button>
          </form>
        </section>

        <section className="rounded-2xl border border-[var(--line)] bg-white p-5">
          <h2 className="text-lg font-semibold">Important dates</h2>
          {dates.length === 0 ? (
            <p className="mt-4 rounded-xl border border-dashed border-[var(--line)] p-4 text-sm text-[var(--ink-muted)]">
              No important dates have been added. Track court dates, notices, and deadlines here.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {dates.map((entry) => (
                <li key={entry.id} className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium">{entry.title}</p>
                    <p className="text-xs text-[var(--ink-muted)]">{new Date(entry.date).toLocaleDateString("en-IN")}{entry.reminderPreference && entry.reminderPreference !== "none" ? ` · reminder: ${entry.reminderPreference.replace("_", " ")}` : ""}</p>
                    {entry.description && <p className="mt-1 text-xs text-[var(--ink-muted)]">{entry.description}</p>}
                  </div>
                  <button type="button" onClick={() => void removeDate(entry.id)} className="text-sm text-[#935a1e] underline">Remove</button>
                </li>
              ))}
            </ul>
          )}
          <form onSubmit={addDate} className="mt-4 space-y-2">
            <label className="block text-sm font-medium">Title
              <input value={dateForm.title} onChange={(event) => setDateForm((current) => ({ ...current, title: event.target.value }))} placeholder="Court date, notice, deadline..." className={`${FIELD} text-sm`} required maxLength={200} />
            </label>
            <label className="block text-sm font-medium">Date
              <input type="date" value={dateForm.date} onChange={(event) => setDateForm((current) => ({ ...current, date: event.target.value }))} className={`${FIELD} text-sm`} required />
            </label>
            <label className="block text-sm font-medium">Reminder preference
              <select value={dateForm.reminderPreference} onChange={(event) => setDateForm((current) => ({ ...current, reminderPreference: event.target.value }))} className={`${FIELD} text-sm`}>
                <option value="none">No reminder</option>
                <option value="day_of">Remind on the day</option>
                <option value="day_before">Remind the day before</option>
              </select>
            </label>
            <button type="submit" className="min-h-11 rounded-lg border border-[var(--forest)] px-3 text-sm font-semibold text-[var(--forest)]">Add date</button>
            <p className="text-xs text-[var(--ink-muted)]">Reminder preference is stored only. Notifications are not sent yet.</p>
          </form>
        </section>

        <section className="rounded-2xl border border-[var(--line)] bg-white p-5">
          <h2 className="text-lg font-semibold">Legal resources</h2>
          <p className="mt-2 text-sm text-[var(--ink-muted)]">Find potentially relevant courts and nearby advocates using the existing case intelligence tools.</p>
          <CaseIntelligencePanel query={intelligenceQuery} defaultLocation={defaultLocation} defaultPracticeArea={item.category || ""} />
        </section>
      </aside>

      {preview && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/30" role="dialog" aria-modal="true" aria-label="Document preview">
          <button type="button" className="flex-1" onClick={() => setPreview(null)} aria-label="Close document preview" />
          <div className="flex h-full w-full max-w-xl flex-col overflow-y-auto border-l border-[var(--line)] bg-white p-5">
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-base font-semibold">{preview.document.fileName}</h3>
              <button type="button" onClick={() => setPreview(null)} className="min-h-11 min-w-11 rounded-lg border border-[var(--line)]" aria-label="Close document preview">✕</button>
            </div>
            <p className="mt-2 text-sm text-[var(--ink-muted)]">
              {preview.document.pageCount ?? "?"} pages · {statusLabel(preview.document.extractedTextStatus)}
            </p>
            {preview.document.extractedTextStatus === "FAILED" && (
              <p className="mt-3 text-sm text-[#935a1e]">{preview.document.extractionError || "Text extraction failed."}</p>
            )}
            {preview.document.extractedTextStatus === "PROCESSING" && (
              <p className="mt-3 text-sm text-[var(--ink-muted)]">Processing document...</p>
            )}
            {preview.document.summary && (
              <div className="mt-4 rounded-lg border border-[var(--line)] bg-[var(--background)] p-3 text-sm">
                <p className="font-semibold">{preview.document.summaryLabel || "AI-generated summary"}</p>
                <p className="mt-2 whitespace-pre-wrap text-[var(--ink-muted)]">{preview.document.summary}</p>
                <p className="mt-2 text-xs text-[var(--ink-muted)]">This is an AI interpretation, not a legal conclusion.</p>
              </div>
            )}
            {preview.extractedText && (
              <pre className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-[var(--line)] bg-[var(--background)] p-3 text-xs leading-5">{preview.extractedText}</pre>
            )}
            {preview.blobUrl ? (
              <iframe title="PDF preview" src={preview.blobUrl} className="mt-4 min-h-80 w-full rounded-lg border border-[var(--line)]" />
            ) : (
              <p className="mt-4 text-sm text-[var(--ink-muted)]">The stored file is unavailable.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
