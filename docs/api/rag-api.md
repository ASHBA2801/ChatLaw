# RAG API Contract

This document specifies the implemented HTTP contract between the Next.js
application (`web/`) and the RAG Engine (`rag-engine/`).

Browser clients should use the Next.js `/api/rag/*` proxy; direct RAG service
access requires authentication.

## Endpoints

- `GET /health` — unauthenticated liveness check.
- `GET /ready` — unauthenticated dependency readiness check.
- `POST /api/search` — authenticated retrieval (no Gemini generation).
- `POST /api/extract/pdf` — authenticated deterministic PDF text extraction (no Gemini).
- `POST /api/summarize/document` — authenticated, user-triggered document summary.
- `POST /api/chat` — authenticated grounded chat (may first return a clarification).
- `POST /api/conversations` — authenticated conversation creation. Optional `case_id`.
- `GET /api/conversations` — authenticated conversation listing.
- `GET /api/conversations/{conversation_id}` — authenticated conversation read.
- `POST /api/conversations/{conversation_id}/messages` — authenticated chat and persistence. Optional authorized `case_context` excerpts.
- `POST /api/documents/generate` — authenticated structured document draft.
- `POST /api/documents/regenerate` — authenticated targeted clause regeneration.
- `GET /api/documents/templates` — authenticated list of implemented templates.

All `/api/*` requests require `Authorization: Bearer <RAG_API_SECRET>`.

## `POST /api/chat` and conversation messages

### Request

```json
{
  "message": "My landlord is refusing to return my deposit.",
  "language": "ta",
  "top_k": 8,
  "min_similarity": 0.6
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | string | yes | User question, trimmed and limited to 12,000 characters. |
| `language` | string | no | ISO language code (`en` or Eighth Schedule codes). Default `en`. |
| `top_k` | integer | no | 1–20; default 8. |
| `min_similarity` | number | no | 0–1; default 0.6. |

### Response

Clarification turns (local interview, **no Gemini**) return:

```json
{
  "answer": "Which state are you in?",
  "response_kind": "clarification",
  "language": "en",
  "has_context": false,
  "no_relevant_context": false,
  "citations": [],
  "interview": {
    "domain": "tenancy",
    "round": 1,
    "max_rounds": 3,
    "slots": {},
    "asked": ["state"],
    "assumptions": [],
    "original_query": "My landlord is refusing to return my deposit."
  }
}
```

Grounded answers use **one** generation call in the selected language and return:

| Field | Type | Description |
| --- | --- | --- |
| `answer` | string | Localized plain-language answer (markdown sections). |
| `response_kind` | string | `clarification` \| `answer` \| `no_context`. |
| `language` | string | Language used for the turn. |
| `has_context` | boolean | Whether retrieval found usable evidence. |
| `no_relevant_context` | boolean | True when generation was skipped for lack of sources. |
| `citations` | array | Validated citations with evidence excerpts. |
| `interview` | object \| null | Slot-filling state when an interview ran. |

When no relevant context is found, generation is skipped and citations are empty.

## Boundary rules

- The RAG Engine is the **only** component that talks to the retrieval pipeline and Gemini generation.
- `web/` never implements RAG; it only calls these endpoints.
- Clarification questions are produced locally and must not call Gemini.
- Localization happens in the same grounded generation request — never English-then-translate.
- Case context must be loaded server-side; browsers must not supply trusted `case_context`.
