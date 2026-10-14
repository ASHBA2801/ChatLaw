import { NextResponse } from "next/server";

import { requireSessionUser } from "@/lib/auth/session";
import { caseErrorResponse } from "@/lib/cases/http";
import { draftCaseFiling, getFilingWorkspace } from "@/lib/filings/store";

export const dynamic = "force-dynamic";
// Drafting runs statute retrieval and a model call; contact discovery may precede it.
export const maxDuration = 180;

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    return NextResponse.json(await getFilingWorkspace(user.id, (await context.params).id));
  } catch (error) {
    return caseErrorResponse(error, "Filings could not be loaded");
  }
}

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const filing = await draftCaseFiling(user.id, (await context.params).id, await request.json());
    return NextResponse.json({ filing }, { status: 201 });
  } catch (error) {
    return caseErrorResponse(error, "The document could not be drafted");
  }
}
