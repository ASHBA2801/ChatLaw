"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import DisclaimerBanner from "./DisclaimerBanner";
import DocumentAiPanel from "./DocumentAiPanel";
import SelectionAiBar, { type SelectionPending } from "./SelectionAiBar";
import { addSection, createCustomSection, removeSection, updateSectionBody } from "@/lib/documents/editor";
import { STATUS_LABELS } from "@/lib/documents/constants";
import type { DocumentStatus, DocumentValues, GeneratedDocumentPayload, ProvisionClass } from "@/lib/documents/types";

type VersionSummary = {
  id: string;
  versionNumber: number;
  status: string;
  title: string;
  createdAt: string;
};

const PROVISION_LABELS: Record<ProvisionClass, string> = {
  required: "Required",
  recommended: "Recommended",
  user_specific: "User-specific",
};

function provisionLabel(value?: ProvisionClass, required?: boolean) {
  if (value && PROVISION_LABELS[value]) return PROVISION_LABELS[value];
  return required ? "Required" : "Recommended";
}

export default function DocumentEditor({
  documentId,
  initialStatus,
  initialValues,
  initialDocument,
  versions,
}: {
  documentId: string;
  initialStatus: DocumentStatus;
  initialValues: DocumentValues;
  initialDocument: GeneratedDocumentPayload;
  versions: VersionSummary[];
}) {
  const [payload, setPayload] = useState(initialDocument);
  const [status, setStatus] = useState<DocumentStatus>(initialStatus);
  const [selectedId, setSelectedId] = useState(initialDocument.sections[0]?.id ?? "");
  const [history, setHistory] = useState<GeneratedDocumentPayload[]>([initialDocument]);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pane, setPane] = useState<"edit" | "preview" | "assistant">("edit");
  const [dirty, setDirty] = useState(false);
  const [selectionRange, setSelectionRange] = useState<{ start: number; end: number } | null>(null);
  const [selectionPending, setSelectionPending] = useState<SelectionPending | null>(null);
  const [pendingRevise, setPendingRevise] = useState<GeneratedDocumentPayload | null>(null);
  const [assistantMessages, setAssistantMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([]);
  const [lastSelectionAction, setLastSelectionAction] = useState<{ action: string; custom?: string } | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const selected = payload.sections.find((section) => section.id === selectedId) ?? payload.sections[0];
  const selectedText =
    selected && selectionRange && selectionRange.end > selectionRange.start
      ? selected.body.slice(selectionRange.start, selectionRange.end)
      : "";

  function push(next: GeneratedDocumentPayload) {
    setPayload(next);
    setHistory((current) => [...current.slice(-20), next]);
    setDirty(true);
  }

  function captureSelection() {
    const el = textareaRef.current;
    if (!el || !selected) {
      setSelectionRange(null);
      return;
    }
    const start = el.selectionStart;
    const end = el.selectionEnd;
    if (end > start) setSelectionRange({ start, end });
    else setSelectionRange(null);
  }

  async function save() {
    setBusy("save");
    setError(null);
    try {
      const response = await fetch(`/api/documents/${documentId}/versions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document: payload, values: initialValues, status }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Could not save a new version.");
      setDirty(false);
      setMessage(`Saved as version ${body.versionNumber}. Previous versions were kept.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setBusy(null);
    }
  }

  async function regenerate() {
    if (!selected) return;
    setBusy("regen");
    setError(null);
    try {
      const response = await fetch(`/api/documents/${documentId}/regenerate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sectionId: selected.id }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Section regeneration failed.");
      push(body.document);
      setMessage(`Regenerated “${selected.title}” only.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Regeneration failed.");
    } finally {
      setBusy(null);
    }
  }

  async function changeStatus(next: DocumentStatus) {
    setBusy("status");
    setError(null);
    try {
      const response = await fetch(`/api/documents/${documentId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: next }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Could not update status.");
      setStatus(next);
      setMessage(`Status set to ${STATUS_LABELS[next]}. Generation never marks a draft as Final.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed.");
    } finally {
      setBusy(null);
    }
  }

  async function restore(versionNumber: number) {
    setBusy("restore");
    setError(null);
    try {
      const response = await fetch(`/api/documents/${documentId}/restore`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ versionNumber }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Could not restore that version.");
      window.location.reload();
      setMessage(`Restored version ${versionNumber} as version ${body.versionNumber}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Restore failed.");
      setBusy(null);
    }
  }

  function undo() {
    if (history.length < 2) return;
    const previous = history[history.length - 2];
    setHistory((current) => current.slice(0, -1));
    setPayload(previous);
    setDirty(true);
  }

  async function runSelectionEdit(action: string, customInstruction = "") {
    if (!selected || !selectionRange || !selectedText) return;
    setBusy("selection");
    setError(null);
    setLastSelectionAction({ action, custom: customInstruction || undefined });
    try {
      const response = await fetch(`/api/documents/${documentId}/selection-edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selectedText,
          action,
          customInstruction,
          surroundingSection: selected,
        }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Selection edit failed.");
      setSelectionPending({
        sectionId: selected.id,
        start: selectionRange.start,
        end: selectionRange.end,
        original: selectedText,
        suggestion: String(body.suggestion || ""),
        explanation: String(body.explanation || ""),
        action,
        warnsCitations: /\[SOURCE\s+\d+\]/i.test(selectedText),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Selection edit failed.");
    } finally {
      setBusy(null);
    }
  }

  function acceptSelection() {
    if (!selectionPending || !selected) return;
    if (selectionPending.action === "explain") {
      setSelectionPending(null);
      return;
    }
    if (selectionPending.warnsCitations) {
      const ok = window.confirm("This selection includes citation markers. Accept the AI replacement anyway?");
      if (!ok) return;
    }
    const before = selected.body.slice(0, selectionPending.start);
    const after = selected.body.slice(selectionPending.end);
    push(updateSectionBody(payload, selected.id, `${before}${selectionPending.suggestion}${after}`));
    setSelectionPending(null);
    setSelectionRange(null);
    setMessage("Selection update applied locally. Save a version to keep it.");
  }

  async function reviseDocument(instruction: string) {
    setBusy("revise");
    setError(null);
    setAssistantMessages((current) => [...current, { role: "user", content: instruction }]);
    try {
      const response = await fetch(`/api/documents/${documentId}/revise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction, sections: payload.sections }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Could not propose document changes.");
      setPendingRevise(body.document as GeneratedDocumentPayload);
      setAssistantMessages((current) => [
        ...current,
        { role: "assistant", content: String(body.notes || "Proposed updates are ready for Accept / Reject.") },
      ]);
    } catch (err) {
      const text = err instanceof Error ? err.message : "Revise failed.";
      setError(text);
      setAssistantMessages((current) => [...current, { role: "assistant", content: text }]);
    } finally {
      setBusy(null);
    }
  }

  function printDocument() {
    window.print();
  }

  return (
    <div className="document-workspace space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3 print:hidden">
        <div className="min-w-0">
          <p className="text-sm text-[var(--ink-muted)]">
            <Link href="/documents" className="underline-offset-2 hover:underline">Documents</Link>
            <span aria-hidden="true"> / </span>
            {payload.document_type}
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{payload.title}</h1>
          <p className="mt-1 text-sm text-[var(--ink-muted)]">
            India{payload.jurisdiction_region ? ` — ${payload.jurisdiction_region}` : ""} · Status {STATUS_LABELS[status]}
            {" · "}
            {dirty ? "Unsaved changes" : "Saved"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a className="inline-flex min-h-11 items-center rounded-sm border border-[var(--line)] bg-white px-4 text-sm font-medium" href={`/api/documents/${documentId}/export?format=pdf`}>Export PDF</a>
          <a className="inline-flex min-h-11 items-center rounded-sm border border-[var(--line)] bg-white px-4 text-sm font-medium" href={`/api/documents/${documentId}/export?format=docx`}>Export DOCX</a>
          <button type="button" onClick={printDocument} className="min-h-11 rounded-sm border border-[var(--line)] bg-white px-4 text-sm font-medium">Print</button>
          <button type="button" onClick={save} disabled={busy !== null} className="min-h-11 rounded-sm bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-60">
            {busy === "save" ? "Saving…" : "Save new version"}
          </button>
        </div>
      </div>

      <div className="print:hidden">
        <DisclaimerBanner compact />
      </div>

      <div className="flex gap-2 lg:hidden print:hidden" role="tablist" aria-label="Document views">
        {(["edit", "preview", "assistant"] as const).map((item) => (
          <button
            key={item}
            type="button"
            role="tab"
            aria-selected={pane === item}
            onClick={() => setPane(item)}
            className={`min-h-11 flex-1 rounded-sm text-sm font-medium ${pane === item ? "bg-[var(--forest)] text-white" : "border border-[var(--line)] bg-white"}`}
          >
            {item === "edit" ? "Edit" : item === "preview" ? "Preview" : "Assistant"}
          </button>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[220px_minmax(0,1fr)_minmax(280px,340px)] print:block">
        <aside className={`rounded-sm border border-[var(--line)] bg-white p-3 print:hidden ${pane === "edit" || pane === "preview" ? "" : "hidden"} xl:block`}>
          <h2 className="px-2 text-sm font-semibold">Clauses</h2>
          <ul className="mt-2 space-y-1">
            {payload.sections.map((section) => (
              <li key={section.id}>
                <button
                  type="button"
                  onClick={() => { setSelectedId(section.id); setPane("edit"); setSelectionPending(null); }}
                  className={`flex min-h-11 w-full flex-col items-start rounded-sm px-3 py-2 text-left text-sm ${section.id === selected?.id ? "bg-[var(--signal-soft)] text-[var(--forest)]" : "hover:bg-[var(--module-fill)]"}`}
                >
                  <span className="w-full truncate">{section.number ? `${section.number}. ${section.title}` : section.title}</span>
                  <span className="mt-0.5 text-[10px] uppercase tracking-wide text-[var(--ink-muted)]">
                    {provisionLabel(section.provision_class, section.required)}
                    {section.review_required ? " · Review" : ""}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={() => {
              const section = createCustomSection("Additional clause");
              push(addSection(payload, section, selected?.id));
              setSelectedId(section.id);
            }}
            className="mt-3 min-h-11 w-full rounded-sm border border-dashed border-[var(--line)] text-sm"
          >
            Add clause
          </button>
        </aside>

        <section className={`space-y-3 ${pane === "edit" || pane === "preview" ? "block" : "hidden"} xl:block`}>
          <div className={`rounded-sm border border-[var(--line)] bg-white p-4 print:hidden ${pane === "edit" ? "block" : "hidden xl:block"}`}>
            {selected ? (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-semibold">{selected.title}</h2>
                    <p className="text-xs uppercase tracking-wide text-[var(--ink-muted)]">
                      {provisionLabel(selected.provision_class, selected.required)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button type="button" onClick={undo} disabled={history.length < 2} className="min-h-11 rounded-sm border border-[var(--line)] px-3 text-sm disabled:opacity-50">Undo</button>
                    <button type="button" onClick={regenerate} disabled={busy !== null} className="min-h-11 rounded-sm border border-[var(--line)] px-3 text-sm">
                      {busy === "regen" ? "Regenerating…" : "Regenerate section"}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const next = removeSection(payload, selected.id);
                        push(next);
                        setSelectedId(next.sections[0]?.id ?? "");
                      }}
                      className="min-h-11 rounded-sm border border-[var(--line)] px-3 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                </div>
                <SelectionAiBar
                  hasSelection={Boolean(selectedText)}
                  pending={selectionPending}
                  busy={busy === "selection"}
                  onAction={(action) => runSelectionEdit(action)}
                  onCustom={(instruction) => runSelectionEdit("custom", instruction)}
                  onAccept={acceptSelection}
                  onReject={() => setSelectionPending(null)}
                  onRegenerate={() => {
                    if (!lastSelectionAction) return;
                    runSelectionEdit(lastSelectionAction.action, lastSelectionAction.custom || "");
                  }}
                />
                <label htmlFor="clause-body" className="text-sm font-medium">Clause text</label>
                <textarea
                  ref={textareaRef}
                  id="clause-body"
                  value={selected.body}
                  onSelect={captureSelection}
                  onMouseUp={captureSelection}
                  onKeyUp={captureSelection}
                  onChange={(event) => {
                    setSelectionPending(null);
                    push(updateSectionBody(payload, selected.id, event.target.value));
                  }}
                  aria-describedby={selected.review_required ? "clause-review-note" : undefined}
                  className="min-h-72 w-full rounded-sm border border-[var(--line)] p-3 font-serif text-[15px] leading-7"
                />
                {selected.review_required ? (
                  <p id="clause-review-note" className="text-sm text-[var(--ink-muted)]">This clause is marked for legal review before use.</p>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-[var(--ink-muted)]">Select a clause to edit.</p>
            )}
          </div>

          <div className={`overflow-hidden rounded-sm border border-[var(--line)] bg-white p-5 ${pane === "preview" ? "block" : "hidden xl:block"} print:border-0 print:p-0`}>
            <h2 className="text-sm font-semibold print:hidden">Document preview</h2>
            <article className="document-sheet document-print-root mt-3 max-h-[70vh] overflow-auto pr-2 print:max-h-none print:overflow-visible">
              <h3 className="font-serif text-xl">{payload.title}</h3>
              <p className="mt-1 text-xs text-[var(--ink-muted)]">Jurisdiction: India{payload.jurisdiction_region ? ` — ${payload.jurisdiction_region}` : ""}</p>
              {payload.sections.map((section) => (
                <section key={section.id} className="mt-5">
                  <h4 className="font-serif text-sm font-semibold tracking-wide">
                    {(section.number ? `${section.number}. ` : "") + section.title}
                  </h4>
                  <p className="mt-2 whitespace-pre-wrap font-serif text-[15px] leading-7">{section.body}</p>
                  {section.legal_basis?.length ? (
                    <p className="mt-2 text-xs text-[var(--ink-muted)]">Legal basis: {section.legal_basis.map((item) => item.label).join("; ")}</p>
                  ) : null}
                  {section.include_signature ? payload.signatures.map((block) => (
                    <pre key={block.party_id} className="mt-4 font-serif text-sm leading-7">{block.lines.join("\n")}</pre>
                  )) : null}
                </section>
              ))}
              {payload.disclaimer ? (
                <p className="mt-8 border-t border-[var(--line)] pt-4 text-xs text-[var(--ink-muted)]">{payload.disclaimer}</p>
              ) : null}
            </article>
          </div>
        </section>

        <aside className={`print:hidden ${pane === "assistant" ? "block" : "hidden"} xl:block`}>
          <DocumentAiPanel
            payload={payload}
            status={status}
            versions={versions}
            busy={busy}
            messages={assistantMessages}
            pendingRevise={pendingRevise}
            onStatus={changeStatus}
            onRestore={restore}
            onRevise={reviseDocument}
            onAcceptRevise={() => {
              if (!pendingRevise) return;
              push(pendingRevise);
              setPendingRevise(null);
              setMessage("AI revise applied locally. Save a version to keep it.");
            }}
            onRejectRevise={() => setPendingRevise(null)}
          />
        </aside>
      </div>

      {error ? <p role="alert" className="text-sm text-[#8a3b2b] print:hidden">{error}</p> : null}
      {message ? <p role="status" className="text-sm text-[var(--forest)] print:hidden">{message}</p> : null}
    </div>
  );
}
