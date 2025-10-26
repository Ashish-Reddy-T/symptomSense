# Backend

FastAPI application orchestrating multimodal agents with LangGraph.

## Application Layout
- `app/main.py` – FastAPI wiring, lifespan bootstrapping, telemetry.
- `app/core` – configuration, logging, error handling.
- `app/services` – Docling/Unstructured ingestion, Gemini embeddings, Qdrant, ViT, faster-whisper, Piper.
- `app/agents` – LangGraph state machine and node implementations.
- `app/routers` – REST endpoints for `/api/process_input`, `/api/stt`, `/api/tts`, `/health`, `/metrics`.
- `scripts/` – ingestion, warm-start, metrics export helpers.
- `tests/` – pytest suite covering routes, agents, and service helpers.

## Running Locally
```bash
pip install uv
uv pip install -e .[dev] --system
uvicorn app.main:app --reload --port 8000
```

## Quality Gates
- `ruff check backend`
- `mypy backend`
- `pytest backend`

## Environment Variables
See project root `.env.example` for the complete list. Key values:
- `GEMINI_API_KEY` (required)
- `QDRANT_MODE` (`memory` for hackathon portability)
- `PIPER_MODEL_PATH` path to the `.onnx` voice file used by Piper CLI
- `TORCH_DEVICE` to toggle CPU vs CUDA

## Worker Notes
- Warm models via `python scripts/warm_start.py` before demos to avoid cold starts.
- Piper CLI must be installed inside the runtime image; ensure voice files exist at `PIPER_MODEL_PATH`.
