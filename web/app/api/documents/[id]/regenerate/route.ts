import { NextResponse } from "next/server";

import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import { regenerateSection, RagDocumentError } from "@/lib/documents/rag";
import { currentPayload, DocumentAccessError, getOwnedDocument } from "@/lib/documents/store";
import { replaceSection } from "@/lib/documents/editor";
import type { DocumentSection } from "@/lib/documents/types";

export const dynamic = "force-dynamic";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const user = await requireSessionUser();
    const { id } = await context.params;
    const document = await getOwnedDocument(user.id, id);
    const current = currentPayload(document);
    const body = await request.json();
    const sectionId = String(body.sectionId || body.section_id || "");
    if (!sectionId) {
      return NextResponse.json({ error: "Select a section to regenerate." }, { status: 400 });
    }
    const generated = await regenerateSection({
      template_id: document.templateId,
      values: current.values,
      section_id: sectionId,
      use_model: body.use_model !== false,
    });
    const nextSection = (generated.document?.sections as DocumentSection[] | undefined)?.[0];
    if (!nextSection) {
      return NextResponse.json({ error: "Section regeneration did not return a clause.", detail: generated }, { status: 422 });
    }
    const merged = replaceSection(current.payload, nextSection);
    if (Array.isArray(generated.citations) && generated.citations.length) {
      const existing = new Map(merged.citations.map((item) => [String((item as { id?: number }).id), item]));
      for (const citation of generated.citations) {
        existing.set(String((citation as { id?: number }).id), citation);
      }
      merged.citations = [...existing.values()];
    }
    return NextResponse.json({
      section: nextSection,
      document: merged,
      validation: generated.validation,
      retrieval: generated.retrieval,
      generation: generated.generation,
    });
  } catch (error) {
    if (error instanceof AuthRequiredError) return NextResponse.json({ error: error.message }, { status: 401 });
    if (error instanceof DocumentAccessError || error instanceof RagDocumentError) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }
    return NextResponse.json({ error: "Request failed" }, { status: 500 });
  }
}
