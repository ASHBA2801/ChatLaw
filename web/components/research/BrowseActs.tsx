"use client";

import { useMemo, useRef, useState } from "react";

import { RagApiError } from "@/lib/api/rag";
import {
  lawCases,
  listSections,
  type ActSummary,
  type ResearchCase,
  type SectionSummary,
} from "@/lib/api/research";

import CaseCard from "./CaseCard";

function sectionLabel(actId: string, section: string) {
  return actId === "CONSTITUTION" ? `Article ${section}` : `Section ${section}`;
}

export default function BrowseActs({
  acts,
  actNames,
  loadError,
  onResearch,
}: {
  acts: ActSummary[] | null;
  actNames: Record<string, string>;
  loadError: string | null;
  onResearch: (query: string) => void;
}) {
  const [actId, setActId] = useState<string | null>(null);
  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  const [sectionFilter, setSectionFilter] = useState("");
  const [lawKey, setLawKey] = useState<string | null>(null);
  const [cases, setCases] = useState<ResearchCase[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const act = acts?.find((item) => item.act_id === actId) ?? null;

  // Guards against a slow response for a previously selected Act or section.
  const latest = useRef({ actId: null as string | null, lawKey: null as string | null });

  function selectLaw(key: string) {
    latest.current.lawKey = key;
    setLawKey(key);
    setCases(null);
    lawCases(key)
      .then((response) => latest.current.lawKey === key && setCases(response.cases))
      .catch((err) => latest.current.lawKey === key && setError(err instanceof RagApiError ? err.message : "Cases could not be loaded."));
  }

  function selectAct(item: ActSummary) {
    latest.current = { actId: item.act_id, lawKey: null };
    setActId(item.act_id);
    setLawKey(null);
    setSections(null);
    setError(null);
    if (!item.section_count) {
      setSections([]);
      selectLaw(item.act_id);
      return;
    }
    listSections(item.act_id)
      .then((response) => latest.current.actId === item.act_id && setSections(response.sections))
      .catch((err) => latest.current.actId === item.act_id && setError(err instanceof RagApiError ? err.message : "Sections could not be loaded."));
  }

  const visibleSections = useMemo(() => {
    const needle = sectionFilter.trim().toLowerCase();
    if (!sections || !needle) return sections ?? [];
    return sections.filter((row) => `${row.section} ${row.preview}`.toLowerCase().includes(needle));
  }, [sections, sectionFilter]);

  if (loadError) {
    return (
      <p role="alert" className="rounded-xl border border-[var(--warn-line)] bg-[var(--warn-bg)] px-5 py-4 text-sm text-[var(--warn)]">
        {loadError}
      </p>
    );
  }
  if (!acts) {
    return <div className="h-40 animate-pulse rounded-xl border border-[var(--line)] bg-[var(--surface)]" aria-busy="true" />;
  }

  if (!actId) {
    return (
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {acts.map((item) => (
          <li key={item.act_id}>
            <button
              type="button"
              onClick={() => selectAct(item)}
              className="panel flex h-full w-full flex-col items-start p-4 text-left hover:border-[var(--line-strong)]"
            >
              <span className="text-[0.9375rem] font-semibold">{actNames[item.act_id] ?? item.act_id}</span>
              <span className="mt-1 text-xs text-[var(--ink-muted)]">
                {item.section_count ? `${item.section_count} sections · ` : "Act-level cases · "}
                {item.case_count} verified {item.case_count === 1 ? "case" : "cases"}
              </span>
            </button>
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => {
            latest.current = { actId: null, lawKey: null };
            setActId(null);
            setLawKey(null);
            setSectionFilter("");
          }}
          className="btn-secondary btn-sm"
        >
          ← All Acts
        </button>
        <h2 className="text-lg font-semibold">{act?.title ?? actNames[actId] ?? actId}</h2>
      </div>
      {error ? (
        <p role="alert" className="text-sm text-[var(--warn)]">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        {act?.section_count ? (
          <div className="panel flex max-h-[70vh] flex-col p-3">
            <input
              value={sectionFilter}
              onChange={(event) => setSectionFilter(event.target.value)}
              placeholder="Filter sections"
              aria-label="Filter sections"
              className="mb-2 min-h-10 rounded-sm border border-[var(--line)] bg-[var(--background)] px-3 text-sm outline-none focus:border-[var(--accent)]"
            />
            {!sections ? (
              <p className="p-2 text-sm text-[var(--ink-muted)]">Loading sections…</p>
            ) : (
              <ul className="min-h-0 flex-1 overflow-y-auto">
                {visibleSections.map((row) => {
                  const key = `${actId}:${row.section}`;
                  return (
                    <li key={row.section}>
                      <button
                        type="button"
                        onClick={() => selectLaw(key)}
                        aria-current={lawKey === key}
                        className={`w-full rounded-md px-2.5 py-2 text-left ${lawKey === key ? "bg-[var(--accent-soft)]" : "hover:bg-[var(--fill)]"}`}
                      >
                        <span className="flex items-center justify-between gap-2 text-sm font-semibold">
                          {sectionLabel(actId, row.section)}
                          {row.case_count ? (
                            <span className="text-xs font-medium text-[var(--accent)]">{row.case_count} cases</span>
                          ) : null}
                        </span>
                        <span className="mt-0.5 line-clamp-2 text-xs text-[var(--ink-muted)]">{row.preview}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        ) : null}

        <div className="min-w-0 space-y-3">
          {!lawKey ? (
            <p className="rounded-xl border border-dashed border-[var(--line)] px-5 py-10 text-center text-sm text-[var(--ink-muted)]">
              Choose a section to see its landmark judgments.
            </p>
          ) : (
            <>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-base font-semibold">
                  {lawKey.includes(":")
                    ? `${sectionLabel(actId, lawKey.split(":")[1])} — landmark and leading judgments`
                    : "Landmark and leading judgments"}
                </h3>
                <button
                  type="button"
                  className="btn-secondary btn-sm"
                  onClick={() =>
                    onResearch(
                      lawKey.includes(":")
                        ? `${sectionLabel(actId, lawKey.split(":")[1])} ${actNames[actId] ?? actId}`
                        : (act?.title ?? actNames[actId] ?? actId),
                    )
                  }
                >
                  Research this {lawKey.includes(":") ? "section" : "Act"}
                </button>
              </div>
              {!cases ? (
                <div className="h-28 animate-pulse rounded-xl border border-[var(--line)] bg-[var(--surface)]" />
              ) : cases.length ? (
                <ul className="space-y-3">
                  {cases.map((item) => (
                    <CaseCard key={item.id} item={item} actNames={actNames} />
                  ))}
                </ul>
              ) : (
                <p className="rounded-xl border border-[var(--line)] bg-[var(--surface)] px-5 py-8 text-center text-sm text-[var(--ink-muted)]">
                  No verified judgments are stored for this yet. Use “Research this section” to search official
                  court websites.
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
