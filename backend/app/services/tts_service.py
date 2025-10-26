"""Text-to-speech service leveraging Piper."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..core.settings import Settings

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 22050


class PiperService:
    """Wrapper around the Piper CLI."""

    def __init__(self, settings: Settings, *, binary: str | None = None) -> None:
        self.settings = settings
        self.binary = binary or shutil.which("piper")
        if not self.binary:
            raise RuntimeError("Piper binary not found on PATH. Install `piper-tts` CLI.")
        self.model_path = self._resolve_model_path(settings)

    def _resolve_model_path(self, settings: Settings) -> Path:
        if settings.PIPER_MODEL_PATH:
            path = Path(settings.PIPER_MODEL_PATH)
        else:
            path = Path(settings.PIPER_VOICE)
        if not path.exists():
            message = (
                f"Piper model not found at {path}. "
                "Set `PIPER_MODEL_PATH` to the .onnx voice file."
            )
            raise FileNotFoundError(message)
        return path

    def synthesize(self, text: str, *, sample_rate: int = DEFAULT_SAMPLE_RATE) -> dict:
        if not text.strip():
            raise ValueError("Text-to-speech requires non-empty text.")
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            cmd = [
                self.binary,
                "--model",
                str(self.model_path),
                "--output_file",
                tmp.name,
            ]
            logger.info("piper_synthesize_start", model=str(self.model_path))
            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            audio = Path(tmp.name).read_bytes()
        logger.info("piper_synthesize_done", bytes=len(audio))
        return {"audio": audio, "sample_rate": sample_rate, "format": "wav"}

    def close(self) -> None:
        """No persistent resources to clean up."""
