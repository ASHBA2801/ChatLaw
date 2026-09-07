import Link from "next/link";
import { redirect } from "next/navigation";

import DisclaimerBanner from "@/components/documents/DisclaimerBanner";
import DocumentsHero from "@/components/documents/DocumentsHero";
import WorkspaceList from "@/components/documents/WorkspaceList";
import { getSessionUser } from "@/lib/auth/session";
import { listOwnedDocuments } from "@/lib/documents/store";

export const dynamic = "force-dynamic";

export default async function DocumentsPage() {
  const user = await getSessionUser();
  if (!user) redirect("/signin?callbackUrl=/documents");
  const documents = await listOwnedDocuments(user.id);

  return (
    <section className="mx-auto w-full max-w-[1200px] space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-[var(--foreground)]">
            Legal Documents
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--ink-muted)]">
            Draft authentic Indian agreements, deeds, notices, complaints, and affidavits using official model formats and natural language.
          </p>
        </div>
        <Link
          href="/documents/new"
          className="inline-flex min-h-11 items-center rounded-sm bg-[var(--forest)] px-5 text-sm font-semibold text-white hover:opacity-95"
        >
          New Document Draft
        </Link>
      </div>

      <DisclaimerBanner />

      {/* Primary Conversational Intake & Category Cards */}
      <DocumentsHero />

      {/* Recent Workspace Documents */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold tracking-tight text-[var(--foreground)]">
            Your Workspace Documents
          </h2>
          <span className="text-xs text-[var(--ink-muted)]">
            {documents.length} draft{documents.length === 1 ? "" : "s"}
          </span>
        </div>
        <WorkspaceList documents={documents} />
      </div>
    </section>
  );
}
