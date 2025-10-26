"""Text-to-speech endpoint."""

from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException, Request

from ..models.dto import TTSRequest, TTSResponse
from ..services.tts_service import DEFAULT_SAMPLE_RATE
from ..telemetry.metrics import RequestTracker

router = APIRouter()


@router.post("/tts", response_model=TTSResponse)
async def tts_endpoint(req: TTSRequest, request: Request) -> TTSResponse:
    tracker = RequestTracker("tts")
    service = getattr(request.app.state, "tts_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="TTS service unavailable.")
    try:
        result = service.synthesize(req.text)
        tracker.observe_success()
    except Exception:
        tracker.observe_error()
        raise
    audio_b64 = base64.b64encode(result["audio"]).decode("utf-8")
    return TTSResponse(
        audio_base64=audio_b64,
        sample_rate=result.get("sample_rate", DEFAULT_SAMPLE_RATE),
        format=result.get("format", "wav"),
    )
