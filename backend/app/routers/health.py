"""Health and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ..telemetry.metrics import latest_metrics

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(latest_metrics(), media_type="text/plain; version=0.0.4")
