"use client";

import { useState } from "react";

import { RagApiError } from "@/lib/api/rag";
import {
  courtLevelLabel,
  formatJudgmentDate,
  lawKeyLabel,
  summarizeJudgment,
  type JudgmentSummary,
  type ResearchCase,
} from "@/lib/api/research";
import { isSafeExternalUrl } from "@/lib/urls/safeUrl";

function Badge({ tone, children }: { tone: "ok" | "accent" | "muted"; children: React.ReactNode }) {
  const styles = {
    ok: "bg-[var(--ok-bg)] text-[var(--ok)] border-[var(--ok-line)]",
    accent: "bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent-mid)]",
    muted: "bg-[var(--fill)] text-[var(--ink-muted)] border-[var(--line)]",
  }[tone];
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${styles}`}>
      {children}
    </span>
  );
}

function SummaryBlock({ summary }: { summary: JudgmentSummary }) {
  const rows: [string, string | null][] = [
    ["Facts", summary.facts],
    ["Held", summary.held],
    ["Ratio", summary.ratio],
    ["Outcome", summary.outcome],
    ["Why it matters", summary.significance],
  ];
  return (
    <div className="space-y-3 rounded-lg bg-[var(--fill)] p-4 text-sm leading-6">
      {summary.issues.length ? (
        <div>
          <h5 className="font-semibold">Issues decided</h5>
          <ul className="mt-1 list-disc pl-5">
            {summary.issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {rows.map(([label, value]) =>
        value ? (
          <div key={label}>
            <h5 className="font-semibold">{label}</h5>
            <p>{value}</p>
          </div>
        ) : null,
      )}
      {summary.provisions_applied.length ? (
        <p className="text-xs text-[var(--ink-muted)]">Provisions applied: {summary.provisions_applied.join("; ")}</p>
      ) : null}
      <p className="text-xs text-[var(--ink-faint)]">
        AI summary written from the official judgment text. Read the judgment before citing it.
      </p>
    </div>
  );
}

export default function CaseCard({
  item,
  actNames,
}: {
  item: ResearchCase;
  actNames: Record<string, string>;
}) {
  const [detail, setDetail] = useState<JudgmentSummary | null>(item.detailed_summary);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sourceUrl = isSafeExternalUrl(item.source_url);

  async function toggleDetail() {
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (detail || loading) return;
    setLoading(true);
    setError(null);
    try {
      setDetail(await summarizeJudgment(item.id));
    } catch (err) {
      setError(err instanceof RagApiError ? err.message : "The detailed summary could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <li className="panel space-y-3 p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold leading-6">{item.title}</h3>
            {item.is_landmark ? <Badge tone="accent">Landmark</Badge> : null}
            {item.is_new ? <Badge tone="muted">New to library</Badge> : null}
          </div>
          <p className="mt-1 text-xs text-[var(--ink-muted)]">
            {[item.court, formatJudgmentDate(item.judgment_date), item.citation, item.case_number]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
        {sourceUrl ? (
          <a href={sourceUrl} target="_blank" rel="noreferrer" className="btn-secondary btn-sm shrink-0">
            Official judgment ↗
          </a>
        ) : null}
      </div>

      <div className="space-y-2 text-sm leading-6">
        <p>{item.summary}</p>
        {item.holding && item.holding !== item.summary ? (
          <p>
            <span className="font-semibold">Held: </span>
            {item.holding}
          </p>
        ) : null}
        {item.relevance ? (
          <p className="text-[var(--ink-muted)]">
            <span className="font-semibold text-[var(--foreground)]">Why it is relevant: </span>
            {item.relevance}
          </p>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-[var(--line)] pt-3">
        {sourceUrl ? <Badge tone="ok">Verified on {new URL(sourceUrl).hostname}</Badge> : null}
        <Badge tone="muted">{courtLevelLabel(item.court_level)}</Badge>
        {item.law_keys.slice(0, 4).map((key) => (
          <Badge key={key} tone="muted">
            {lawKeyLabel(key, actNames)}
          </Badge>
        ))}
        {item.predecessor_provision ? <Badge tone="muted">Decided under {item.predecessor_provision}</Badge> : null}
        <button
          type="button"
          onClick={() => void toggleDetail()}
          className="ml-auto text-xs font-semibold text-[var(--accent)] hover:underline"
          aria-expanded={open}
        >
          {open ? "Hide detailed summary" : "Detailed summary"}
        </button>
      </div>

      {open ? (
        loading ? (
          <p className="text-sm text-[var(--ink-muted)]" aria-live="polite">
            Reading the official judgment and summarising it…
          </p>
        ) : error ? (
          <p role="alert" className="text-sm text-[var(--warn)]">
            {error}
          </p>
        ) : detail ? (
          <SummaryBlock summary={detail} />
        ) : null
      ) : null}
    </li>
  );
}
