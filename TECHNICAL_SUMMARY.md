# SYMPTOM SENSE - Agentic Medical AI Assistant**

## Technical Resume Summary

### 🎯 PROJECT OVERVIEW

Multimodal AI-powered medical diagnostic assistant built with LangGraph-orchestrated agent architecture for analyzing X-ray images and medical text queries with real-time confidence scoring, web search augmentation, and human-in-the-loop review flagging.

---

### 🏗️ ARCHITECTURE & TECH STACK

**Backend (Python)**

- **FastAPI REST API** with async endpoints + CORS support
- **LangGraph** state machine orchestrating 5+ specialized agent nodes
- **Qdrant** vector database (disk/memory/remote modes) for RAG retrieval
- **Gemini API** (primary LLM + embeddings) with **OpenRouter** fallback
- **PyTorch** + **Transformers** for local **ViT** image classification
- **Docling** for PDF→Markdown parsing with chunking
- **Brave Search API** for real-time web medical information
- **faster-whisper** (STT) + **Piper-TTS** (voice synthesis)

**Frontend (Angular 19)**

- Standalone component architecture with TypeScript
- Multi-provider chat interface (Mistral/Gemini/Custom Agentic)
- Image upload with base64 conversion + preview
- Real-time voice input via Web Speech API
- Markdown-formatted medical responses with citations

---

### 🤖 AGENT SYSTEM COMPONENTS

**1. Classification Agent**

- Routes queries to specialized agents based on input type (text/image/multimodal)
- Keyword detection for temporal queries → triggers web search

**2. Vision Agent (ViT)**

- Fine-tuned vit-xray-pneumonia model for chest X-ray classification
- Returns prediction label + confidence score (0-1 scale)
- CUDA/CPU device abstraction

**3. RAG Agent (Document Retrieval)**

- Chunks PDFs into 1500-char semantic windows with 200-char overlap
- Gemini embeddings (768D) with local sentence-transformer fallback
- Cross-encoder reranking (ms-marco-MiniLM-L-6-v2)
- Query expansion for medical terminology

**4. Web Search Agent**

- Brave Search integration for current medical guidelines
- Auto-enhancement with authoritative sources (NIH/CDC/WHO/PubMed)
- Relevance filtering + deduplication with RAG sources
- Triggered on: low RAG confidence (<0.5), temporal keywords, or zero results

**5. Synthesis Agent (LLM)**

- Multi-source context combination (RAG + Web + Vision)
- Pydantic schema validation for structured outputs
- Logprob extraction for LLM confidence scoring
- Citation tracking with inline references

**6. Confidence Verification Agent**

- Unified confidence scoring aggregating:
  - Image confidence (ViT softmax)
  - RAG confidence (retrieval scores + consensus)
  - LLM confidence (logprob→probability conversion)
- Categorization: HIGH (≥85%), MEDIUM (≥70%), LOW (<70%)
- Weighted fusion: 50% image, 25% RAG, 25% LLM (multimodal) OR 60% RAG, 40% LLM (text-only)

---

### 🔧 ADVANCED SERVICES

**Agent Orchestrator (`agent_combine.py`)**

- Dynamic agent priority weighting based on confidence profiles
- Contradiction detection between vision/text sources
- Parallel vs sequential execution routing
- Synthesis prompt generation with source attribution

**Natural Language Generation (`nlg_service.py`)**

- Tone adaptation: clinical/conversational/professional
- Confidence-aware phrasing (high/medium/low templates)
- Smart disclaimers (context-aware, not blanket AI warnings)
- Citation formatting with relevance scores

**Human-in-the-Loop (`hitl_service.py`)**

- JSON-based review queue (`hitl_queue`)
- Auto-flagging on: overall confidence <70% OR contradictory signals (image vs RAG diff >40%)
- Status tracking: pending → in_review → resolved
- Queue statistics dashboard

**Confidence Service (`confidence_service.py`)**

- Multi-modal confidence aggregation with weighted fusion
- Logprob normalization (-5 to 0 → 0.4 to 0.95 scale)
- RAG consensus boosting (3+ high scores → 10% confidence boost)
- Trigger rules for web fallback and HITL

---

### 📊 DATA PIPELINE
**Ingestion (`ingest_data.py`)**

```
PDF → Docling Parser → Markdown → Chunker → Gemini Embeddings → Qdrant
```

- Batch processing with metadata (source_file, chunk_index)
- Auto-detection of embedding dimensions for collection creation
- Graceful fallback from memory→disk mode for persistence

**Retrieval Flow**

```
Query → Embedding → Qdrant Search (top 10) → Cross-Encoder Rerank → Top 5
```
---

### 🎨 FRONTEND FEATURES

**Angular Chat Interface**

- 4 AI provider options: Mistral (multimodal), Gemini, OpenRouter, Agentic Local
- Image upload with validation (5MB max, jpg/png/webp)
- Base64 encoding for multimodal requests
- Voice-to-text input with MediaRecorder API
- Session management with auto-timeout
- Error handling with auto-dismiss toasts

**Response Formatting**

- Deduplicated confidence sections
- Structured output: Main Answer → Image Analysis → Confidence Metrics → HITL Flag → Warnings → Web Sources → RAG Citations → Follow-up Questions
- Medical disclaimer footer
- Markdown rendering with citation links

---

### 🔒 CONFIGURATION & DEPLOYMENT
**Environment Variables (`.env`)**

```
GEMINI_API_KEY, BRAVE_API_KEY
QDRANT_MODE=disk|memory|remote
VIT_MODEL=backend/app/models/vit-xray-pneumonia
TORCH_DEVICE=cpu|cuda
HITL_ENABLED=true, HITL_CONFIDENCE_THRESHOLD=0.70
BRAVE_SEARCH_ENABLED=true
USE_LOCAL_EMBEDDINGS=true (384D sentence-transformers)
```

**Docker Support**

- Multi-stage builds (CPU/CUDA variants)
- `docker-compose.yml` with Qdrant service
- ngrok tunnel for public demos

**Testing & QA**

- Pytest for backend services
- Mock providers for offline testing
- Ruff + Black linting, mypy type checking
- GitHub Actions CI pipeline

---

### 🚀 KEY INNOVATIONS

1. **Multi-Agent Confidence Fusion** - First system to aggregate vision, RAG, and LLM confidences into unified clinical risk scoring
2. **Intelligent Web Fallback** - Automated Brave Search invocation on low RAG confidence or temporal queries
3. **Context-Aware NLG** - Dynamic tone/disclaimer adjustment based on confidence levels (no generic "I'm just an AI" disclaimers)
4. **HITL Triage System** - Automatic human expert flagging with JSON queue management
5. **Zero-Dependency Frontend** - Angular standalone components with direct FastAPI integration

---

### 📈 PRODUCTION METRICS

- **Latency**: ~2-4s end-to-end (image + text query)
- **Confidence Coverage**: 100% (all responses scored)
- **RAG Precision**: Top-5 retrieval with reranking
- **Embedding Fallback**: Gemini→Local sentence-transformers (384D)
- **CORS**: Wildcard for hackathon, configurable for production

---

### 🎓 TECHNOLOGIES MASTERED

- **ML/AI**: LangGraph agents, PyTorch vision models, cross-encoder reranking, embedding similarity search
- **Backend**: FastAPI async, Pydantic validation, structlog JSON logging, Tenacity retry logic
- **Frontend**: Angular 19 signals, RxJS observables, TypeScript strict mode, HttpClient
- **DevOps**: Docker multi-stage, Qdrant vector DB, ngrok tunneling, GitHub Actions CI
- **APIs**: Google Gemini (LLM+embeddings), Brave Search, OpenRouter fallback

---
