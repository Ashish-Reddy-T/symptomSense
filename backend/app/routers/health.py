"""Health and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from starlette.requests import Request
from fastapi.responses import PlainTextResponse

from ..telemetry.metrics import latest_metrics
from ..storage.qdrant_client import get_collection_count
from ..core.settings import Settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/qdrant")
async def qdrant_health() -> dict[str, object]:
    """Return a small diagnostic about the Qdrant collection used by the app.

    This function intentionally imports the running FastAPI `app` lazily to
    avoid circular imports during router registration.
    """
    try:
        main_mod = __import__("backend.app.main", fromlist=["app"])
        app = getattr(main_mod, "app", None)
    except Exception:
        app = None

    if app is None:
        return {"available": False, "message": "app not available"}

    settings: Settings = getattr(app.state, "settings", None)
    client = getattr(app.state, "qdrant", None)
    if client is None or settings is None:
        return {"available": False, "message": "qdrant client not initialised"}
    count = get_collection_count(client, settings.QDRANT_COLLECTION)
    return {"available": True, "collection": settings.QDRANT_COLLECTION, "count": count}


@router.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(latest_metrics(), media_type="text/plain; version=0.0.4")
