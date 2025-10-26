"""Speech-to-text service using faster-whisper."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Iterable

from faster_whisper import WhisperModel

from ..core.settings import Settings

logger = logging.getLogger(__name__)


def _compute_type(device: str) -> str:
    if device == "cuda":
        return "float16"
    return "int8_float32"


class WhisperService:
    def __init__(
        self,
        settings: Settings,
        *,
        model: WhisperModel | None = None,
    ) -> None:
        self.settings = settings
        self.model = model or WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.TORCH_DEVICE,
            compute_type=_compute_type(settings.TORCH_DEVICE),
        )

    def transcribe_bytes(self, audio_bytes: bytes, *, language: str | None = None) -> dict:
        with tempfile.NamedTemporaryFile(suffix=".webm") as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            return self.transcribe_file(tmp.name, language=language)

    def transcribe_file(self, path: str | Path, *, language: str | None = None) -> dict:
        logger.info("stt_transcribe_start", path=str(path))
        segments, info = self.model.transcribe(
            str(path),
            beam_size=5,
            language=language,
        )
        text_segments = [segment.text.strip() for segment in segments if segment.text]
        transcript = " ".join(text_segments).strip()
        result = {
            "text": transcript,
            "language": info.language,
            "duration": info.duration,
            "words": text_segments,
        }
        logger.info("stt_transcribe_done", language=result["language"])
        return result

    def close(self) -> None:
        del self.model
