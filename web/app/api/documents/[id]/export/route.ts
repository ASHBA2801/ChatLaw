import { NextResponse } from "next/server";

import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import { buildDocx } from "@/lib/documents/export/docx";
import { buildPdf } from "@/lib/documents/export/pdf";
import { currentPayload, DocumentAccessError, getOwnedDocument } from "@/lib/documents/store";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id } = await context.params;
    const format = new URL(request.url).searchParams.get("format") || "pdf";
    const document = await getOwnedDocument(user.id, id);
    const current = currentPayload(document);
    const safeName = document.title.replace(/[^\w\s-]+/g, "").trim() || "chatlaw-document";
    if (format === "docx") {
      const buffer = await buildDocx(current.payload);
      return new NextResponse(new Uint8Array(buffer), {
        headers: {
          "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          "Content-Disposition": `attachment; filename="${safeName}.docx"`,
        },
      });
    }
    if (format === "pdf") {
      const bytes = await buildPdf(current.payload);
      return new NextResponse(Buffer.from(bytes), {
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": `attachment; filename="${safeName}.pdf"`,
        },
      });
    }
    return NextResponse.json({ error: "Supported export formats are pdf and docx." }, { status: 400 });
  } catch (error) {
    if (error instanceof AuthRequiredError) return NextResponse.json({ error: error.message }, { status: 401 });
    if (error instanceof DocumentAccessError) return NextResponse.json({ error: error.message }, { status: error.status });
    return NextResponse.json({ error: "Export failed" }, { status: 500 });
  }
}
