import Link from "next/link";
import { redirect } from "next/navigation";

import DisclaimerBanner from "@/components/documents/DisclaimerBanner";
import WorkspaceList from "@/components/documents/WorkspaceList";
import { getSessionUser } from "@/lib/auth/session";
import { listOwnedDocuments } from "@/lib/documents/store";

export const dynamic = "force-dynamic";

export default async function DocumentsPage() {
  const user = await getSessionUser();
  if (!user) redirect("/signin?callbackUrl=/documents");
  const documents = await listOwnedDocuments(user.id);

  return (
    <section className="mx-auto w-full max-w-[1200px] space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Documents</h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--ink-muted)]">
            Structured AI drafts for supported agreement types. Review carefully — a draft is not an official filing.
          </p>
        </div>
        <Link
          href="/documents/new"
          className="inline-flex min-h-11 items-center rounded-full bg-[var(--forest)] px-5 text-sm font-semibold text-white"
        >
          New document
        </Link>
      </div>
      <DisclaimerBanner />
      <WorkspaceList documents={documents} />
    </section>
  );
}
