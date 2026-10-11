import Link from "next/link";

import { STATUS_LABELS } from "@/lib/documents/constants";

type DocumentRow = {
  id: string;
  title: string;
  documentType: string;
  status: keyof typeof STATUS_LABELS | string;
  currentVersionNumber: number;
  createdAt: Date | string;
  updatedAt: Date | string;
  jurisdictionRegion: string | null;
};

function formatDate(value: Date | string) {
  return new Date(value).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export default function WorkspaceList({ documents }: { documents: DocumentRow[] }) {
  if (documents.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[var(--line-strong)] bg-[var(--surface)] px-6 py-14 text-center">
        <h2 className="text-lg font-semibold">No drafts yet</h2>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[var(--ink-muted)]">
          Start from a supported template. You will enter the parties and terms first; ChatLaw will then assemble a structured draft for review.
        </p>
        <Link href="/documents/new" className="btn-primary mt-6">
          Create a document
        </Link>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--surface)] shadow-[var(--shadow-soft)]">
      <table className="w-full text-left text-sm">
        <caption className="sr-only">Saved legal drafts</caption>
        <thead className="border-b border-[var(--line)] bg-[var(--fill)] text-xs text-[var(--ink-muted)]">
          <tr>
            <th scope="col" className="px-4 py-3 font-medium">Document</th>
            <th scope="col" className="hidden px-4 py-3 font-medium sm:table-cell">Type</th>
            <th scope="col" className="px-4 py-3 font-medium">Status</th>
            <th scope="col" className="hidden px-4 py-3 font-medium md:table-cell">Version</th>
            <th scope="col" className="hidden px-4 py-3 font-medium lg:table-cell">Updated</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((document) => (
            <tr key={document.id} className="border-b border-[var(--line)] last:border-0 hover:bg-[var(--background)]">
              <th scope="row" className="px-4 py-4 font-medium">
                <Link href={`/documents/${document.id}`} className="text-[var(--foreground)] hover:text-[var(--accent)]">
                  {document.title}
                </Link>
                <p className="mt-1 text-xs font-normal text-[var(--ink-muted)] sm:hidden">{document.documentType}</p>
              </th>
              <td className="hidden px-4 py-4 sm:table-cell">{document.documentType}</td>
              <td className="px-4 py-4"><span className="inline-flex rounded-full bg-[var(--fill)] px-2.5 py-0.5 text-xs font-medium text-[var(--ink-muted)]">{STATUS_LABELS[document.status as keyof typeof STATUS_LABELS] ?? document.status}</span></td>
              <td className="hidden px-4 py-4 md:table-cell">{document.currentVersionNumber}</td>
              <td className="hidden px-4 py-4 lg:table-cell">{formatDate(document.updatedAt)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
