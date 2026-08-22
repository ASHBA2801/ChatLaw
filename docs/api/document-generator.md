# Document generation API

ChatLaw generates structured legal drafts from templates. Browser clients call
the Next.js `/api/documents` routes. Those routes authenticate the user with
Auth.js and, when generation is required, call the RAG engine with the
server-side service secret. Gemini keys are never sent to the browser.

## Implemented templates

- Non-Disclosure Agreement (`nda`)
- Service Agreement (`service_agreement`)
- Rent / Lease Agreement (`rent_lease`)
- Employment Agreement (`employment_agreement`)
- Partnership Agreement (`partnership_agreement`)
- Sale Agreement (`sale_agreement`)
- Memorandum of Understanding (`mou`)
- Affidavit (`affidavit`)
- Legal Notice (`legal_notice`)
- Authorization Letter (`authorization_letter`)
- Consumer Complaint (`consumer_complaint`)
- General Complaint / Police Complaint (`complaint`)

Unsupported document types are not listed in the builder. Chat drafting mode
refuses unsupported types instead of inventing a freeform template.

Clause specs carry a `provision_class` of `required`, `recommended`, or
`user_specific` (surfaced in the editor sidebar).

## Chat → document drafting

Conversation turns may enter document drafting mode when the user asks to draft
a supported document. Clarification asks only for missing **required** template
fields (including jurisdiction state/UT). No Gemini call is made during
clarification.

Response kinds:

- `document_clarification` — ask the next required field
- `document_ready` — payload includes `document_draft.template_id` and `values`
- `document_unsupported` — type not in the registry

The web chat client creates the draft with `POST /api/documents` (which calls
RAG `/generate`) and opens `/documents/{id}`. Optional `conversationId` is
stored on `UserDocument`.

## RAG engine

- `GET /api/documents/templates`
- `POST /api/documents/generate`
- `POST /api/documents/regenerate`
- `POST /api/documents/revise` — instruction-based section patches (proposal only)
- `POST /api/documents/selection-edit` — selected-text AI suggestion (proposal only)

Request fields for generate: `template_id`, `values`, optional `use_model`,
`top_k`, `min_similarity`. Regeneration also requires `section_id`.

Revise requires current `sections` plus `instruction`. Selection-edit requires
`selected_text`, `action`, and `surrounding_section`.

Missing required fields return `422` and do not generate. The generator does
not invent parties, dates, amounts, statutes, or case citations. Legal
citations are attached only from the existing retrieval/evidence pipeline.
Revise/selection-edit refuse silent emptying of required clauses and restore
citation markers on jurisdiction-sensitive sections when stripped.

## Next.js workspace

Authenticated routes:

- `GET/POST /api/documents`
- `GET/PATCH/DELETE /api/documents/{id}`
- `POST /api/documents/{id}/versions`
- `POST /api/documents/{id}/regenerate`
- `POST /api/documents/{id}/revise`
- `POST /api/documents/{id}/selection-edit`
- `POST /api/documents/{id}/restore`
- `GET /api/documents/{id}/export?format=pdf|docx`

Ownership is enforced from the server session. A document ID is not sufficient
without a matching `userId`.

The editor applies AI proposals only after Accept (selection or revise). Save
creates an append-only version. Export PDF/DOCX and Print are wired to real
output (print uses the document preview sheet).
