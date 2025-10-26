# 🎯 QUICK START - Agentic Medical Assistant

**For Hackathon Demo - 2 Minute Setup**

---

## ⚡ Fastest Path to Running Demo

### Step 1: Check Prerequisites (30 seconds)
```bash
# Verify backend and frontend are running
curl http://localhost:8000/health  # Should return {"status":"ok"}
curl http://localhost:3000/        # Should return HTML

# If not running, see "Start Services" below
```

### Step 2: Open Browser (10 seconds)
```
http://localhost:3000/public/
```

### Step 3: Run Demo Query (20 seconds)
1. Type: **"What are the symptoms of pneumonia?"**
2. Click **"Run"**
3. Show response with:
   - Natural language answer
   - Confidence score
   - Citations

### Step 4: Image Demo (1 minute)
1. Upload chest X-ray image
2. Type: **"Analyze this X-ray"**
3. Click **"Run"**
4. Show:
   - Classification result (NORMAL/PNEUMONIA)
   - Confidence percentage
   - HITL flag if low confidence

---

## 🚀 Start Services (if not running)

### Terminal 1 - Backend
```bash
cd /Users/AshishR_T/Desktop/hackPSU/agentic-med-assistant/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Wait for: "Application startup complete"
```

### Terminal 2 - Frontend
```bash
cd /Users/AshishR_T/Desktop/hackPSU/agentic-med-assistant/frontend
python3 -m http.server 3000
```

### Verify
```bash
# Run test suite
cd /Users/AshishR_T/Desktop/hackPSU/agentic-med-assistant
./scripts/test_system.sh
```

---

## 🎤 Demo Script (3 minutes)

### Introduction (30 seconds)
"We built an agentic medical assistant that combines multiple AI services:
- Vision Transformer for X-ray analysis
- RAG with medical knowledge base
- Web search for latest information
- Confidence scoring with human-in-loop
- LangGraph orchestration"

### Demo 1: Text Query (45 seconds)
1. Navigate to http://localhost:3000/
2. Query: "What is pneumonia?"
3. Point out:
   - Natural language response (NLG service)
   - Knowledge base citations (RAG)
   - Confidence score (medium/high)

### Demo 2: Image Classification (60 seconds)
1. Upload X-ray image
2. Query: "What does this show?"
3. Point out:
   - ViT classification (PNEUMONIA/NORMAL)
   - Confidence percentage
   - **HITL flag** if low confidence
   - Disclaimer about medical review

### Demo 3: Multi-Modal (45 seconds)
1. Upload image + text: "Is this pneumonia? What treatment?"
2. Point out:
   - Combined image + text analysis
   - Orchestrator routing to multiple agents
   - Treatment recommendations from knowledge base
   - Overall confidence aggregation

---

## 🔧 Emergency Fixes

### "Backend not responding"
```bash
# Check if running
lsof -ti:8000

# If not, start it
cd backend && uvicorn app.main:app --reload
```

### "Frontend 404 error"
```bash
# Serve from the frontend ROOT so /public and /src are both available
cd frontend && python3 -m http.server 3000

# Then open the index from the public folder
open http://localhost:3000/public/

# If you must serve from frontend/public, change paths in index.html
# from /src/... to ./... and copy the JS/CSS into public/ (quick but hacky).
```

### "VIT model error"
```bash
# Check .env has absolute path
grep VIT_MODEL ../.env
# Should show: VIT_MODEL=/Users/.../vit-xray-pneumonia
```

### "Run full diagnostics"
```bash
./scripts/test_system.sh
# Should show all green checkmarks
```

---

## 📊 Key Metrics to Highlight

- **6+ Specialized Services**: NLG, HITL, Confidence, Brave, VIT, RAG, Orchestrator
- **Multi-Modal**: Text, images, and combinations
- **Confidence-Aware**: System knows when it's uncertain
- **HITL Integration**: Low confidence → human review queue
- **Production Ready**: Docker, tests, metrics, docs

---

## 🌐 URLs Cheatsheet

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000/ | Main UI |
| Backend Health | http://localhost:8000/health | Status check |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Metrics | http://localhost:8000/metrics | Prometheus |
| Logs | `/tmp/backend.log` | Backend logs |
| HITL Queue | `data/hitl_queue/` | Flagged items |

---

## 🧪 Test Queries

### Simple Medical
```
"What is pneumonia?"
"How to treat a fever?"
"Symptoms of bronchitis?"
```

### Temporal (Web Search)
```
"Latest 2025 COVID treatment guidelines"
"Recent developments in pneumonia vaccines"
"New 2025 medical research on antibiotics"
```

### Image Classification
```
Upload X-ray + "Analyze this chest X-ray"
Upload X-ray + "What abnormalities do you see?"
Upload X-ray + "Is this pneumonia?"
```

### Multi-Modal
```
Upload X-ray + "Is this pneumonia? What's the treatment?"
Upload X-ray + "Diagnose and recommend next steps"
```

---

## 🏆 Judge Questions - Prepared Answers

**Q: How does your system handle uncertainty?**
A: We use confidence scoring across multiple sources (VIT, LLM, RAG) and aggregate them. Low confidence (<70%) automatically flags items for human review in our HITL queue.

**Q: How is this different from ChatGPT?**
A: We use specialized agents (image classifier, medical RAG, web search) orchestrated by LangGraph. Each agent is expert in its domain, and we combine their outputs with confidence tracking.

**Q: What if the model is wrong?**
A: Low confidence cases are automatically flagged for medical professional review. We also provide citations so users can verify information sources.

**Q: Can it handle multi-modal inputs?**
A: Yes! Upload an X-ray and ask a text question - our orchestrator routes to both image analysis and text processing agents, then combines results.

**Q: How do you ensure medical accuracy?**
A: Three layers: (1) RAG from curated medical documents, (2) Confidence scoring to detect uncertainty, (3) HITL flagging for professional review.

---

## 📱 Backup Plans

### Plan A: Local Demo (Primary)
- Both servers on localhost
- Fastest, most reliable
- No internet dependency for core features

### Plan B: Ngrok Public Demo
```bash
ngrok http 8000  # Get public URL
# Update frontend/src/api.js with ngrok URL
# Share public link with judges
```

### Plan C: Video Recording
- Record successful demo beforehand
- Show validation report (VALIDATION_REPORT.md)
- Walk through code architecture (AGENTS.md)

---

## ✅ Pre-Demo Checklist (60 seconds)

- [ ] Backend running: `curl localhost:8000/health` → `{"status":"ok"}`
- [ ] Frontend accessible: `curl localhost:3000/` → HTML
- [ ] Test query works: Type "What is pneumonia?" → Get response
- [ ] Image upload works: Upload X-ray → Get classification
- [ ] Confidence visible: Check response shows confidence level
- [ ] HITL queue exists: `ls data/hitl_queue/` → Files present
- [ ] Battery charged: Laptop plugged in
- [ ] Browser tabs ready: localhost:3000, localhost:8000/docs

---

## 🎬 Opening Line

"Hi! We built an intelligent medical assistant that doesn't just answer questions - it knows when to be uncertain. Let me show you..."

[Open http://localhost:3000/ and type "What is pneumonia?"]

---

**Last Updated**: 2025-01-26  
**Status**: ✅ READY FOR DEMO  
**Estimated Demo Time**: 3-5 minutes
