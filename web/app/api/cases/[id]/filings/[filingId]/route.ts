import { NextResponse } from "next/server";

import { requireSessionUser } from "@/lib/auth/session";
import { caseErrorResponse } from "@/lib/cases/http";
import { deleteOwnedFiling, getOwnedFiling, updateOwnedFiling } from "@/lib/filings/store";

export const dynamic = "force-dynamic";

type Context = { params: Promise<{ id: string; filingId: string }> };

export async function GET(_request: Request, context: Context) {
  try {
    const user = await requireSessionUser();
    const { id, filingId } = await context.params;
    return NextResponse.json({ filing: await getOwnedFiling(user.id, id, filingId) });
  } catch (error) {
    return caseErrorResponse(error, "The document could not be loaded");
  }
}

export async function PATCH(request: Request, context: Context) {
  try {
    const user = await requireSessionUser();
    const { id, filingId } = await context.params;
    return NextResponse.json({ filing: await updateOwnedFiling(user.id, id, filingId, await request.json()) });
  } catch (error) {
    return caseErrorResponse(error, "The document could not be saved");
  }
}

export async function DELETE(_request: Request, context: Context) {
  try {
    const user = await requireSessionUser();
    const { id, filingId } = await context.params;
    await deleteOwnedFiling(user.id, id, filingId);
    return NextResponse.json({ ok: true });
  } catch (error) {
    return caseErrorResponse(error, "The document could not be deleted");
  }
}
