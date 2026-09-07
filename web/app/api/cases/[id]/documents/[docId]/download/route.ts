import { NextResponse } from "next/server";
import { requireSessionUser } from "@/lib/auth/session";
import { readOwnedCaseDocumentBytes } from "@/lib/cases/documents";
import { caseErrorResponse } from "@/lib/cases/http";

export const dynamic = "force-dynamic";

function contentDisposition(fileName: string): string {
  const ascii = fileName.replace(/[^\w .()\-]/g, "_");
  return `attachment; filename="${ascii}"; filename*=UTF-8''${encodeURIComponent(fileName)}`;
}

export async function GET(_request: Request, context: { params: Promise<{ id: string; docId: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id, docId } = await context.params;
    const { document, bytes } = await readOwnedCaseDocumentBytes(user.id, id, docId);
    return new NextResponse(new Uint8Array(bytes), {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": contentDisposition(document.fileName),
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store",
      },
    });
  } catch (error) {
    return caseErrorResponse(error, "Document download failed");
  }
}
