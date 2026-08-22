import { redirect } from "next/navigation";

import NewCaseForm from "@/components/cases/NewCaseForm";
import { getSessionUser } from "@/lib/auth/session";

export default async function NewCasePage() {
  if (!(await getSessionUser())) redirect("/signin?callbackUrl=/cases/new");
  return (
    <section className="mx-auto w-full max-w-2xl px-4 py-8 sm:px-6">
      <h1 className="text-3xl font-semibold tracking-tight">Create a case</h1>
      <p className="mt-2 text-sm text-[var(--ink-muted)]">
        Only add information needed to organize this personal matter.
      </p>
      <NewCaseForm />
    </section>
  );
}
