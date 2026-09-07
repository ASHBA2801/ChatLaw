import { NextResponse } from "next/server";
import { requireSessionUser } from "@/lib/auth/session";
import { askAboutOwnedCase } from "@/lib/cases/ask";
import { caseErrorResponse } from "@/lib/cases/http";

export const dynamic = "force-dynamic";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const body = await request.json() as { message?: unknown; conversationId?: unknown; case_context?: unknown; language?: unknown };
    if (body.case_context !== undefined) {
      return NextResponse.json({ error: "Case context cannot be supplied by the client." }, { status: 400 });
    }
    if (typeof body.message !== "string" || !body.message.trim()) {
      return NextResponse.json({ error: "A question is required." }, { status: 422 });
    }
    const result = await askAboutOwnedCase({
      userId: user.id,
      caseId: (await context.params).id,
      message: body.message,
      conversationId: typeof body.conversationId === "string" ? body.conversationId : null,
      language: typeof body.language === "string" ? body.language : "en",
    });
    return NextResponse.json(result);
  } catch (error) {
    return caseErrorResponse(error, "Case question failed");
  }
}
