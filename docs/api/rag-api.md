# RAG API Contract

This document specifies the intended HTTP contract between the Next.js
application (`web/`) and the RAG Engine (`rag-engine/`).

> **STATUS: CONTRACT ONLY — NOT IMPLEMENTED.**
>
> The RAG Engine is manually developed and not yet implemented. This document
> describes the *conceptual* contract. It must not be treated as a live API.
> No real endpoint exists yet, and no fake response is shipped in the codebase.

## Base URL (conceptual)

```
https://<rag-engine-host>/api/v1
```

## `POST /query`

Sends a user query to the RAG Engine and receives a grounded legal answer.

### Request

```json
{
  "query": "What is the punishment for theft under the BNS?",
  "language": "en",
  "conversation_id": "cm000000000000000000000000"
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `query` | string | yes | The user's legal question. |
| `language` | string | no | Language code (e.g. `en`, `hi`). Default `en`. |
| `conversation_id` | string | no | Conversation id for multi-turn context. |

### Response (conceptual)

```json
{
  "answer": "Under the Bharatiya Nyaya Sanhita ...",
  "grounded": true,
  "confidence": "high",
  "citations": [
    {
      "document": "Bharatiya Nyaya Sanhita, 2023",
      "section": "303",
      "chapter": "XVII",
      "excerpt": "..."
    }
  ],
  "sources": [
    {
      "name": "Bharatiya Nyaya Sanhita, 2023",
      "authority": "Parliament of India",
      "url": "https://..."
    }
  ]
}
```

| Field | Type | Description |
| --- | --- | --- |
| `answer` | string | The generated, grounded answer. |
| `grounded` | boolean | Whether the answer is supported by retrieved evidence. |
| `confidence` | string | `high` / `medium` / `low`. |
| `citations` | array | Precise legal citations (document, section, chapter). |
| `sources` | array | Provenance of the cited sources. |

## Other endpoints (conceptual)

Additional endpoints may be added later (e.g. health check, conversation
context). The contract is documented here and may evolve.

## Boundary rules

- The RAG Engine is the **only** component that talks to the retrieval
  pipeline and Gemini generation.
- `web/` never implements RAG; it only calls these endpoints.
- Responses must be clearly grounded; ungrounded answers should set
  `grounded: false`.
