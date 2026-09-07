import { NextResponse } from "next/server";
import { requireSessionUser } from "@/lib/auth/session";
import { publicCaseDocument } from "@/lib/cases/documents";
import { caseErrorResponse } from "@/lib/cases/http";
import { summarizeOwnedCaseDocument } from "@/lib/cases/summarize";

export const dynamic = "force-dynamic";

export async function POST(_request: Request, context: { params: Promise<{ id: string; docId: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id, docId } = await context.params;
    const document = await summarizeOwnedCaseDocument(user.id, id, docId);
    return NextResponse.json({ document: publicCaseDocument(document) });
  } catch (error) {
    return caseErrorResponse(error, "Document summary failed");
  }
}
