import { NextResponse } from "next/server";
import { requireSessionUser } from "@/lib/auth/session";
import { deleteImportantDate, updateImportantDate } from "@/lib/cases/dates";
import { caseErrorResponse } from "@/lib/cases/http";

export const dynamic = "force-dynamic";

export async function PATCH(request: Request, context: { params: Promise<{ id: string; dateId: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id, dateId } = await context.params;
    return NextResponse.json({ date: await updateImportantDate(user.id, id, dateId, await request.json()) });
  } catch (error) {
    return caseErrorResponse(error, "Date request failed");
  }
}

export async function DELETE(_request: Request, context: { params: Promise<{ id: string; dateId: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id, dateId } = await context.params;
    await deleteImportantDate(user.id, id, dateId);
    return NextResponse.json({ deleted: true });
  } catch (error) {
    return caseErrorResponse(error, "Date request failed");
  }
}
