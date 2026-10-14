import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import FilingDocument, { type FilingView } from "@/components/filings/FilingDocument";
import { getSessionUser } from "@/lib/auth/session";
import { getOwnedFiling } from "@/lib/filings/store";
import { FILING_STATUSES, kindLabel, type FilingStatus } from "@/lib/filings/types";

export const dynamic = "force-dynamic";

function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

export default async function FilingPage({ params }: { params: Promise<{ id: string; filingId: string }> }) {
  const { id, filingId } = await params;
  const user = await getSessionUser();
  if (!user) redirect(`/signin?callbackUrl=/cases/${id}/filings/${filingId}`);
  const filing = await getOwnedFiling(user.id, id, filingId).catch(() => null);
  if (!filing) notFound();

  const recipients = (filing.recipients ?? {}) as { to?: unknown; recipient?: { name?: string } | null };
  const view: FilingView = {
    id: filing.id,
    caseId: filing.caseId,
    kind: filing.kind,
    forum: filing.forum,
    title: filing.title,
    subject: filing.subject,
    body: filing.body,
    emailBody: filing.emailBody,
    to: strings(recipients.to),
    cc: strings(filing.cc),
    status: (FILING_STATUSES as readonly string[]).includes(filing.status) ? (filing.status as FilingStatus) : "DRAFT",
    warnings: strings(filing.warnings),
    placeholders: strings(filing.placeholders),
    citations: Array.isArray(filing.citations) ? (filing.citations as FilingView["citations"]) : [],
    filing: (filing.filing ?? {}) as FilingView["filing"],
    recipientName: recipients.recipient?.name ?? null,
    language: filing.language,
    createdAt: filing.createdAt.toISOString(),
  };

  return (
    <section className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6 lg:px-8">
      <Link href={`/cases/${id}`} className="text-sm font-medium text-[var(--accent)] underline-offset-2 hover:underline print:hidden">
        ← Back to case
      </Link>
      <div className="mt-4 print:hidden">
        <h1 className="text-2xl font-semibold tracking-tight [text-wrap:balance]">{filing.title}</h1>
        <p className="mt-1 text-sm text-[var(--ink-muted)]">
          {kindLabel(filing.kind)} · drafted {filing.createdAt.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
        </p>
      </div>
      <FilingDocument filing={view} />
    </section>
  );
}
