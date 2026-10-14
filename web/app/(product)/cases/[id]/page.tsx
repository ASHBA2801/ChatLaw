import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import CaseDetail from "@/components/cases/CaseDetail";
import FilingStudio from "@/components/filings/FilingStudio";
import { getSessionUser } from "@/lib/auth/session";
import { getOwnedCase, toPublicCase } from "@/lib/cases/store";
import { getFilingWorkspace } from "@/lib/filings/store";

export const dynamic = "force-dynamic";

export default async function CasePage({ params }: { params: Promise<{ id: string }> }) {
  const user = await getSessionUser();
  if (!user) redirect(`/signin?callbackUrl=/cases/${(await params).id}`);
  const item = await getOwnedCase(user.id, (await params).id).catch(() => null);
  if (!item) notFound();
  const publicItem = toPublicCase(item);
  const workspace = await getFilingWorkspace(user.id, item.id);
  return (
    <section className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6 lg:px-8">
      <Link href="/cases" className="text-sm font-medium text-[var(--accent)] underline-offset-2 hover:underline">
        ← All cases
      </Link>
      <div className="mt-5">
        <h1 className="text-3xl font-semibold tracking-tight">{item.title}</h1>
        <p className="mt-2 text-sm text-[var(--ink-muted)]">
          {[item.category, item.subCategory].filter(Boolean).join(" / ") || "Category not specified"}
          {" · "}
          {[item.locality, item.city, item.district, item.state].filter(Boolean).join(", ") || item.country || "Location not specified"}
        </p>
      </div>
      <FilingStudio caseId={item.id} initial={JSON.parse(JSON.stringify(workspace))} />
      <CaseDetail item={JSON.parse(JSON.stringify(publicItem))} />
    </section>
  );
}
