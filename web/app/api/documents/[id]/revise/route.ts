import { NextResponse } from "next/server";

import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import { reviseDocument, RagDocumentError } from "@/lib/documents/rag";
import { currentPayload, DocumentAccessError, getOwnedDocument } from "@/lib/documents/store";
import type { DocumentSection, GeneratedDocumentPayload } from "@/lib/documents/types";

export const dynamic = "force-dynamic";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id } = await context.params;
    const document = await getOwnedDocument(user.id, id);
    const current = currentPayload(document);
    const body = await request.json();
    const instruction = String(body.instruction || "").trim();
    if (!instruction) {
      return NextResponse.json({ error: "An instruction is required." }, { status: 400 });
    }
    const sections = (Array.isArray(body.sections) ? body.sections : current.payload.sections) as DocumentSection[];
    const targetSectionIds = Array.isArray(body.targetSectionIds)
      ? body.targetSectionIds.map(String)
      : Array.isArray(body.target_section_ids)
        ? body.target_section_ids.map(String)
        : undefined;

    const revised = await reviseDocument({
      template_id: document.templateId,
      values: current.values,
      sections,
      instruction,
      target_section_ids: targetSectionIds,
      use_model: body.use_model !== false,
    });

    const proposal = revised.document as GeneratedDocumentPayload | undefined;
    if (!proposal?.sections?.length) {
      return NextResponse.json({ error: "Revise did not return a proposal.", detail: revised }, { status: 422 });
    }

    return NextResponse.json({
      proposalOnly: true,
      document: {
        ...current.payload,
        ...proposal,
        signatures: proposal.signatures?.length ? proposal.signatures : current.payload.signatures,
        disclaimer: proposal.disclaimer || current.payload.disclaimer,
      },
      notes: revised.notes,
      warnings: revised.warnings,
      validation: revised.validation,
      retrieval: revised.retrieval,
      generation: revised.generation,
    });
  } catch (error) {
    if (error instanceof AuthRequiredError) return NextResponse.json({ error: error.message }, { status: 401 });
    if (error instanceof DocumentAccessError || error instanceof RagDocumentError) {
      return NextResponse.json({ error: error.message, detail: "payload" in error ? error.payload : undefined }, { status: error.status });
    }
    return NextResponse.json({ error: "Request failed" }, { status: 500 });
  }
}
