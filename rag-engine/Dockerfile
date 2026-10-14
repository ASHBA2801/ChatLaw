FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/rag-engine

WORKDIR /app/rag-engine

COPY rag-engine/requirements.prod.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY rag-engine/api ./api
COPY rag-engine/embeddings ./embeddings
COPY rag-engine/generation ./generation
COPY rag-engine/retrieval ./retrieval
COPY rag-engine/context ./context
COPY rag-engine/verification ./verification
COPY rag-engine/conversation ./conversation
COPY rag-engine/documents ./documents
COPY rag-engine/extraction ./extraction
COPY rag-engine/cases ./cases
COPY rag-engine/research ./research
COPY rag-engine/complaints ./complaints
COPY rag-engine/scenario ./scenario
COPY rag-engine/acts ./acts
COPY rag-engine/database ./database
COPY rag-engine/config ./config
COPY rag-engine/ingestion ./ingestion
COPY legal_corpus /app/legal_corpus
COPY legal-data/metadata/eighth-schedule-languages.json /app/legal-data/metadata/eighth-schedule-languages.json
COPY web/data/legal/official-judgments.json /app/web/data/legal/official-judgments.json

RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
