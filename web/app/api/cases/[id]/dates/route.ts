import { NextResponse } from "next/server";
import { requireSessionUser } from "@/lib/auth/session";
import { createImportantDate, listImportantDates } from "@/lib/cases/dates";
import { caseErrorResponse } from "@/lib/cases/http";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    return NextResponse.json({ dates: await listImportantDates(user.id, (await context.params).id) });
  } catch (error) {
    return caseErrorResponse(error, "Date request failed");
  }
}

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const item = await createImportantDate(user.id, (await context.params).id, await request.json());
    return NextResponse.json({ date: item }, { status: 201 });
  } catch (error) {
    return caseErrorResponse(error, "Date request failed");
  }
}
