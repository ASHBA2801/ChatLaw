import { NextResponse } from "next/server";
import { requireSessionUser } from "@/lib/auth/session";
import { getOwnedCaseDocument, publicCaseDocument, renameCaseDocument } from "@/lib/cases/documents";
import { caseErrorResponse } from "@/lib/cases/http";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ id: string; docId: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id, docId } = await context.params;
    const document = await getOwnedCaseDocument(user.id, id, docId);
    return NextResponse.json({
      document: {
        ...publicCaseDocument(document),
        extractedText: document.extractedText,
      },
    });
  } catch (error) {
    return caseErrorResponse(error, "Document request failed");
  }
}

export async function PATCH(request: Request, context: { params: Promise<{ id: string; docId: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id, docId } = await context.params;
    const body = await request.json() as { fileName?: unknown };
    if (typeof body.fileName !== "string") {
      return NextResponse.json({ error: "A filename is required." }, { status: 422 });
    }
    const document = await renameCaseDocument(user.id, id, docId, body.fileName);
    return NextResponse.json({ document: publicCaseDocument(document) });
  } catch (error) {
    return caseErrorResponse(error, "Document request failed");
  }
}
