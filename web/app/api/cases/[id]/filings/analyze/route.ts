import { NextResponse } from "next/server";

import { requireSessionUser } from "@/lib/auth/session";
import { caseErrorResponse } from "@/lib/cases/http";
import { analyzeCaseFacts } from "@/lib/filings/store";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

export async function POST(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    return NextResponse.json(await analyzeCaseFacts(user.id, (await context.params).id));
  } catch (error) {
    return caseErrorResponse(error, "The case could not be analysed");
  }
}
