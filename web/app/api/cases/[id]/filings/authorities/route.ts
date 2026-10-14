import { NextResponse } from "next/server";

import { requireSessionUser } from "@/lib/auth/session";
import { caseErrorResponse } from "@/lib/cases/http";
import { lookupAuthorities } from "@/lib/filings/store";

export const dynamic = "force-dynamic";
// Official-site contact discovery can take a while on a cold cache.
export const maxDuration = 180;

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    return NextResponse.json(await lookupAuthorities(user.id, (await context.params).id, await request.json()));
  } catch (error) {
    return caseErrorResponse(error, "Offices could not be looked up");
  }
}
