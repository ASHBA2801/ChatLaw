import { Suspense } from "react";
import { redirect } from "next/navigation";

import DocumentBuilder from "@/components/documents/DocumentBuilder";
import { getSessionUser } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

export default async function NewDocumentPage() {
  const user = await getSessionUser();
  if (!user) redirect("/signin?callbackUrl=/documents/new");

  return (
    <section className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6 lg:px-8">
      <Suspense fallback={<div className="h-40 animate-pulse rounded-sm border border-[var(--line)] bg-white" />}>
        <DocumentBuilder />
      </Suspense>
    </section>
  );
}
