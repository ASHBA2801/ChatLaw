# Embeddings (RAG-03)

RAG-03 contains a provider abstraction and an isolated Gemini adapter for the
first manually supervised embedding ingestion. The adapter is configured only
through environment variables; it does not invent a model name.

Required variables:

```text
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=<exact Gemini embedding model>
GEMINI_EMBEDDING_MODEL=<same exact model>
GEMINI_API_KEY=<secret>
EMBEDDING_DIMENSION=768
EMBEDDING_BATCH_SIZE=32
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/chatlaw
```

The adapter uses the Google SDK's default Gemini API endpoint; no API base URL
variable is currently supported. The configured model must return exactly 768
finite numeric values because the existing database column is `vector(768)`.
The ingestion orchestrator retries failed batches three times after the first
attempt, using 1/2/4 second exponential backoff. It does not expose retry
configuration through the environment yet.

Run `python scripts/validate_embedding_config.py` to validate configuration
without importing the provider SDK, making an API request, or connecting to
PostgreSQL. Use `python scripts/embed_chunks.py --input data/chunks --execute`
only when the configuration has been reviewed and real ingestion is intended.