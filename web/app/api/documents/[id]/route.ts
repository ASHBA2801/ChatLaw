import { NextResponse } from "next/server";

import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import {
  currentPayload,
  deleteOwnedDocument,
  DocumentAccessError,
  getOwnedDocument,
  updateOwnedStatus,
} from "@/lib/documents/store";
import { parseStatus } from "@/lib/documents/status";

export const dynamic = "force-dynamic";

function fail(error: unknown) {
  if (error instanceof AuthRequiredError) return NextResponse.json({ error: error.message }, { status: 401 });
  if (error instanceof DocumentAccessError) return NextResponse.json({ error: error.message }, { status: error.status });
  return NextResponse.json({ error: "Request failed" }, { status: 500 });
}

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id } = await context.params;
    const document = await getOwnedDocument(user.id, id);
    const current = currentPayload(document);
    return NextResponse.json({
      id: document.id,
      title: document.title,
      templateId: document.templateId,
      documentType: document.documentType,
      jurisdictionCountry: document.jurisdictionCountry,
      jurisdictionRegion: document.jurisdictionRegion,
      status: document.status,
      currentVersionNumber: document.currentVersionNumber,
      createdAt: document.createdAt,
      updatedAt: document.updatedAt,
      values: current.values,
      document: current.payload,
      versions: document.versions.map((version) => ({
        id: version.id,
        versionNumber: version.versionNumber,
        status: version.status,
        title: version.title,
        createdAt: version.createdAt,
      })),
    });
  } catch (error) {
    return fail(error);
  }
}

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id } = await context.params;
    const body = await request.json();
    if (body.status) {
      const document = await updateOwnedStatus(user.id, id, parseStatus(body.status));
      return NextResponse.json({ id: document.id, status: document.status });
    }
    return NextResponse.json({ error: "No supported update fields" }, { status: 400 });
  } catch (error) {
    return fail(error);
  }
}

export async function DELETE(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id } = await context.params;
    await deleteOwnedDocument(user.id, id);
    return NextResponse.json({ deleted: true });
  } catch (error) {
    return fail(error);
  }
}
