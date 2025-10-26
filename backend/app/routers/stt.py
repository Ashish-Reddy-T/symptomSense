"""Speech-to-text endpoint."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from ..models.dto import STTResponse
from ..telemetry.metrics import RequestTracker

router = APIRouter()


@router.post("/stt", response_model=STTResponse)
async def stt_endpoint(
    request: Request,
    audio: UploadFile = File(...),  # noqa: B008 - FastAPI pattern requires callable default
    language: str | None = Form(default=None),
) -> STTResponse:
    tracker = RequestTracker("stt")
    service = getattr(request.app.state, "stt_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="STT service unavailable.")

    audio_bytes = await audio.read()
    try:
        result = service.transcribe_bytes(audio_bytes, language=language)
        tracker.observe_success()
    except Exception:
        tracker.observe_error()
        raise
    return STTResponse(**result)
