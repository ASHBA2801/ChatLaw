import { NextResponse } from "next/server";
import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import { createOwnedCase, listOwnedCases } from "@/lib/cases/store";
import { caseErrorResponse } from "@/lib/cases/http";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const user = await requireSessionUser();
    return NextResponse.json({ cases: await listOwnedCases(user.id) });
  } catch (error) {
    return caseErrorResponse(error);
  }
}

export async function POST(request: Request) {
  try {
    const user = await requireSessionUser();
    return NextResponse.json({ case: await createOwnedCase(user.id, await request.json()) }, { status: 201 });
  } catch (error) {
    if (error instanceof AuthRequiredError) return caseErrorResponse(error);
    return caseErrorResponse(error);
  }
}
