import { NextResponse } from "next/server";

import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import { selectionEdit, RagDocumentError } from "@/lib/documents/rag";
import { currentPayload, DocumentAccessError, getOwnedDocument } from "@/lib/documents/store";

export const dynamic = "force-dynamic";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id } = await context.params;
    const document = await getOwnedDocument(user.id, id);
    const current = currentPayload(document);
    const body = await request.json();
    const selectedText = String(body.selectedText || body.selected_text || "").trim();
    const action = String(body.action || "").trim();
    if (!selectedText || !action) {
      return NextResponse.json({ error: "Selected text and an action are required." }, { status: 400 });
    }

    const surrounding =
      (body.surroundingSection || body.surrounding_section || {}) as Record<string, unknown>;

    const result = await selectionEdit({
      selected_text: selectedText,
      action,
      surrounding_section: surrounding,
      document_title: current.payload.title,
      jurisdiction: `India${current.payload.jurisdiction_region ? ` — ${current.payload.jurisdiction_region}` : ""}`,
      custom_instruction: String(body.customInstruction || body.custom_instruction || ""),
      language: String(body.language || "en"),
      use_model: body.use_model !== false,
    });

    return NextResponse.json({
      proposalOnly: true,
      suggestion: result.suggestion ?? "",
      explanation: result.explanation ?? "",
      preservesCitations: result.preserves_citations !== false,
      generation: result.generation,
    });
  } catch (error) {
    if (error instanceof AuthRequiredError) return NextResponse.json({ error: error.message }, { status: 401 });
    if (error instanceof DocumentAccessError || error instanceof RagDocumentError) {
      return NextResponse.json({ error: error.message, detail: "payload" in error ? error.payload : undefined }, { status: error.status });
    }
    return NextResponse.json({ error: "Request failed" }, { status: 500 });
  }
}
