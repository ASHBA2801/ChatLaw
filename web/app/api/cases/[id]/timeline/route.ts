import { NextResponse } from "next/server";
import { requireSessionUser } from "@/lib/auth/session";
import { caseErrorResponse } from "@/lib/cases/http";
import { addTimelineNote } from "@/lib/cases/timeline";

export const dynamic = "force-dynamic";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const event = await addTimelineNote(user.id, (await context.params).id, await request.json());
    return NextResponse.json({ event }, { status: 201 });
  } catch (error) {
    return caseErrorResponse(error, "Timeline request failed");
  }
}
