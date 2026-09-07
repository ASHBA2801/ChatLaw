"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { RagApiError, searchLegalSources, type SearchResult } from "@/lib/api/rag";
import { searchOfficialJudgments, type RankedCaseResult } from "@/lib/cases/official-cases";
import { isSafeExternalUrl } from "@/lib/urls/safeUrl";

type Scope = "all" | "statutes" | "cases";

function formatJudgmentDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });
  } catch {
    return dateStr;
  }
}

export default function ResearchWorkspace({ initialQuery }: { initialQuery: string }) {
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);
  const [query, setQuery] = useState(initialQuery);
  const [filter, setFilter] = useState("");
  const [scope, setScope] = useState<Scope>("all");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [cases, setCases] = useState<RankedCaseResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [noRelevant, setNoRelevant] = useState(false);
  const autoStarted = useRef(false);

  useEffect(() => {
    if (autoStarted.current || !initialQuery.trim()) return;
    autoStarted.current = true;
    formRef.current?.requestSubmit();
  }, [initialQuery]);

  async function runSearch(value: string) {
    setLoading(true);
    setError(null);
    setSearched(true);
    const officialHits = searchOfficialJudgments(value, { limit: 12 });
    setCases(officialHits);
    try {
      const response = await searchLegalSources({ query: value, top_k: 12, min_similarity: 0.55 });
      setResults(response.results);
      setNoRelevant(response.no_relevant_context && officialHits.length === 0);
      router.replace(`/research?q=${encodeURIComponent(value)}`, { scroll: false });
    } catch (err) {
      setResults([]);
      // Official cases still usable offline from local verified data.
      setNoRelevant(officialHits.length === 0);
      if (officialHits.length === 0) {
        setError(err instanceof RagApiError ? err.message : "Search failed. Try again.");
      } else {
        setError(null);
      }
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    void runSearch(trimmed);
  }

  const filteredStatutes = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return results;
    return results.filter((item) => {
      const haystack = [item.document_title, item.section_number, item.chapter, item.subsection, item.content]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [filter, results]);

  const filteredCases = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return cases;
    return cases.filter((item) =>
      [item.title, item.citation, item.court, item.legal_issue, item.relevant_law, item.why_relevant]
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [cases, filter]);

  const showStatutes = scope === "all" || scope === "statutes";
  const showCases = scope === "all" || scope === "cases";

  return (
    <div className="space-y-6">
      <form ref={formRef} onSubmit={onSubmit} className="rounded-sm border border-[var(--line)] bg-white p-4 sm:p-5">
        <label htmlFor="research-query" className="text-sm font-semibold">
          Legal question or keywords
        </label>
        <div className="mt-2 flex flex-col gap-3 sm:flex-row">
          <input
            id="research-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="e.g. privacy Article 21 OR security deposit landlord"
            className="min-h-11 flex-1 rounded-sm border border-[var(--line)] bg-[var(--background)] px-4 text-sm outline-none focus:border-[var(--forest)]"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="min-h-11 rounded-sm bg-[var(--forest)] px-6 text-sm font-semibold text-white disabled:opacity-50"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
        {searched ? (
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="flex rounded-sm border border-[var(--line)] p-1" role="group" aria-label="Result type">
              {(
                [
                  ["all", "All"],
                  ["statutes", "Statutes"],
                  ["cases", "Cases"],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setScope(value)}
                  className={`min-h-10 flex-1 rounded-sm px-3 text-sm font-medium ${scope === value ? "bg-[var(--forest)] text-white" : "text-[var(--ink-muted)]"}`}
                  aria-pressed={scope === value}
                >
                  {label}
                </button>
              ))}
            </div>
            <input
              id="research-filter"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              placeholder="Filter by title, section, court, or text"
              className="min-h-11 flex-1 rounded-sm border border-[var(--line)] px-4 text-sm outline-none focus:border-[var(--forest)]"
            />
          </div>
        ) : null}
      </form>

      {error ? (
        <div role="alert" className="rounded-sm border border-[var(--warn-line)] bg-[var(--warn-bg)] px-5 py-4 text-sm text-[var(--warn)]">
          {error}
        </div>
      ) : null}

      {!searched && !loading ? (
        <div className="rounded-sm border border-dashed border-[var(--line)] bg-white px-6 py-14 text-center">
          <h2 className="text-lg font-semibold">Search statutes and landmark cases</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[var(--ink-muted)]">
            Statute passages come from the ChatLaw corpus. Landmark cases are a curated verified set with official
            citations — not an exhaustive judgment database.
          </p>
        </div>
      ) : null}

      {loading ? (
        <div className="space-y-3" aria-busy="true" aria-live="polite">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-sm border border-[var(--line)] bg-white" />
          ))}
        </div>
      ) : null}

      {searched && !loading && noRelevant && !error ? (
        <div className="rounded-sm border border-[var(--line)] bg-white px-6 py-12 text-center">
          <h2 className="text-lg font-semibold">No matching sources</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[var(--ink-muted)]">
            Try different keywords, a section number, a case name, or ask in{" "}
            <Link href="/chat" className="font-semibold text-[var(--forest)] underline-offset-2 hover:underline">
              Chat
            </Link>
            .
          </p>
        </div>
      ) : null}

      {searched && !loading && scope === "cases" && filteredCases.length === 0 ? (
        <div className="rounded-sm border border-[var(--line)] bg-white px-6 py-10 text-center">
          <h3 className="text-base font-semibold">No sufficiently relevant judgments found</h3>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[var(--ink-muted)]">
            No sufficiently relevant judgment was found in the available official case-law sources.
          </p>
        </div>
      ) : null}

      {searched && !loading && showCases && filteredCases.length > 0 ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Relevant official judgments</h2>
              <p className="mt-1 text-xs text-[var(--ink-muted)]">
                Authoritative judgments retrieved and ranked by legal relevance from official court sources.
              </p>
            </div>
            <span className="text-xs font-medium text-[var(--forest)]">Official Indian Judiciary</span>
          </div>
          <ul className="space-y-3">
            {filteredCases.map((item) => {
              const sourceUrl = isSafeExternalUrl(item.source_url);
              return (
                <li key={item.id} className="rounded-sm border border-[var(--line)] bg-white p-4 sm:p-5 space-y-2.5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-base font-semibold leading-6">{item.title}</h3>
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold border ${
                          item.relevance_level === "Highly relevant"
                            ? "bg-[#e8f5e9] text-[#1b5e20] border-[#a5d6a7]"
                            : item.relevance_level === "Relevant"
                              ? "bg-[#e3f2fd] text-[#0d47a1] border-[#90caf9]"
                              : "bg-[#f5f5f5] text-[#424242] border-[#e0e0e0]"
                        }`}>
                          {item.relevance_score}% · {item.relevance_level}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-[var(--ink-muted)]">
                        {item.court} · {formatJudgmentDate(item.judgment_date)} · {item.citation}
                      </p>
                    </div>
                    {sourceUrl ? (
                      <a
                        href={sourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="min-h-10 inline-flex items-center rounded-sm border border-[var(--line)] px-3 text-sm font-medium text-[var(--forest)] hover:border-[var(--forest)] bg-white"
                      >
                        Official judgment ↗
                      </a>
                    ) : null}
                  </div>

                  <div className="pt-2 text-xs space-y-1.5 border-t border-[var(--line)] text-[var(--ink)]">
                    <div>
                      <span className="font-semibold text-[var(--signal)]">Relevant issue: </span>
                      <span>{item.legal_issue}</span>
                    </div>
                    <div>
                      <span className="font-semibold text-[var(--signal)]">Relevant law: </span>
                      <span className="text-[var(--ink-muted)]">{item.relevant_law}</span>
                    </div>
                    <div>
                      <span className="font-semibold text-[var(--signal)]">Why this case is relevant: </span>
                      <span className="leading-5 text-[var(--ink-muted)]">{item.why_relevant}</span>
                    </div>
                    <div className="text-[11px] text-[var(--ink-muted)]">
                      <span className="font-medium">Source: </span>
                      <span>{item.source_authority}</span>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}

      {searched && !loading && showStatutes && filteredStatutes.length > 0 ? (
        <section className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold">Statutes and legal sources</h2>
            <p className="mt-1 text-xs text-[var(--ink-muted)]">Retrieved passages from the ChatLaw legal corpus.</p>
          </div>
          <ul className="space-y-3">
            {filteredStatutes.map((item) => {
              const sourceUrl =
                isSafeExternalUrl(
                  typeof item.metadata?.source_url === "string" ? item.metadata.source_url : null,
                ) ??
                isSafeExternalUrl(typeof item.metadata?.url === "string" ? item.metadata.url : null);
              return (
                <li key={item.chunk_id} className="rounded-sm border border-[var(--line)] bg-white p-4 sm:p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="text-base font-semibold leading-6">{item.document_title}</h3>
                      <p className="mt-1 text-xs text-[var(--ink-muted)]">
                        {[
                          item.chapter ? `Chapter ${item.chapter}` : null,
                          item.section_number ? `Section ${item.section_number}` : null,
                          item.subsection ? `Subsection ${item.subsection}` : null,
                        ]
                          .filter(Boolean)
                          .join(" · ") || "Passage"}
                        {" · "}
                        Relevance {(item.similarity * 100).toFixed(0)}%
                      </p>
                    </div>
                    {sourceUrl ? (
                      <a
                        href={sourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="min-h-10 rounded-sm border border-[var(--line)] px-3 text-sm font-medium text-[var(--forest)] hover:border-[var(--forest)]"
                      >
                        Open source
                      </a>
                    ) : null}
                  </div>
                  <p className="mt-3 text-sm leading-6 text-[var(--foreground)]">
                    {item.content.slice(0, 420)}
                    {item.content.length > 420 ? "…" : ""}
                  </p>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
