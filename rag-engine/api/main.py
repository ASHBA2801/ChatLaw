"""ChatLaw RAG Engine HTTP API."""

import logging
import os
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import chat, search, conversations, documents, extract, summarize

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

MAX_REQUEST_BYTES = int(os.getenv("RAG_MAX_REQUEST_BYTES", "262144"))
EXTRACT_MAX_BYTES = int(os.getenv("RAG_EXTRACT_MAX_BYTES", str(16 * 1024 * 1024)))
RATE_LIMIT_REQUESTS = int(os.getenv("RAG_RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RAG_RATE_LIMIT_WINDOW_SECONDS", "60"))
_rate_limit: dict[str, deque[float]] = defaultdict(deque)


def _configured_secret() -> str:
    return os.getenv("RAG_API_SECRET", "").strip()


def _authorized(request: Request) -> bool:
    expected = _configured_secret()
    supplied = request.headers.get("authorization", "")
    return bool(expected) and supplied.startswith("Bearer ") and secrets.compare_digest(
        supplied[7:].strip(), expected
    )


def _client_key(request: Request) -> str:
    return request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()


@asynccontextmanager
async def lifespan(_: FastAPI):
    from retrieval.vector_search import close_pool
    yield
    close_pool()

app = FastAPI(
    title="ChatLaw RAG Engine API",
    description="Grounded legal information retrieval and generation API.",
    version="0.1.0",
    lifespan=lifespan,
)
origins = [origin.strip() for origin in os.getenv(
    "CHATLAW_FRONTEND_ORIGIN",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=False, allow_methods=["GET", "POST", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"])


@app.middleware("http")
async def production_guards(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        if not _authorized(request):
            return JSONResponse(status_code=401, content={"detail": "Authentication required"})
        content_length = request.headers.get("content-length")
        max_bytes = EXTRACT_MAX_BYTES if request.url.path == "/api/extract/pdf" else MAX_REQUEST_BYTES
        if content_length and (not content_length.isdigit() or int(content_length) > max_bytes):
            return JSONResponse(status_code=413, content={"detail": "Request payload is too large"})
        if request.url.path in {
            "/api/chat",
            "/api/search",
            "/api/documents/generate",
            "/api/documents/regenerate",
            "/api/documents/revise",
            "/api/documents/selection-edit",
        } or request.url.path.endswith("/messages"):
            now = time.monotonic()
            bucket = _rate_limit[_client_key(request)]
            while bucket and bucket[0] <= now - RATE_LIMIT_WINDOW_SECONDS:
                bucket.popleft()
            if len(bucket) >= RATE_LIMIT_REQUESTS:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"},
                                    headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)})
            bucket.append(now)
    return await call_next(request)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(documents.router)
app.include_router(extract.router)
app.include_router(summarize.router)


@app.get("/", tags=["health"])
def root() -> dict[str, object]:
    """Friendly landing for browsers and probes hitting the service root."""
    return {
        "service": "chatlaw-rag-engine",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "chatlaw-rag-engine"}


@app.get("/ready", tags=["health"])
def ready() -> dict[str, str]:
    from retrieval.vector_search import check_readiness
    if not check_readiness():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="RAG service dependencies are unavailable")
    return {"status": "ready", "service": "chatlaw-rag-engine"}