# 📁 Project Resources - Agentic Medical Assistant

**Quick reference for all documentation, scripts, and access points**

---

## 📚 Documentation Files

### 🚀 Deployment & Operations
| File | Purpose | When to Use |
|------|---------|-------------|
| **DEPLOYABLE.md** | Complete deployment guide | Setting up Docker, ngrok, production |
| **QUICKSTART.md** | 2-minute demo script | Right before hackathon presentation |
| **VALIDATION_REPORT.md** | System test results | Showing judges that it works |
| **README.md** | Project overview | First-time setup, general info |
| **AGENTS.md** | Technical architecture | Deep dive into system design |

### 🧪 Testing & Scripts
| File | Purpose | Command |
|------|---------|---------|
| **scripts/test_system.sh** | Automated test suite | `./scripts/test_system.sh` |
| **scripts/ingest_data.py** | PDF ingestion to vector DB | `python scripts/ingest_data.py` |
| **scripts/warm_start.py** | Pre-load models | `python scripts/warm_start.py` |

---

## 🌐 Access URLs (Local)

```
Frontend:        http://localhost:3000/
Backend API:     http://localhost:8000/health
API Docs:        http://localhost:8000/docs
Metrics:         http://localhost:8000/metrics
Backend Logs:    /tmp/backend.log
HITL Queue:      data/hitl_queue/
```

---

## 🔑 Key Commands

### Start System
```bash
# Terminal 1 - Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend/public && python3 -m http.server 3000
```

### Test System
```bash
# Automated tests
./scripts/test_system.sh

# Manual health check
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/api/process_input \
  -H "Content-Type: application/json" \
  -d '{"text_query": "What is pneumonia?"}'
```

### Stop System
```bash
# Kill all services
pkill -f uvicorn
pkill -f "http.server 3000"

# Or kill specific PIDs
kill 92763 92765  # Backend
kill 94307        # Frontend
```

### Check Status
```bash
# Check running processes
lsof -ti:8000  # Backend
lsof -ti:3000  # Frontend

# View logs
tail -f /tmp/backend.log

# Check HITL queue
ls -l data/hitl_queue/
```

---

## 📦 Project Structure

```
agentic-med-assistant/
├─ 📄 DEPLOYABLE.md          ← Deployment guide
├─ 📄 QUICKSTART.md          ← Demo script
├─ 📄 VALIDATION_REPORT.md   ← Test results
├─ 📄 RESOURCES.md           ← This file
├─ 📄 README.md              ← Project overview
├─ 📄 AGENTS.md              ← Architecture
├─ 📄 .env                   ← Config (DO NOT COMMIT)
├─ backend/
│  ├─ app/
│  │  ├─ main.py             ← FastAPI app
│  │  ├─ agents/             ← LangGraph nodes
│  │  ├─ services/           ← VIT, RAG, NLG, etc.
│  │  ├─ routers/            ← API endpoints
│  │  └─ models/             ← VIT weights
│  └─ pyproject.toml
├─ frontend/
│  ├─ public/
│  │  └─ index.html          ← Main UI
│  └─ src/
│     ├─ main.js             ← Frontend logic
│     └─ styles.css          ← Styling
├─ scripts/
│  ├─ test_system.sh         ← Test suite
│  └─ ingest_data.py         ← Data ingestion
├─ data/
│  ├─ knowledge_base/        ← Medical PDFs
│  ├─ qdrant_db/             ← Vector storage
│  └─ hitl_queue/            ← Flagged items
└─ docker/
   └─ Dockerfile             ← Container build
```

---

## 🎯 Demo Scenarios

### Scenario 1: Text Query
```
Query: "What is pneumonia?"
Shows: Natural language response, citations, confidence
```

### Scenario 2: Image Classification
```
Upload: Chest X-ray
Query: "Analyze this X-ray"
Shows: PNEUMONIA/NORMAL, confidence %, HITL flag
```

### Scenario 3: Multi-Modal
```
Upload: X-ray + Query: "Is this pneumonia? Treatment?"
Shows: Combined analysis, treatment info, confidence
```

### Scenario 4: Web Search (if triggered)
```
Query: "Latest 2025 COVID treatment guidelines"
Shows: Web sources from Brave API, citations
```

---

## 🧩 Service Configuration

### Environment Variables (.env)
```bash
# Required
GEMINI_API_KEY=your_key
BRAVE_API_KEY=your_key
VIT_MODEL=/absolute/path/to/vit-xray-pneumonia

# Database
QDRANT_MODE=disk
QDRANT_PATH=./data/qdrant_db

# Optional
STT_ENABLED=false
TTS_ENABLED=false
WEB_SEARCH_ENABLED=true
CONFIDENCE_THRESHOLD=0.70
```

### Model Paths
```
VIT Model: backend/app/models/vit-xray-pneumonia/
  ├─ model.safetensors
  ├─ config.json
  └─ preprocessor_config.json

Piper TTS: backend/app/models/piper-en_US-amy-medium/
  ├─ model.onnx
  └─ config.json
```

---

## 🔍 Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Backend won't start | Check .env path, VIT_MODEL absolute path |
| Frontend 404 | Use `localhost:3000/` not `/public/index.html` |
| Port in use | `lsof -ti:8000 \| xargs kill -9` |
| VIT model error | Verify absolute path in .env |
| CORS error | Add origin to FRONTEND_ORIGINS |
| Low confidence | Expected behavior, shows HITL flag |

See DEPLOYABLE.md Troubleshooting section for details.

---

## 📊 System Metrics

### Performance
- Text query: ~2-3 seconds
- Image classification: ~3-4 seconds
- Health check: <100ms

### Resources
- Backend RAM: ~2.5GB
- Frontend RAM: ~50MB
- Disk: ~2.8GB total

### Test Coverage
- ✅ 6/6 automated tests passing
- ✅ 4/4 manual cURL validations
- ✅ All service integrations tested

---

## 🏆 Hackathon Checklist

### Pre-Demo (2 minutes)
- [ ] Backend running: `curl localhost:8000/health`
- [ ] Frontend accessible: Open localhost:3000
- [ ] Test query works: Type "What is pneumonia?"
- [ ] Image upload ready: Have X-ray prepared
- [ ] Battery charged: Laptop plugged in

### During Demo (3 minutes)
- [ ] Show text query response
- [ ] Demonstrate image classification
- [ ] Point out confidence scoring
- [ ] Highlight HITL flagging
- [ ] Show multi-agent orchestration

### Judge Questions
- [ ] Review QUICKSTART.md Q&A section
- [ ] Can explain confidence system
- [ ] Can show HITL queue
- [ ] Can demonstrate multi-modal
- [ ] Have VALIDATION_REPORT.md ready

---

## 📞 Emergency Contacts

### If System Goes Down
1. Run `./scripts/test_system.sh` to diagnose
2. Check logs: `tail -f /tmp/backend.log`
3. Restart services (see "Stop System" above)
4. Verify with health check

### If Demo Fails
- **Plan B**: Show VALIDATION_REPORT.md
- **Plan C**: Walk through code in AGENTS.md
- **Plan D**: Show API docs at localhost:8000/docs

---

## 🎓 Learning Resources

### Understanding the System
1. Start with **README.md** - high-level overview
2. Read **AGENTS.md** - technical architecture
3. Check **VALIDATION_REPORT.md** - what works
4. Study `backend/app/agents/graph.py` - LangGraph flow

### API Exploration
1. Open http://localhost:8000/docs
2. Try "Try it out" on /process_input
3. Check /health and /metrics endpoints
4. View schemas in /openapi.json

### Code Deep Dive
- **Services**: `backend/app/services/` - VIT, RAG, NLG
- **Agents**: `backend/app/agents/nodes/` - LangGraph nodes
- **Routers**: `backend/app/routers/` - API endpoints
- **Frontend**: `frontend/src/main.js` - UI logic

---

## 📱 Contact Information

- **Project**: Agentic Medical Assistant
- **Hackathon**: PSU Hackathon 2025
- **Status**: ✅ Production Ready
- **Last Validated**: 2025-01-26

---

## 🎯 Final Checklist Before Judging

### Technical
- [ ] Backend healthy: ✅ Confirmed (PIDs 92763, 92765)
- [ ] Frontend accessible: ✅ Confirmed (PID 94307)
- [ ] All tests passing: ✅ 6/6 automated + 4/4 manual
- [ ] Documentation complete: ✅ 5 docs created

### Demo Prep
- [ ] QUICKSTART.md reviewed
- [ ] Test queries prepared
- [ ] X-ray images ready
- [ ] Browser tabs open
- [ ] Laptop charged

### Backup Plans
- [ ] Validation report ready
- [ ] Architecture diagram available
- [ ] Code walkthrough prepared
- [ ] API docs accessible

---

**Everything is ready! Open localhost:3000 and start demoing! 🚀**
