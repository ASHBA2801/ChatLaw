import { NextResponse } from "next/server";

import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import { addOwnedVersion, currentPayload, DocumentAccessError, getOwnedDocument } from "@/lib/documents/store";

export const dynamic = "force-dynamic";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id } = await context.params;
    const document = await getOwnedDocument(user.id, id);
    const body = await request.json();
    const versionNumber = Number(body.versionNumber);
    const version = document.versions.find((item) => item.versionNumber === versionNumber);
    if (!version) {
      return NextResponse.json({ error: "Version not found" }, { status: 404 });
    }
    const current = currentPayload({ ...document, currentVersionNumber: version.versionNumber, versions: [version, ...document.versions] });
    const restored = await addOwnedVersion({
      userId: user.id,
      documentId: id,
      values: current.values,
      payload: current.payload,
    });
    return NextResponse.json({
      id: restored.document.id,
      versionNumber: restored.version.versionNumber,
      restoredFrom: versionNumber,
    }, { status: 201 });
  } catch (error) {
    if (error instanceof AuthRequiredError) return NextResponse.json({ error: error.message }, { status: 401 });
    if (error instanceof DocumentAccessError) return NextResponse.json({ error: error.message }, { status: error.status });
    return NextResponse.json({ error: "Request failed" }, { status: 500 });
  }
}
