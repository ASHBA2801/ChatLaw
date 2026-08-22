import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from api.models import RetrievalTimings, SearchRequest, SearchResponse, SearchResult
from api.service import RagService, create_service

router = APIRouter(prefix="/api", tags=["search"])
logger = logging.getLogger(__name__)


def get_service() -> RagService:
    return create_service()


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, service: RagService = Depends(get_service)) -> SearchResponse:
    started = time.perf_counter()
    try:
        result = service.search(request.query, request.top_k, request.min_similarity)
        return SearchResponse(
            query=request.query,
            results=[SearchResult.model_validate(item, from_attributes=True) for item in result.results],
            no_relevant_context=result.no_relevant_context,
            retrieval=RetrievalTimings(top_k=request.top_k, results_returned=len(result.results),
                                       embedding_latency_seconds=result.embedding_latency_seconds,
                                       database_latency_seconds=result.database_latency_seconds),
        )
    except (ValueError, RuntimeError) as exc:
        logger.exception("[SEARCH] dependency or configuration failure")
        raise HTTPException(status_code=503, detail="Search service is unavailable") from exc
    except Exception as exc:
        logger.exception("[SEARCH] request failed")
        raise HTTPException(status_code=500, detail="Search request failed") from exc
    finally:
        service.close()
        logger.info("[SEARCH] Complete (%.2fs)", time.perf_counter() - started)