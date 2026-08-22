# Generation

Intended to hold Gemini-backed legal response generation.

`prompt.py` contains the strict grounding instructions and `gemini.py` uses
the configurable `GEMINI_GENERATION_MODEL` through the existing `google-genai`
SDK. `answer.py` prevents generation when retrieval returns no context and
renders citations only from retrieval metadata.