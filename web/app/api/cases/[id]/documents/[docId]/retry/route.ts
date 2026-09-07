import { NextResponse } from "next/server";
import { requireSessionUser } from "@/lib/auth/session";
import { publicCaseDocument, retryCaseDocumentExtraction } from "@/lib/cases/documents";
import { caseErrorResponse } from "@/lib/cases/http";

export const dynamic = "force-dynamic";

export async function POST(_request: Request, context: { params: Promise<{ id: string; docId: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id, docId } = await context.params;
    const document = await retryCaseDocumentExtraction(user.id, id, docId);
    return NextResponse.json({ document: publicCaseDocument(document) });
  } catch (error) {
    return caseErrorResponse(error, "Document retry failed");
  }
}
