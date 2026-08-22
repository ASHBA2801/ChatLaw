import { NextResponse } from "next/server";
import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import { addCaseDocument, deleteCaseDocument, publicCaseDocument } from "@/lib/cases/documents";
import { getOwnedCase } from "@/lib/cases/store";
import { caseErrorResponse } from "@/lib/cases/http";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const item = await getOwnedCase(user.id, (await context.params).id);
    return NextResponse.json({ documents: item.documents.map(publicCaseDocument) });
  } catch (error) {
    return caseErrorResponse(error, "Document request failed");
  }
}

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const form = await request.formData();
    const file = form.get("file");
    if (!(file instanceof File)) {
      return NextResponse.json({ error: "A PDF file is required." }, { status: 422 });
    }
    const document = await addCaseDocument(user.id, (await context.params).id, file);
    return NextResponse.json({ document: publicCaseDocument(document) }, { status: 201 });
  } catch (error) {
    return caseErrorResponse(error, "Document request failed");
  }
}

export async function DELETE(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const body = await request.json();
    await deleteCaseDocument(user.id, (await context.params).id, String(body.documentId || ""));
    return NextResponse.json({ deleted: true });
  } catch (error) {
    if (error instanceof AuthRequiredError) {
      return caseErrorResponse(error);
    }
    return caseErrorResponse(error, "Document request failed");
  }
}
