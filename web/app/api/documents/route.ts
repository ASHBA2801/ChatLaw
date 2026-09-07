import { NextResponse } from "next/server";

import { AuthRequiredError, requireSessionUser } from "@/lib/auth/session";
import { generateDraft, RagDocumentError } from "@/lib/documents/rag";
import { createOwnedDocument, DocumentAccessError, listOwnedDocuments } from "@/lib/documents/store";
import { getTemplate } from "@/lib/documents/templates";
import { validateValues } from "@/lib/documents/validation";
import type { DocumentValues, GeneratedDocumentPayload } from "@/lib/documents/types";

export const dynamic = "force-dynamic";

function fail(error: unknown) {
  if (error instanceof AuthRequiredError) {
    return NextResponse.json({ error: error.message }, { status: 401 });
  }
  if (error instanceof DocumentAccessError || error instanceof RagDocumentError) {
    return NextResponse.json({ error: error.message, detail: "payload" in error ? error.payload : undefined }, { status: error.status });
  }
  return NextResponse.json({ error: "Request failed" }, { status: 500 });
}

export async function GET() {
  try {
    const user = await requireSessionUser();
    const documents = await listOwnedDocuments(user.id);
    return NextResponse.json({ documents });
  } catch (error) {
    return fail(error);
  }
}

export async function POST(request: Request) {
  try {
    const user = await requireSessionUser();
    const body = await request.json();
    const templateId = String(body.templateId || body.template_id || "");
    const values = (body.values || {}) as DocumentValues;
    const template = getTemplate(templateId);
    const validation = validateValues(template, values);
    if (!validation.canGenerate) {
      return NextResponse.json({ error: "Required information is missing.", validation }, { status: 422 });
    }
    const generated = await generateDraft({
      template_id: templateId,
      values,
      use_model: body.use_model !== false,
      language: typeof values.draft_language === "string" ? values.draft_language : "en",
    });
    const payload = generated.document as GeneratedDocumentPayload;
    if (!payload) {
      return NextResponse.json({ error: "Generation did not return a document.", detail: generated }, { status: 422 });
    }
    const created = await createOwnedDocument({
      userId: user.id,
      title: payload.title,
      templateId,
      documentType: template.documentType,
      jurisdictionCountry: String(values.jurisdiction_country || "IN"),
      jurisdictionRegion: String(values.jurisdiction_region || "") || null,
      conversationId: typeof body.conversationId === "string" ? body.conversationId : null,
      values,
      payload,
      generation: {
        retrieval: generated.retrieval,
        generation: generated.generation,
        validation: generated.validation,
        evidence: generated.evidence,
      },
    });
    return NextResponse.json({
      id: created.document.id,
      versionNumber: created.version.versionNumber,
      status: created.document.status,
      validation: generated.validation,
      document: payload,
    }, { status: 201 });
  } catch (error) {
    if (error instanceof Error && error.message.startsWith("Unknown document template")) {
      return NextResponse.json({ error: "Unknown document template" }, { status: 404 });
    }
    return fail(error);
  }
}
