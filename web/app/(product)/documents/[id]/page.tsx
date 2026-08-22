import { notFound, redirect } from "next/navigation";

import DocumentEditor from "@/components/documents/DocumentEditor";
import { getSessionUser } from "@/lib/auth/session";
import { currentPayload, DocumentAccessError, getOwnedDocument } from "@/lib/documents/store";
import type { DocumentStatus } from "@/lib/documents/types";

export const dynamic = "force-dynamic";

export default async function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await getSessionUser();
  if (!user) redirect("/signin?callbackUrl=/documents");
  const { id } = await params;
  let document;
  try {
    document = await getOwnedDocument(user.id, id);
  } catch (error) {
    if (error instanceof DocumentAccessError && error.status === 404) notFound();
    throw error;
  }
  const current = currentPayload(document);
  return (
    <section className="mx-auto w-full max-w-[1200px] px-4 py-6 sm:px-6 lg:px-8">
      <DocumentEditor
        documentId={document.id}
        initialStatus={document.status as DocumentStatus}
        initialValues={current.values}
        initialDocument={current.payload}
        versions={document.versions.map((version) => ({
          id: version.id,
          versionNumber: version.versionNumber,
          status: version.status,
          title: version.title,
          createdAt: version.createdAt.toISOString(),
        }))}
      />
    </section>
  );
}
