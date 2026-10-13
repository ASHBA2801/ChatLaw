"use client";

import { useState } from "react";

import type { Articulation, Provision } from "@/lib/api/research";
import { isSafeExternalUrl } from "@/lib/urls/safeUrl";

function BulletList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <h4 className="text-sm font-semibold">{title}</h4>
      <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm leading-6 text-[var(--foreground)]">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export function ArticulationCard({
  articulation,
  loading,
  error,
}: {
  articulation: Articulation | null;
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return (
      <div className="panel space-y-3 p-5" aria-busy="true">
        <p className="text-sm text-[var(--ink-muted)]">Explaining the law from the statutory text…</p>
        <div className="h-3 w-11/12 animate-pulse rounded bg-[var(--fill)]" />
        <div className="h-3 w-10/12 animate-pulse rounded bg-[var(--fill)]" />
        <div className="h-3 w-8/12 animate-pulse rounded bg-[var(--fill)]" />
      </div>
    );
  }
  if (!articulation) {
    return error ? (
      <p className="rounded-xl border border-[var(--caution-line)] bg-[var(--caution-bg)] px-4 py-3 text-sm text-[var(--caution)]">
        {error}
      </p>
    ) : null;
  }
  return (
    <div className="panel space-y-4 p-5">
      <div>
        <h3 className="text-base font-semibold">What the law says</h3>
        <p className="mt-2 text-[0.9375rem] leading-7">{articulation.overview}</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <BulletList title="Essential ingredients" items={articulation.elements} />
        <BulletList title="Key points" items={articulation.key_points} />
        <BulletList title="Punishment, penalty or remedy" items={articulation.consequences} />
        <BulletList title="Exceptions and defences" items={articulation.exceptions} />
        <BulletList title="Related provisions" items={articulation.related_provisions} />
        <BulletList title="Typical next steps" items={articulation.practical_steps} />
      </div>
      <p className="text-xs leading-5 text-[var(--ink-faint)]">
        AI explanation written only from {articulation.sources.join("; ")}. It is legal information, not legal
        advice. Read the provision text below before relying on it.
      </p>
    </div>
  );
}

function ProvisionItem({ provision }: { provision: Provision }) {
  const [open, setOpen] = useState(false);
  const sourceUrl = isSafeExternalUrl(provision.source_url);
  // Sections named in the search get a longer preview than related ones.
  const previewLength = provision.matched_by === "reference" ? 1200 : 360;
  const preview = provision.text.length > previewLength ? `${provision.text.slice(0, previewLength)}…` : provision.text;
  return (
    <li className="py-4 first:pt-0 last:pb-0">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h4 className="text-[0.9375rem] font-semibold leading-6">{provision.label}</h4>
          <p className="mt-0.5 text-xs text-[var(--ink-muted)]">
            {[
              provision.act_title,
              provision.chapter,
              provision.translated_from ? `Replaces ${provision.translated_from}` : null,
              provision.matched_by === "reference"
                ? "Named in your search"
                : provision.similarity != null
                  ? `Related · ${(provision.similarity * 100).toFixed(0)}% match`
                  : "Related",
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
        {sourceUrl ? (
          <a href={sourceUrl} target="_blank" rel="noreferrer" className="text-xs font-semibold text-[var(--accent)] hover:underline">
            Official Act ↗
          </a>
        ) : null}
      </div>
      <p className="mt-2 whitespace-pre-line font-[family-name:var(--font-doc)] text-sm leading-6 text-[var(--foreground)]">
        {open ? provision.text : preview}
      </p>
      {provision.text.length > previewLength ? (
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="mt-1 text-xs font-semibold text-[var(--accent)] hover:underline"
          aria-expanded={open}
        >
          {open ? "Show less" : "Read full section"}
        </button>
      ) : null}
    </li>
  );
}

export function ProvisionList({ provisions }: { provisions: Provision[] }) {
  if (!provisions.length) return null;
  return (
    <div className="panel p-5">
      <h3 className="text-base font-semibold">Statutory text</h3>
      <p className="mt-1 text-xs text-[var(--ink-muted)]">Retrieved directly from the ChatLaw statute corpus.</p>
      <ul className="mt-4 divide-y divide-[var(--line)]">
        {provisions.map((provision, index) => (
          <ProvisionItem key={`${provision.law_key}-${index}`} provision={provision} />
        ))}
      </ul>
    </div>
  );
}
