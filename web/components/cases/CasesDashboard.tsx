"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

type CaseRow = {
  id: string;
  title: string;
  category: string | null;
  city: string | null;
  state: string | null;
  status: string;
  updatedAt: Date | string;
  _count: { documents: number; timeline: number };
};

const STATUSES = ["ALL", "ACTIVE", "ON_HOLD", "RESOLVED", "ARCHIVED"] as const;
type SortKey = "updated" | "title" | "status";

const CONTROL =
  "h-11 w-full rounded-sm border border-[var(--line)] bg-white px-3 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]";

function relativeUpdate(value: Date | string) {
  const time = new Date(value).getTime();
  if (Number.isNaN(time)) return "Updated unknown";
  const diff = Date.now() - time;
  if (diff < 86_400_000) return "Updated recently";
  return `Updated ${new Date(value).toLocaleDateString("en-IN")}`;
}

export default function CasesDashboard({ cases }: { cases: CaseRow[] }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<(typeof STATUSES)[number]>("ALL");
  const [sort, setSort] = useState<SortKey>("updated");

  const categories = useMemo(
    () => [...new Set(cases.map((item) => item.category).filter(Boolean))] as string[],
    [cases],
  );
  const [category, setCategory] = useState("ALL");

  const visible = useMemo(() => {
    const needle = query.toLowerCase().trim();
    const filtered = cases.filter((item) => {
      const haystack = `${item.title} ${item.category || ""} ${item.city || ""} ${item.state || ""}`.toLowerCase();
      const matchesQuery = !needle || haystack.includes(needle);
      const matchesStatus = status === "ALL" || item.status === status;
      const matchesCategory = category === "ALL" || item.category === category;
      return matchesQuery && matchesStatus && matchesCategory;
    });
    return filtered.sort((left, right) => {
      if (sort === "title") return left.title.localeCompare(right.title);
      if (sort === "status") return left.status.localeCompare(right.status);
      return new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime();
    });
  }, [cases, query, status, category, sort]);

  return (
    <div className="mt-8">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_auto_auto_auto]">
        <label className="block sm:col-span-2 lg:col-span-1">
          <span className="sr-only">Search cases</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search cases..."
            className={CONTROL}
            autoComplete="off"
          />
        </label>
        <label className="text-sm">
          <span className="sr-only">Filter by status</span>
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value as (typeof STATUSES)[number])}
            className={CONTROL}
          >
            {STATUSES.map((item) => (
              <option key={item} value={item}>
                {item === "ALL" ? "All statuses" : item.replace("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="sr-only">Filter by category</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)} className={CONTROL}>
            <option value="ALL">All categories</option>
            {categories.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="sr-only">Sort cases</span>
          <select value={sort} onChange={(event) => setSort(event.target.value as SortKey)} className={CONTROL}>
            <option value="updated">Last updated</option>
            <option value="title">Title</option>
            <option value="status">Status</option>
          </select>
        </label>
      </div>

      {visible.length === 0 ? (
        <div className="mt-6 rounded-sm border border-[var(--line)] bg-white px-6 py-16 text-center">
          <h2 className="text-xl font-semibold">
            {cases.length ? "No matching cases" : "You don't have any cases yet."}
          </h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-[var(--ink-muted)]">
            {cases.length
              ? "Try a different search or filter."
              : "Create a private workspace for a legal matter, upload PDFs, track dates, and ask grounded questions."}
          </p>
          {!cases.length ? (
            <Link
              href="/cases/new"
              className="mt-6 inline-flex min-h-11 items-center rounded-sm bg-[var(--forest)] px-5 text-sm font-semibold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
            >
              Create Case
            </Link>
          ) : (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setStatus("ALL");
                setCategory("ALL");
              }}
              className="mt-6 inline-flex min-h-11 items-center rounded-sm border border-[var(--forest)] px-4 text-sm font-semibold text-[var(--forest)]"
            >
              Clear filters
            </button>
          )}
        </div>
      ) : (
        <ul className="mt-6 grid list-none gap-4 md:grid-cols-2">
          {visible.map((item) => (
            <li key={item.id}>
              <article className="h-full rounded-sm border border-[var(--line)] bg-white p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h2 className="truncate text-lg font-semibold" title={item.title}>
                      {item.title}
                    </h2>
                    <p className="mt-1 text-sm text-[var(--ink-muted)]">
                      {item.category || "Category not specified"}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-sm bg-[var(--signal-soft)] px-3 py-1 text-xs font-semibold text-[var(--forest)]">
                    {item.status.replace("_", " ")}
                  </span>
                </div>
                <p className="mt-4 text-sm">
                  {[item.city, item.state].filter(Boolean).join(", ") || "Jurisdiction not specified"}
                </p>
                <p className="mt-2 text-xs text-[var(--ink-muted)]">
                  {item._count.documents} document{item._count.documents === 1 ? "" : "s"} ·{" "}
                  {relativeUpdate(item.updatedAt)}
                </p>
                <Link
                  href={`/cases/${item.id}`}
                  className="mt-5 inline-flex min-h-11 items-center rounded-sm border border-[var(--forest)] px-4 text-sm font-semibold text-[var(--forest)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
                >
                  Open Case
                </Link>
              </article>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
