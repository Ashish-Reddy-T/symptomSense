# Agentic Medical Assistant

Agentic, multimodal RAG stack built for the PSU hackathon. A FastAPI backend orchestrated by LangGraph combines document retrieval (Docling + Qdrant + Gemini embeddings), ViT image analysis, faster-whisper speech-to-text, and Piper TTS. Gemini 2.5 Flash powers the primary reasoning loop with optional OpenRouter failover. A lightweight vanilla JS frontend drives the demo.

## Highlights
- **Agentic LangGraph flow**: input classification, document RAG, image analysis, final synthesis, and confidence verification.
- **Multimodal I/O**: PDF ingestion via Docling, ViT-based imaging, faster-whisper STT, Piper TTS playback with local voice packs.
- **Retrieval infra**: Gemini text-embedding-005 vectors stored in Qdrant with cross-encoder reranking.
- **Production tooling**: Docker/Docker Compose, Prometheus metrics, structured logging, CI with Ruff + mypy + pytest.

## Quickstart
1. Copy environment defaults and fill secrets:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies (uv recommended):
   ```bash
   cd backend
   pip install uv
   uv pip install -e .[dev] --system
   ```
3. (Optional) ingest PDFs into Qdrant:
   ```bash
   python ../scripts/ingest_data.py
   ```
4. Run the API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. Open `frontend/public/index.html` in a browser (or serve via any static file server).

## Docker
- Local stack with Qdrant:
  ```bash
  cd infra
  docker compose up --build
  ```
- Standalone image:
  ```bash
  docker build -f docker/Dockerfile -t agentic-med-assistant .
  docker run --env-file .env -p 8000:8000 agentic-med-assistant
  ```

## Makefile Targets
`make dev`, `make ingest`, `make warm`, `make fmt`, `make lint`, `make type`, `make test`, `make build`.

## Testing
```bash
cd backend
pytest -q
```

Ensure required models (torch, transformers, docling, faster-whisper, piper) are installed; see `pyproject.toml` for the full dependency list.

## Frontend Features
- Text + image submission with MediaRecorder-based audio capture.
- Live STT transcription populates the query box.
- TTS playback via Piper, inline citations, follow-up actions, and confidence banners rendered in the UI.

## Architecture
See `AGENTS.md` and `tree.md` for the complete blueprint plus Mermaid diagram.
