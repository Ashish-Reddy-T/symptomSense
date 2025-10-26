"""Application configuration powered by pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration shared across the app."""

    # API keys
    GEMINI_API_KEY: str
    OPENROUTER_API_KEY: str | None = None

    # Retrieval / storage
    QDRANT_MODE: Literal["memory", "disk", "remote"] = "memory"
    QDRANT_PATH: Path = Path("./data/qdrant_db")
    QDRANT_URL: str | None = None
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "medical-knowledge"

    # Parsing
    PARSER: Literal["docling", "unstructured"] = "docling"

    # Models
    VIT_MODEL: str = "backend/app/models/vit-xray-pneumonia"
    TORCH_DEVICE: Literal["cpu", "cuda"] = "cpu"
    WHISPER_MODEL: str = "small"
    PIPER_VOICE: str = "en_US-amy-medium"
    PIPER_MODEL_PATH: str | None = None
    GEMINI_MODEL: str = "models/gemini-2.5-flash"
    GEMINI_EMBED_MODEL: str = "models/text-embedding-005"
    # Many local sentence-transformers produce 384-d embeddings (all-MiniLM-L6-v2).
    # Set a sensible default so Qdrant collections created at startup match local
    # fallback embeddings when external embedding providers (Gemini) are
    # unavailable or rate-limited.
    GEMINI_EMBED_DIMENSION: int | None = 384
    # Prefer open-source/local embeddings instead of Gemini when True.
    USE_LOCAL_EMBEDDINGS: bool = True
    # Local embedding model name (sentence-transformers or HF model). You can
    # set this to 'BAAI/bge-large-en' or another HF model name; the code will
    # fall back to 'all-MiniLM-L6-v2' if the requested model can't be loaded.
    # Use a small, fast local model by default to avoid long downloads in dev.
    # Set to 'BAAI/bge-large-en' if you want to use that larger model.
    LOCAL_EMBED_MODEL: str = "all-MiniLM-L6-v2"
    OPENROUTER_MODEL: str = "openrouter/mistral-7b-instruct"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Agent thresholds
    MIN_IMAGE_CONFIDENCE: float = 0.8
    MIN_AVG_LOGPROB: float = -1.0

    # App meta
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    ENV: Literal["dev", "prod", "test"] = "dev"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    LOG_STRUCTURED: bool = True

    # CORS
    FRONTEND_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("QDRANT_PATH", mode="before")
    @classmethod
    def _coerce_path(cls, value: str | Path) -> Path:
        return Path(value)

    @field_validator("FRONTEND_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, value) -> list[str]:
        if isinstance(value, str):
            if value.strip() == "*":
                return ["*"]
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
