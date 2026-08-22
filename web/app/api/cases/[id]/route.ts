import { NextResponse } from "next/server";
import { requireSessionUser } from "@/lib/auth/session";
import { archiveOwnedCase, getOwnedCase, toPublicCase, updateOwnedCase } from "@/lib/cases/store";
import { caseErrorResponse } from "@/lib/cases/http";

export const dynamic = "force-dynamic";

async function caseId(context: { params: Promise<{ id: string }> }) {
  return (await context.params).id;
}

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    return NextResponse.json({ case: toPublicCase(await getOwnedCase(user.id, await caseId(context))) });
  } catch (error) {
    return caseErrorResponse(error);
  }
}

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    return NextResponse.json({ case: await updateOwnedCase(user.id, await caseId(context), await request.json()) });
  } catch (error) {
    return caseErrorResponse(error);
  }
}

export async function DELETE(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    await archiveOwnedCase(user.id, await caseId(context));
    return NextResponse.json({ archived: true });
  } catch (error) {
    return caseErrorResponse(error);
  }
}
