"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { RagApiError } from "@/lib/api/rag";
import {
  articulateLaw,
  COURT_LEVELS,
  listActs,
  researchCases,
  researchLaw,
  type ActSummary,
  type Articulation,
  type CasesResponse,
  type CourtLevel,
  type LawResponse,
} from "@/lib/api/research";

import BrowseActs from "./BrowseActs";
import CaseCard from "./CaseCard";
import { ArticulationCard, ProvisionList } from "./LawPanel";

type Mode = "research" | "browse";

const EXAMPLES = [
  "Section 103 BNS punishment for murder",
  "IPC 498A cruelty by husband",
  "Divorce on the ground of cruelty under section 13 Hindu Marriage Act",
  "Who is a consumer under section 2(7) Consumer Protection Act 2019",
  "Electronic evidence certificate section 63 BSA",
  "Anticipatory bail 438 CrPC",
];

// Names for Acts that are researched but not in the statute corpus.
const EXTRA_ACT_NAMES: Record<string, string> = {
  CONSTITUTION: "Constitution of India",
  RAILWAYS1989: "Railways Act, 1989",
  IDA1947: "Industrial Disputes Act, 1947",
};

function errorMessage(error: unknown, fallback: string) {
  return error instanceof RagApiError ? error.message : fallback;
}

export default function ResearchWorkspace({ initialQuery }: { initialQuery: string }) {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("research");
  const [query, setQuery] = useState(initialQuery);
  const [courtLevels, setCourtLevels] = useState<CourtLevel[]>(["SUPREME_COURT", "HIGH_COURT", "DISTRICT_COURT", "TRIBUNAL"]);

  const [law, setLaw] = useState<LawResponse | null>(null);
  const [lawLoading, setLawLoading] = useState(false);
  const [lawError, setLawError] = useState<string | null>(null);

  const [articulation, setArticulation] = useState<Articulation | null>(null);
  const [articulationLoading, setArticulationLoading] = useState(false);
  const [articulationError, setArticulationError] = useState<string | null>(null);

  const [cases, setCases] = useState<CasesResponse | null>(null);
  const [casesLoading, setCasesLoading] = useState(false);
  const [casesError, setCasesError] = useState<string | null>(null);
  const [courtFilter, setCourtFilter] = useState<CourtLevel | "ALL">("ALL");

  const [acts, setActs] = useState<ActSummary[] | null>(null);
  const [actsError, setActsError] = useState<string | null>(null);

  const runId = useRef(0);
  const autoStarted = useRef(false);

  useEffect(() => {
    listActs()
      .then((response) => setActs(response.acts))
      .catch((error) => setActsError(errorMessage(error, "The list of Acts could not be loaded.")));
  }, []);

  const actNames = useMemo(() => {
    const names: Record<string, string> = { ...EXTRA_ACT_NAMES };
    for (const act of acts ?? []) {
      if (act.short_title) names[act.act_id] = act.short_title;
    }
    for (const provision of law?.provisions ?? []) names[provision.act_id] = provision.short_title;
    return names;
  }, [acts, law]);

  const loadCases = useCallback(
    async (value: string, lawKeys: string[] | undefined, refresh: boolean, id: number) => {
      setCasesLoading(true);
      setCasesError(null);
      try {
        const response = await researchCases({ query: value, law_keys: lawKeys, court_levels: courtLevels, refresh });
        if (runId.current === id) setCases(response);
      } catch (error) {
        if (runId.current === id) setCasesError(errorMessage(error, "Case law could not be searched."));
      } finally {
        if (runId.current === id) setCasesLoading(false);
      }
    },
    [courtLevels],
  );

  const runResearch = useCallback(
    async (value: string) => {
      const id = ++runId.current;
      setMode("research");
      setLaw(null);
      setLawError(null);
      setArticulation(null);
      setArticulationError(null);
      setCases(null);
      setCasesError(null);
      setCourtFilter("ALL");
      setLawLoading(true);
      router.replace(`/research?q=${encodeURIComponent(value)}`, { scroll: false });

      let lawKeys: string[] | undefined;
      try {
        const response = await researchLaw(value);
        if (runId.current !== id) return;
        setLaw(response);
        lawKeys = response.law_keys;
      } catch (error) {
        if (runId.current !== id) return;
        setLawError(errorMessage(error, "The statute corpus could not be searched."));
      } finally {
        if (runId.current === id) setLawLoading(false);
      }

      setArticulationLoading(true);
      void articulateLaw(value)
        .then((response) => {
          if (runId.current !== id) return;
          setArticulation(response.articulation);
          setArticulationError(response.error);
        })
        .catch((error) => runId.current === id && setArticulationError(errorMessage(error, "The explanation could not be generated.")))
        .finally(() => runId.current === id && setArticulationLoading(false));

      void loadCases(value, lawKeys, false, id);
    },
    [loadCases, router],
  );

  useEffect(() => {
    if (autoStarted.current || !initialQuery.trim()) return;
    autoStarted.current = true;
    void runResearch(initialQuery.trim());
  }, [initialQuery, runResearch]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed.length >= 2) void runResearch(trimmed);
  }

  function toggleCourt(level: CourtLevel) {
    setCourtLevels((current) =>
      current.includes(level) ? (current.length > 1 ? current.filter((x) => x !== level) : current) : [...current, level],
    );
  }

  const searched = law !== null || lawLoading || lawError !== null;
  const visibleCases = (cases?.cases ?? []).filter((item) => courtFilter === "ALL" || item.court_level === courtFilter);
  const caseCourts = Array.from(new Set((cases?.cases ?? []).map((item) => item.court_level)));

  return (
    <div className="space-y-6">
      <div className="flex rounded-lg bg-[var(--fill)] p-1 sm:w-fit" role="tablist" aria-label="Research mode">
        {(
          [
            ["research", "Research a question"],
            ["browse", "Browse Acts and landmark cases"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={mode === value}
            onClick={() => setMode(value)}
            className={`min-h-9 flex-1 rounded-md px-3 text-sm font-medium ${mode === value ? "bg-[var(--surface)] text-[var(--accent)] shadow-[var(--shadow-soft)]" : "text-[var(--ink-muted)] hover:text-[var(--foreground)]"}`}
          >
            {label}
          </button>
        ))}
      </div>

      {mode === "browse" ? (
        <BrowseActs
          acts={acts}
          actNames={actNames}
          loadError={actsError}
          onResearch={(value) => {
            setQuery(value);
            void runResearch(value);
          }}
        />
      ) : (
        <>
          <form onSubmit={onSubmit} className="panel space-y-3 p-4 sm:p-5">
            <label htmlFor="research-query" className="text-sm font-semibold">
              Section, Act, or legal question
            </label>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                id="research-query"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="e.g. Section 85 BNS, IPC 302, or tenant security deposit not returned"
                className="min-h-11 flex-1 rounded-sm border border-[var(--line)] bg-[var(--background)] px-4 text-sm outline-none focus:border-[var(--accent)]"
              />
              <button type="submit" disabled={lawLoading || query.trim().length < 2} className="btn-primary disabled:opacity-50">
                {lawLoading ? "Researching…" : "Research"}
              </button>
            </div>
            <fieldset className="flex flex-wrap items-center gap-2">
              <legend className="sr-only">Courts to search</legend>
              <span className="text-xs font-medium text-[var(--ink-muted)]">Search judgments from</span>
              {COURT_LEVELS.map(({ value, label }) => (
                <label
                  key={value}
                  className={`inline-flex min-h-8 cursor-pointer items-center gap-1.5 rounded-full border px-3 text-xs font-medium ${courtLevels.includes(value) ? "border-[var(--accent-mid)] bg-[var(--accent-soft)] text-[var(--accent)]" : "border-[var(--line)] text-[var(--ink-muted)]"}`}
                >
                  <input type="checkbox" className="sr-only" checked={courtLevels.includes(value)} onChange={() => toggleCourt(value)} />
                  {label}
                </label>
              ))}
            </fieldset>
          </form>

          {!searched ? (
            <div className="rounded-xl border border-dashed border-[var(--line)] bg-[var(--surface)] px-6 py-10">
              <h2 className="text-center text-lg font-semibold">Start with a section or a situation</h2>
              <p className="mx-auto mt-2 max-w-xl text-center text-sm leading-6 text-[var(--ink-muted)]">
                ChatLaw pulls the provision from its statute corpus, explains it, and finds judgments of the Supreme
                Court, High Courts and District Courts. Every judgment shown links to an official court copy that was
                checked to name the parties. Old IPC, CrPC and Evidence Act sections are mapped to BNS, BNSS and BSA.
              </p>
              <div className="mx-auto mt-5 flex max-w-3xl flex-wrap justify-center gap-2">
                {EXAMPLES.map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => {
                      setQuery(example);
                      void runResearch(example);
                    }}
                    className="rounded-full border border-[var(--line)] bg-[var(--background)] px-3 py-1.5 text-xs font-medium hover:border-[var(--accent-mid)] hover:text-[var(--accent)]"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {searched ? (
            <nav aria-label="Research results" className="flex flex-wrap gap-4 text-sm font-semibold text-[var(--accent)]">
              <a href="#law-heading" className="hover:underline">
                The law{law ? ` (${law.provisions.length} provisions)` : ""}
              </a>
              <a href="#cases-heading" className="hover:underline">
                Case law{casesLoading ? " (searching…)" : cases ? ` (${cases.cases.length} judgments)` : ""}
              </a>
            </nav>
          ) : null}

          {searched ? (
            <section className="space-y-3" aria-labelledby="law-heading">
              <h2 id="law-heading" className="text-lg font-semibold">
                The law
              </h2>
              {law?.notes.map((note) => (
                <p key={note} className="rounded-lg bg-[var(--accent-soft)] px-4 py-2.5 text-sm text-[var(--accent-strong)]">
                  {note}
                </p>
              ))}
              {lawLoading ? (
                <div className="h-32 animate-pulse rounded-xl border border-[var(--line)] bg-[var(--surface)]" aria-busy="true" />
              ) : lawError ? (
                <p role="alert" className="rounded-xl border border-[var(--warn-line)] bg-[var(--warn-bg)] px-5 py-4 text-sm text-[var(--warn)]">
                  {lawError}
                </p>
              ) : law && law.provisions.length === 0 ? (
                <p className="rounded-xl border border-[var(--line)] bg-[var(--surface)] px-5 py-6 text-sm text-[var(--ink-muted)]">
                  No matching provision was found in the statute corpus. Try naming the Act and section, or ask in{" "}
                  <Link href="/chat" className="font-semibold text-[var(--accent)] hover:underline">
                    Chat
                  </Link>
                  .
                </p>
              ) : null}
              {law && law.provisions.length ? (
                <ArticulationCard articulation={articulation} loading={articulationLoading} error={articulationError} />
              ) : null}
              {law ? <ProvisionList provisions={law.provisions} /> : null}
            </section>
          ) : null}

          {searched ? (
            <section className="space-y-3" aria-labelledby="cases-heading">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h2 id="cases-heading" className="text-lg font-semibold">
                    Case law
                  </h2>
                  <p className="mt-1 text-xs text-[var(--ink-muted)]">
                    {casesLoading
                      ? "Checking the ChatLaw case library, then official court websites if needed. A new search can take up to a minute."
                      : cases?.source === "library"
                        ? "From the ChatLaw case library — these judgments were verified when first found."
                        : cases?.source === "official_search" || cases?.source === "mixed"
                          ? `Found on official court websites just now and saved to the library (${cases.verified} of ${cases.proposed} candidates had a verifiable official copy).`
                          : "Judgments are shown only when an official court copy could be verified."}
                  </p>
                </div>
                {caseCourts.length > 1 ? (
                  <select
                    value={courtFilter}
                    onChange={(event) => setCourtFilter(event.target.value as CourtLevel | "ALL")}
                    aria-label="Filter by court"
                    className="min-h-9 rounded-md border border-[var(--line)] bg-[var(--surface)] px-2 text-sm"
                  >
                    <option value="ALL">All courts</option>
                    {COURT_LEVELS.filter(({ value }) => caseCourts.includes(value)).map(({ value, label }) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                ) : null}
              </div>

              {casesLoading ? (
                <div className="space-y-3" aria-busy="true" aria-live="polite">
                  {[0, 1].map((i) => (
                    <div key={i} className="h-36 animate-pulse rounded-xl border border-[var(--line)] bg-[var(--surface)]" />
                  ))}
                </div>
              ) : casesError ? (
                <p role="alert" className="rounded-xl border border-[var(--warn-line)] bg-[var(--warn-bg)] px-5 py-4 text-sm text-[var(--warn)]">
                  {casesError}
                </p>
              ) : cases ? (
                <>
                  {cases.message ? (
                    <p className="rounded-xl border border-[var(--line)] bg-[var(--surface)] px-5 py-4 text-sm text-[var(--ink-muted)]">
                      {cases.message}
                    </p>
                  ) : null}
                  {visibleCases.length ? (
                    <ul className="space-y-3">
                      {visibleCases.map((item) => (
                        <CaseCard key={item.id} item={item} actNames={actNames} />
                      ))}
                    </ul>
                  ) : null}
                  <div className="flex justify-center pt-1">
                    <button
                      type="button"
                      className="btn-secondary btn-sm"
                      onClick={() => void loadCases(law?.query ?? query.trim(), law?.law_keys, true, runId.current)}
                    >
                      Search official court websites again
                    </button>
                  </div>
                </>
              ) : null}
            </section>
          ) : null}
        </>
      )}
    </div>
  );
}
