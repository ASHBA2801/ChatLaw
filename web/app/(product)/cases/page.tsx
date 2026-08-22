import Link from "next/link";
import { redirect } from "next/navigation";

import CasesDashboard from "@/components/cases/CasesDashboard";
import { getSessionUser } from "@/lib/auth/session";
import { listOwnedCases } from "@/lib/cases/store";

export const dynamic = "force-dynamic";

export default async function CasesPage() {
  const user = await getSessionUser();
  if (!user) redirect("/signin?callbackUrl=/cases");
  const cases = await listOwnedCases(user.id);
  return (
    <section className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">My cases</h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-[var(--ink-muted)]">
            Your personal legal matters — documents, dates, timeline, and case-scoped questions in one workspace.
          </p>
        </div>
        <Link
          href="/cases/new"
          className="inline-flex min-h-11 items-center rounded-full bg-[var(--forest)] px-5 text-sm font-semibold text-white"
        >
          + New case
        </Link>
      </div>
      <div className="mt-6">
        <CasesDashboard cases={cases} />
      </div>
    </section>
  );
}
