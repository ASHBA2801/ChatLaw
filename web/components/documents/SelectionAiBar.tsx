"use client";

import { useState } from "react";

const ACTIONS: Array<{ id: string; label: string }> = [
  { id: "improve", label: "Improve wording" },
  { id: "simplify", label: "Simplify" },
  { id: "formal", label: "More formal" },
  { id: "explain", label: "Explain" },
  { id: "expand", label: "Expand" },
  { id: "shorten", label: "Shorten" },
  { id: "rewrite", label: "Rewrite" },
  { id: "legally_clearer", label: "Legally clearer" },
  { id: "alternative", label: "Suggest alternative" },
  { id: "translate", label: "Translate" },
];

export type SelectionPending = {
  sectionId: string;
  start: number;
  end: number;
  original: string;
  suggestion: string;
  explanation: string;
  action: string;
  warnsCitations: boolean;
};

export default function SelectionAiBar({
  disabled,
  hasSelection,
  pending,
  busy,
  onAction,
  onCustom,
  onAccept,
  onReject,
  onRegenerate,
}: {
  disabled?: boolean;
  hasSelection: boolean;
  pending: SelectionPending | null;
  busy: boolean;
  onAction: (action: string) => void;
  onCustom: (instruction: string) => void;
  onAccept: () => void;
  onReject: () => void;
  onRegenerate: () => void;
}) {
  const [custom, setCustom] = useState("");

  if (pending) {
    return (
      <div className="rounded-sm border border-[var(--line)] bg-[#f8faf6] p-3" role="region" aria-label="AI suggestion preview">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">Suggestion preview</p>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          <div>
            <p className="text-xs text-[var(--ink-muted)]">Selected</p>
            <p className="mt-1 whitespace-pre-wrap rounded-sm border border-[var(--line)] bg-white p-2 font-serif text-sm">{pending.original}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--ink-muted)]">{pending.action === "explain" ? "Explanation" : "Suggested"}</p>
            <p className="mt-1 whitespace-pre-wrap rounded-sm border border-[var(--line)] bg-white p-2 font-serif text-sm">
              {pending.action === "explain" ? pending.explanation : pending.suggestion || pending.explanation}
            </p>
          </div>
        </div>
        {pending.explanation && pending.action !== "explain" ? (
          <p className="mt-2 text-sm text-[var(--ink-muted)]">{pending.explanation}</p>
        ) : null}
        {pending.warnsCitations ? (
          <p className="mt-2 text-sm text-[var(--warn)]" role="status">
            This selection includes citation markers. Accepting may affect legal references — review carefully.
          </p>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          {pending.action !== "explain" ? (
            <button type="button" onClick={onAccept} disabled={busy || !pending.suggestion} className="min-h-11 rounded-sm bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-60">
              Accept
            </button>
          ) : null}
          <button type="button" onClick={onReject} disabled={busy} className="min-h-11 rounded-sm border border-[var(--line)] bg-white px-4 text-sm">
            Reject
          </button>
          <button type="button" onClick={onRegenerate} disabled={busy} className="min-h-11 rounded-sm border border-[var(--line)] bg-white px-4 text-sm">
            {busy ? "Working…" : "Regenerate"}
          </button>
        </div>
      </div>
    );
  }

  if (!hasSelection) return null;

  return (
    <div className="rounded-sm border border-[var(--line)] bg-white p-3" role="toolbar" aria-label="Selected text AI actions">
      <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)]">AI edit selection</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {ACTIONS.map((action) => (
          <button
            key={action.id}
            type="button"
            disabled={disabled || busy}
            onClick={() => onAction(action.id)}
            className="min-h-10 rounded-sm border border-[var(--line)] px-3 text-sm disabled:opacity-50"
          >
            {action.label}
          </button>
        ))}
      </div>
      <form
        className="mt-3 flex flex-col gap-2 sm:flex-row"
        onSubmit={(event) => {
          event.preventDefault();
          const instruction = custom.trim();
          if (!instruction) return;
          onCustom(instruction);
          setCustom("");
        }}
      >
        <label htmlFor="selection-custom" className="sr-only">Custom instruction for selected text</label>
        <input
          id="selection-custom"
          value={custom}
          onChange={(event) => setCustom(event.target.value)}
          placeholder="Custom instruction for this selection…"
          disabled={disabled || busy}
          className="min-h-11 flex-1 rounded-sm border border-[var(--line)] px-3 text-sm"
        />
        <button type="submit" disabled={disabled || busy || !custom.trim()} className="min-h-11 rounded-sm bg-[var(--forest)] px-4 text-sm font-semibold text-white disabled:opacity-60">
          Apply
        </button>
      </form>
    </div>
  );
}
