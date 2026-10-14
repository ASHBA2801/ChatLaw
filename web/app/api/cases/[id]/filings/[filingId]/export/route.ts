import { NextResponse } from "next/server";

import { requireSessionUser } from "@/lib/auth/session";
import { caseErrorResponse } from "@/lib/cases/http";
import { buildFilingDocx } from "@/lib/filings/docx";
import { getOwnedFiling } from "@/lib/filings/store";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(_request: Request, context: { params: Promise<{ id: string; filingId: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id, filingId } = await context.params;
    const filing = await getOwnedFiling(user.id, id, filingId);
    const disclaimer = (filing.filing as { disclaimer?: string } | null)?.disclaimer ?? null;
    const buffer = await buildFilingDocx({ title: filing.title, body: filing.body, disclaimer });
    const safeName = filing.title.replace(/[^\w\s-]+/g, "").trim().slice(0, 80) || "chatlaw-complaint";
    return new NextResponse(new Uint8Array(buffer), {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "Content-Disposition": `attachment; filename="${safeName}.docx"`,
      },
    });
  } catch (error) {
    return caseErrorResponse(error, "Export failed");
  }
}
