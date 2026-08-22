"use client";

import { FormEvent, useState } from "react";

import { STATUS_LABELS } from "@/lib/documents/constants";
import type { DocumentStatus, DocumentWarning, GeneratedDocumentPayload } from "@/lib/documents/types";

type VersionSummary = {
  id: string;
  versionNumber: number;
  status: string;
  title: string;
  createdAt: string;
};

type ChatItem = { role: "user" | "assistant"; content: string };

export default function DocumentAiPanel({
  payload,
  status,
  versions,
  busy,
  messages,
  pendingRevise,
  onStatus,
  onRestore,
  onRevise,
  onAcceptRevise,
  onRejectRevise,
}: {
  payload: GeneratedDocumentPayload;
  status: DocumentStatus;
  versions: VersionSummary[];
  busy: string | null;
  messages: ChatItem[];
  pendingRevise: GeneratedDocumentPayload | null;
  onStatus: (status: DocumentStatus) => void;
  onRestore: (versionNumber: number) => void;
  onRevise: (instruction: string) => void;
  onAcceptRevise: () => void;
  onRejectRevise: () => void;
}) {
  const [instruction, setInstruction] = useState("");

  function submit(event: FormEvent) {
    event.preventDefault();
    const text = instruction.trim();
    if (!text) return;
    onRevise(text);
    setInstruction("");
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-[var(--line)] bg-white p-4">
        <h2 className="text-sm font-semibold">AI assistant</h2>
        <p className="mt-1 text-sm text-[var(--ink-muted)]">
          Ask for document changes. Suggestions are previewed before they replace your draft.
        </p>
        <div className="mt-3 max-h-48 space-y-2 overflow-auto" aria-live="polite">
          {messages.length === 0 ? (
            <p className="text-sm text-[var(--ink-muted)]">Examples: “Make the termination period 30 days.” or “Add a confidentiality clause.”</p>
          ) : (
            messages.map((item, index) => (
              <div key={`${item.role}-${index}`} className={`rounded-xl px-3 py-2 text-sm ${item.role === "user" ? "bg-[#eef5d0]" : "bg-[#edf2ec]"}`}>
                <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--ink-muted)]">{item.role === "user" ? "You" : "Assistant"}</p>
                <p className="mt-1 whitespace-pre-wrap">{item.content}</p>
              </div>
            ))
          )}
        </div>
        {pendingRevise ? (
          <div className="mt-3 rounded-xl border border-[var(--line)] bg-[#f8faf6] p-3">
            <p className="text-sm font-medium">Pending document changes</p>
            <p className="mt-1 text-sm text-[var(--ink-muted)]">
              {pendingRevise.sections.length} sections in proposal. Accept to apply locally, then save a version.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <button type="button" onClick={onAcceptRevise} disabled={busy !== null} className="min-h-11 rounded-full bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-60">
                Accept
              </button>
              <button type="button" onClick={onRejectRevise} disabled={busy !== null} className="min-h-11 rounded-full border border-[var(--line)] bg-white px-4 text-sm">
                Reject
              </button>
            </div>
          </div>
        ) : null}
        <form onSubmit={submit} className="mt-3 space-y-2">
          <label htmlFor="doc-ai-instruction" className="sr-only">Document change instruction</label>
          <textarea
            id="doc-ai-instruction"
            value={instruction}
            onChange={(event) => setInstruction(event.target.value)}
            rows={3}
            placeholder="Describe the change…"
            className="w-full rounded-xl border border-[var(--line)] p-3 text-sm"
            disabled={busy !== null}
          />
          <button type="submit" disabled={busy !== null || !instruction.trim()} className="min-h-11 w-full rounded-full bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-60">
            {busy === "revise" ? "Working…" : "Propose changes"}
          </button>
        </form>
      </div>

      <div className="rounded-2xl border border-[var(--line)] bg-white p-4">
        <h2 className="text-sm font-semibold">Warnings and legal context</h2>
        <ul className="mt-3 space-y-2">
          {(payload.warnings as DocumentWarning[]).map((warning) => (
            <li key={`${warning.code}-${warning.message.slice(0, 24)}`} className="text-sm leading-6">{warning.message}</li>
          ))}
        </ul>
        {payload.sections.some((section) => section.legal_basis?.length) ? (
          <div className="mt-4">
            <h3 className="text-sm font-medium">Citations</h3>
            <ul className="mt-2 space-y-1 text-sm text-[var(--ink-muted)]">
              {payload.sections.flatMap((section) =>
                (section.legal_basis || []).map((item) => (
                  <li key={`${section.id}-${item.citation_id}`}>{item.label}</li>
                )),
              )}
            </ul>
          </div>
        ) : null}
      </div>

      <div className="rounded-2xl border border-[var(--line)] bg-white p-4">
        <fieldset>
          <legend className="text-sm font-medium">Document status</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {(["draft", "review", "final"] as const).map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => onStatus(item)}
                aria-pressed={status === item}
                className={`min-h-11 rounded-full px-3 text-sm ${status === item ? "bg-[var(--forest)] text-white" : "border border-[var(--line)]"}`}
              >
                {STATUS_LABELS[item]}
              </button>
            ))}
          </div>
        </fieldset>
        <div className="mt-4">
          <h3 className="text-sm font-medium">Versions</h3>
          <ul className="mt-2 space-y-2">
            {versions.map((version) => (
              <li key={version.id} className="flex items-center justify-between gap-2 text-sm">
                <span>Version {version.versionNumber} · {version.status}</span>
                <button type="button" onClick={() => onRestore(version.versionNumber)} className="min-h-11 rounded-full border border-[var(--line)] px-3">
                  Restore
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
