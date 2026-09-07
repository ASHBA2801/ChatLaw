import { NextResponse } from "next/server";

import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import { addOwnedVersion, DocumentAccessError, getOwnedDocument } from "@/lib/documents/store";
import { parseStatus } from "@/lib/documents/status";
import type { DocumentValues, GeneratedDocumentPayload } from "@/lib/documents/types";

export const dynamic = "force-dynamic";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id } = await context.params;
    await getOwnedDocument(user.id, id);
    const body = await request.json();
    const payload = body.document as GeneratedDocumentPayload | undefined;
    const values = (body.values || {}) as DocumentValues;
    if (!payload?.sections) {
      return NextResponse.json({ error: "A document payload is required to save a version." }, { status: 400 });
    }
    const saved = await addOwnedVersion({
      userId: user.id,
      documentId: id,
      values,
      payload,
      status: body.status ? parseStatus(body.status) : undefined,
    });
    return NextResponse.json({
      id: saved.document.id,
      versionNumber: saved.version.versionNumber,
      status: saved.document.status,
    }, { status: 201 });
  } catch (error) {
    if (error instanceof AuthRequiredError) return NextResponse.json({ error: error.message }, { status: 401 });
    if (error instanceof DocumentAccessError) return NextResponse.json({ error: error.message }, { status: error.status });
    return NextResponse.json({ error: "Request failed" }, { status: 500 });
  }
}
