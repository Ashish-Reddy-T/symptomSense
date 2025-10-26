# 🚀 Deployment Guide - Agentic Medical Assistant

**Complete guide for local, Docker, and public deployment with ngrok**

---

## 📋 Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Ngrok Public Access](#ngrok-public-access)
4. [Production Checklist](#production-checklist)
5. [Troubleshooting](#troubleshooting)

---

## 🏠 Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js (optional, for alternative frontend serving)
- 4GB+ RAM (8GB recommended for VIT model)
- Git

### Step 1: Clone & Setup Environment

```bash
# Clone repository
git clone <your-repo-url>
cd agentic-med-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Create `.env` file in project root:

```bash
# API Keys (REQUIRED)
GEMINI_API_KEY=your_gemini_api_key_here
BRAVE_API_KEY=your_brave_api_key_here

# Optional API Keys
OPENROUTER_API_KEY=your_openrouter_key_here

# Vector Database (Qdrant)
QDRANT_MODE=disk                                    # memory | disk | remote
QDRANT_PATH=./data/qdrant_db                        # Only for disk mode
QDRANT_URL=                                         # Only for remote mode
QDRANT_API_KEY=                                     # Only for remote mode

# Document Parsing
PARSER=docling                                      # docling | unstructured

# Vision Model
VIT_MODEL=/absolute/path/to/backend/app/models/vit-xray-pneumonia
TORCH_DEVICE=cpu                                    # cpu | cuda

# Speech-to-Text / Text-to-Speech (Optional)
WHISPER_MODEL=small                                 # tiny | base | small | medium | large
PIPER_VOICE=en_US-amy-low
STT_ENABLED=false                                   # Enable STT
TTS_ENABLED=false                                   # Enable TTS

# Web Search
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_ENABLED=true

# Confidence & HITL
CONFIDENCE_THRESHOLD=0.70
HITL_QUEUE_PATH=./data/hitl_queue

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
ENV=dev                                             # dev | prod
LOG_LEVEL=INFO
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Step 3: Prepare Model Files

Ensure VIT model is downloaded:

```bash
# If not already present, download VIT model
mkdir -p backend/app/models/vit-xray-pneumonia
# Download model.safetensors, config.json, preprocessor_config.json to this directory
```

### Step 4: Initialize Vector Database (Optional)

If you have medical PDFs to ingest:

```bash
# Place PDFs in data/knowledge_base/
mkdir -p data/knowledge_base
cp your_medical_pdfs/*.pdf data/knowledge_base/

# Run ingestion script
python scripts/ingest_data.py
```

### Step 5: Start Backend

```bash
# From project root
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# OR run in background
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

# Check logs
tail -f /tmp/backend.log
```

### Step 6: Start Frontend

```bash
# From project root, in new terminal
cd frontend/public
python3 -m http.server 3000

# OR run in background
nohup python3 -m http.server 3000 > /tmp/frontend.log 2>&1 &
```

### Step 7: Verify System

Run comprehensive tests:

```bash
# From project root
chmod +x scripts/test_system.sh
./scripts/test_system.sh
```

Expected output:
```
✅ Backend is healthy
✅ Got response (4000+ chars)
✅ Image classified as: PNEUMONIA (0.62)
✅ Frontend is accessible
✅ ALL TESTS PASSED
```

### Access Points
- **Frontend UI**: http://localhost:3000/
- **Backend API**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics

---

## 🐳 Docker Deployment

### Step 1: Build Docker Images

```bash
# Build backend image
docker build -f docker/Dockerfile -t agentic-med-assistant:latest .

# OR use CPU-only version
docker build -f docker/Dockerfile.cpu -t agentic-med-assistant:cpu .
```

### Step 2: Configure Docker Compose

Ensure `infra/docker-compose.yml` is configured:

```yaml
version: "3.9"

services:
  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: agentic-backend
    env_file:
      - ../.env
    ports:
      - "8000:8000"
    volumes:
      - ../data:/app/data
      - ../backend/app/models:/app/models
    networks:
      - agentic-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: nginx:alpine
    container_name: agentic-frontend
    ports:
      - "3000:80"
    volumes:
      - ../frontend/public:/usr/share/nginx/html:ro
    networks:
      - agentic-net
    depends_on:
      - backend

  qdrant:
    image: qdrant/qdrant:latest
    container_name: agentic-qdrant
    ports:
      - "6333:6333"
    volumes:
      - ../data/qdrant_db:/qdrant/storage
    networks:
      - agentic-net

networks:
  agentic-net:
    driver: bridge
```

### Step 3: Run with Docker Compose

```bash
# Start all services
cd infra
docker-compose up --build -d

# Check logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

### Step 4: Verify Docker Deployment

```bash
# Check container status
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000/
```

---

## 🌐 Ngrok Public Access

For hackathon demos or external testing, expose your local deployment publicly.

### Step 1: Install Ngrok

```bash
# macOS
brew install ngrok

# Linux
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Or download from https://ngrok.com/download
```

### Step 2: Authenticate Ngrok

```bash
# Get authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken <your_auth_token>
```

### Step 3: Configure Ngrok Tunnel

Update `infra/ngrok.yml`:

```yaml
version: "2"
authtoken: <your_auth_token>

tunnels:
  backend:
    addr: 8000
    proto: http
    inspect: true
  
  frontend:
    addr: 3000
    proto: http
```

### Step 4: Start Ngrok Tunnels

```bash
# Start tunnels using config
ngrok start --all --config infra/ngrok.yml

# OR start single tunnel
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

### Step 5: Update Frontend API Base

Update `frontend/src/api.js` to use ngrok URL:

```javascript
// Change from:
const API_BASE = 'http://localhost:8000';

// To:
const API_BASE = 'https://abc123.ngrok.io';  // Your ngrok URL
```

### Step 6: Update Backend CORS

Update `.env` to allow ngrok origin:

```bash
FRONTEND_ORIGINS=http://localhost:3000,https://xyz789.ngrok.io
```

Restart backend for changes to take effect.

### Step 7: Share URLs

- **Frontend**: https://xyz789.ngrok.io (frontend tunnel)
- **Backend API**: https://abc123.ngrok.io (backend tunnel)
- **API Docs**: https://abc123.ngrok.io/docs

### Ngrok Pro Tips

1. **Custom Domains**: Upgrade to ngrok Pro for custom subdomains
2. **Authentication**: Add basic auth with `--auth "username:password"`
3. **HTTPS Only**: Ngrok provides free HTTPS automatically
4. **Inspect Traffic**: Visit http://127.0.0.1:4040 for ngrok inspector

---

## ✅ Production Checklist

### Before Demo/Deployment

- [ ] **Environment Variables Set**
  - [ ] `GEMINI_API_KEY` configured
  - [ ] `BRAVE_API_KEY` configured
  - [ ] `VIT_MODEL` points to correct absolute path
  - [ ] `QDRANT_MODE` set (disk recommended for persistence)

- [ ] **Model Files Present**
  - [ ] VIT model downloaded to `backend/app/models/vit-xray-pneumonia/`
  - [ ] Model contains: `model.safetensors`, `config.json`, `preprocessor_config.json`

- [ ] **Vector Database Initialized**
  - [ ] Qdrant storage directory exists: `data/qdrant_db/`
  - [ ] Medical documents ingested (if using RAG): `python scripts/ingest_data.py`

- [ ] **Services Running**
  - [ ] Backend: `curl http://localhost:8000/health` returns `{"status":"ok"}`
  - [ ] Frontend: `curl http://localhost:3000/` returns HTML
  - [ ] No port conflicts (8000, 3000, 6333 available)

- [ ] **System Tests Passed**
  - [ ] Run `./scripts/test_system.sh` - all tests green
  - [ ] Health check ✅
  - [ ] Text query ✅
  - [ ] Image classification ✅
  - [ ] Confidence system ✅
  - [ ] Frontend accessible ✅

- [ ] **Hackathon Demo Ready**
  - [ ] ngrok tunnels started (if public access needed)
  - [ ] Frontend API base updated to ngrok URL
  - [ ] CORS configured for ngrok origins
  - [ ] Test query prepared (e.g., "What is pneumonia?" + X-ray image)

### Resource Requirements

| Component | CPU | RAM | Disk | Notes |
|-----------|-----|-----|------|-------|
| Backend | 2+ cores | 2GB | 500MB | Base API |
| VIT Model | 1+ core | 2GB | 400MB | Image classification |
| Qdrant | 1 core | 512MB | 1GB+ | Vector database |
| Frontend | Minimal | 100MB | 10MB | Static files |
| **Total** | **4 cores** | **4-8GB** | **2GB+** | Recommended |

### Performance Optimization

```bash
# Enable GPU acceleration (if available)
TORCH_DEVICE=cuda

# Reduce VIT model size (faster, slightly less accurate)
# Use ViT-base instead of ViT-large

# Disable unused services
STT_ENABLED=false
TTS_ENABLED=false

# Use in-memory Qdrant for speed (loses persistence)
QDRANT_MODE=memory
```

---

## 🔧 Troubleshooting

### Backend Won't Start

**Issue**: `ModuleNotFoundError: No module named 'app'`
```bash
# Solution: Run from backend/ directory or set PYTHONPATH
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Issue**: `VIT model not found`
```bash
# Solution: Verify absolute path in .env
echo $VIT_MODEL  # Should show full path like /Users/.../vit-xray-pneumonia
ls -la /path/to/vit-xray-pneumonia/  # Should contain model.safetensors
```

**Issue**: `Port 8000 already in use`
```bash
# Solution: Kill existing process
lsof -ti:8000 | xargs kill -9
# Or use different port
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Frontend Issues

**Issue**: `404 Not Found` on http://localhost:3000/public/index.html
```bash
# Solution: Remove /public/ from URL
# Correct: http://localhost:3000/
# Wrong: http://localhost:3000/public/index.html
```

**Issue**: CORS errors in browser console
```bash
# Solution: Add frontend origin to .env
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# Restart backend
```

### API Errors

**Issue**: `401 Unauthorized` from Gemini API
```bash
# Solution: Check API key is valid
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models
```

**Issue**: `Brave API rate limit exceeded`
```bash
# Solution: Reduce WEB_SEARCH_MAX_RESULTS or wait
WEB_SEARCH_MAX_RESULTS=3  # Lower from 5
```

**Issue**: Low confidence / HITL always triggered
```bash
# Solution: Adjust threshold
CONFIDENCE_THRESHOLD=0.50  # Lower from 0.70 for more lenient filtering
```

### Docker Issues

**Issue**: Build fails with "no space left on device"
```bash
# Solution: Clean Docker cache
docker system prune -a
```

**Issue**: Container can't access .env file
```bash
# Solution: Ensure .env is in parent directory
ls ../.env  # Should exist
# Or mount explicitly in docker-compose.yml
```

**Issue**: Qdrant data not persisting
```bash
# Solution: Check volume mount
docker-compose exec backend ls /app/data/qdrant_db
# Should show collection/ and meta.json
```

### Ngrok Issues

**Issue**: "ERR_NGROK_108" connection refused
```bash
# Solution: Ensure backend is running first
curl http://localhost:8000/health  # Should return before starting ngrok
```

**Issue**: Frontend can't reach backend through ngrok
```bash
# Solution 1: Update frontend API_BASE to ngrok URL
# Solution 2: Add ngrok origin to FRONTEND_ORIGINS in .env
# Solution 3: Restart backend after CORS change
```

---

## 🎯 Quick Reference Commands

### Start/Stop Services

```bash
# Start backend (foreground)
cd backend && uvicorn app.main:app --reload

# Start backend (background)
nohup uvicorn backend.app.main:app > /tmp/backend.log 2>&1 &

# Start frontend
cd frontend/public && python3 -m http.server 3000 &

# Stop all
pkill -f uvicorn
pkill -f "http.server 3000"

# Check running services
lsof -ti:8000  # Backend
lsof -ti:3000  # Frontend
```

### Docker Commands

```bash
# Build and start
cd infra && docker-compose up --build -d

# View logs
docker-compose logs -f backend

# Restart single service
docker-compose restart backend

# Stop and remove
docker-compose down -v  # -v removes volumes
```

### Testing Commands

```bash
# Full system test
./scripts/test_system.sh

# Health check
curl http://localhost:8000/health

# Simple query
curl -X POST http://localhost:8000/api/process_input \
  -H "Content-Type: application/json" \
  -d '{"text_query": "What is pneumonia?"}'

# Check HITL queue
ls -la data/hitl_queue/
```

---

## 📞 Support & Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Prometheus Metrics**: http://localhost:8000/metrics
- **Ngrok Inspector**: http://127.0.0.1:4040 (when ngrok running)
- **Backend Logs**: `/tmp/backend.log`
- **HITL Queue**: `data/hitl_queue/`

---

## 🎓 Hackathon Demo Script

### 1-Minute Quick Demo

```bash
# Terminal 1: Start backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Start frontend
cd frontend/public && python3 -m http.server 3000

# Browser: Open http://localhost:3000/
# Type: "What are the symptoms of pneumonia?"
# Show: Natural language response with citations

# Upload: X-ray image
# Show: Classification result, confidence level, HITL flag
```

### 3-Minute Full Demo

1. **Text Query**: "What is pneumonia?" → Show RAG citations
2. **Web Search**: "Latest 2025 COVID treatment guidelines" → Show web sources
3. **Image Analysis**: Upload X-ray → Show VIT classification + confidence
4. **HITL Demonstration**: Show low confidence triggers human review
5. **Multi-modal**: Text + Image query → Show combined analysis

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0  
**Status**: ✅ Tested & Production Ready
