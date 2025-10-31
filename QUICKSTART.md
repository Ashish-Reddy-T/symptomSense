# 🎯 QUICK START - Agentic Medical Assistant

**QuickStart for NewBies**

---

## ⚡ Fastest Path to Running Demo

### Step 1: Check Prerequisites (30 seconds)
```bash
# Verify backend is running
curl http://localhost:8000/health  # Should return {"status":"ok"}

# Choose your frontend:
# Option A: AngularJS (Recommended - Modern UI with voice/image)
curl http://localhost:4200/        # Should return HTML

# Option B: Legacy Vanilla JS
curl http://localhost:3000/        # Should return HTML

# If not running, see "Start Services" below
```

### Step 2: Open Browser (10 seconds)
```
# AngularJS Frontend (Recommended):
http://localhost:4200/

# OR Legacy Frontend:
http://localhost:3000/public/
```

---

## 🚀 Start Services (if not running)

### Terminal 1 - Backend
```bash
cd /Users/AshishR_T/Desktop/hackPSU/agentic-med-assistant/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Wait for: "Application startup complete"
```

### Terminal 2 - Frontend (Choose One)

#### Option A: AngularJS Frontend (Recommended)
```bash
cd /Users/AshishR_T/Desktop/hackPSU/agentic-med-assistant/angularJS
npm install --legacy-peer-deps  # First time only
npm run start:local

# Opens at: http://localhost:4200
# Features: Voice input, image upload, session management, modern UI
```

#### Option B: Legacy Vanilla JS Frontend
```bash
cd /Users/AshishR_T/Desktop/hackPSU/agentic-med-assistant/frontend
python3 -m http.server 3000

# Opens at: http://localhost:3000/public/
# Features: Basic text/image input
```

### Verify
```bash
# Run test suite
cd /Users/AshishR_T/Desktop/hackPSU/agentic-med-assistant
./scripts/test_system.sh
```

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

## 🧪 Sample Test Queries

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

## 🎬 Go Voice Your Thoughts

"Hi! We built an intelligent medical assistant that doesn't just answer questions - it knows when to be uncertain. Let me show you..."

**SAMPLE**: [Open http://localhost:4200/ and click "Start Consultation", then type "What is pneumonia?" OR use voice input]

---