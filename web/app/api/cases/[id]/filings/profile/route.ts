import { NextResponse } from "next/server";

import { requireSessionUser } from "@/lib/auth/session";
import { caseErrorResponse } from "@/lib/cases/http";
import { saveFilingProfile } from "@/lib/filings/store";

export const dynamic = "force-dynamic";

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    return NextResponse.json(await saveFilingProfile(user.id, (await context.params).id, await request.json()));
  } catch (error) {
    return caseErrorResponse(error, "Your details could not be saved");
  }
}
