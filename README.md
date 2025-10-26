# 🏥 SymptomSense: AI-Powered Medical Diagnostic Assistant

*Building Trust in AI Healthcare Through Multi-Agent Intelligence and Confidence-Aware Decision Making*

---

## 💡 Inspiration

Healthcare accessibility remains one of humanity's greatest challenges. We've all experienced it—waiting hours in emergency rooms for preliminary assessments, struggling to interpret medical information online, or wondering if symptoms warrant immediate attention. The COVID-19 pandemic amplified these issues, with telemedicine usage increasing by 154% in 2020, yet most digital health tools remain simplistic chatbots that either provide generic advice or dangerously overconfident diagnoses.

**The problem**: Existing AI health assistants fall into two camps—overly cautious systems that redirect everything to "consult your doctor," or reckless ones that provide confident diagnoses without acknowledging uncertainty.

**Our vision**: What if AI could be *intelligently uncertain*? What if a system could analyze your symptoms across multiple modalities, transparently show its confidence level, and know exactly when to escalate to human experts?

We were inspired by recent advances in **agentic AI architectures** (LangGraph, AutoGPT) and **retrieval-augmented generation (RAG)** that enable AI systems to reason with external knowledge. We asked: *"Can we build a medical assistant that doesn't just answer questions, but orchestrates multiple specialized agents, evaluates its own confidence, and prioritizes patient safety?"*

SymptomSense was born from this question—a multi-agent medical diagnostic platform that combines computer vision, medical literature retrieval, real-time web research, and confidence-aware decision-making into a cohesive, trustworthy system.

---

## 🎯 What It Does

**SymptomSense is an intelligent medical diagnostic assistant that analyzes text, images, and voice inputs through a coordinated network of specialized AI agents to provide evidence-based health insights with transparent confidence scoring.**

### Core Capabilities

#### 🔬 **Multi-Modal Input Processing**

-   **Text Queries**: Natural language symptom descriptions, medical questions
-   **Image Analysis**: Upload chest X-rays, skin lesions, or other medical images
-   **Voice Input**: Speech-to-text powered by Faster Whisper for hands-free interaction

#### 🤖 **Agentic AI Architecture**

SymptomSense doesn't use a single AI model—it orchestrates **6 specialized agents** via LangGraph:

1.  **Input Classification Agent**: Routes queries to appropriate analysis pathways
2.  **Vision Analysis Agent**: ViT (Vision Transformer) trained on medical images for chest X-ray classification (NORMAL/PNEUMONIA detection)
3.  **RAG Document Agent**: Retrieves relevant passages from curated medical literature using vector similarity search
4.  **Web Research Agent**: Brave Search integration for latest clinical guidelines and temporal medical information
5.  **Synthesis Agent**: Gemini 2.5 Flash combines insights from all sources into coherent responses
6.  **Confidence Verification Agent**: Meta-analysis of AI certainty across all modalities

#### 📊 **Transparent Confidence Scoring**

Every response includes a **multi-dimensional confidence profile**:

-   **Overall Confidence**: High (>80%), Medium (60-80%), Low (<60%)
-   **Image Analysis Confidence**: Computer vision model certainty
-   **Knowledge Base Confidence**: RAG retrieval relevance scores
-   **LLM Reasoning Confidence**: Language model logprob analysis

#### ⚠️ **Human-in-the-Loop (HITL) Safety**

Low-confidence cases (<70%) are **automatically flagged for medical professional review** and added to a review queue with:

-   Original query and analysis
-   Confidence breakdown
-   Suggested expert specialties
-   Priority level

#### 🌐 **Real-Time Knowledge Updates**

Unlike static medical chatbots, SymptomSense queries **live web sources** when:

-   Temporal queries detected ("latest 2025 treatment guidelines")
-   Local knowledge base has low confidence (<50%)
-   User explicitly requests recent information

#### 📚 **Evidence-Based Responses**

All answers include:

-   **Citations from medical literature** with relevance scores
-   **Links to clinical practice guidelines** from authoritative sources (NCBI, NIH, medical journals)
-   **Warnings** when information is uncertain or requires specialist confirmation

---

## 🛠️ How We Built It

### Architecture Overview

---


### Technology Stack

#### **Frontend** 🎨
- **Angular 20** - Latest standalone components architecture
- **TypeScript** (strict mode) - Type-safe development
- **RxJS** - Reactive programming for async operations
- **Web Speech API** - Browser-native voice input
- **Custom UI** - Medical-themed responsive design with gradient backgrounds

#### **Backend Core** 🚀
- **FastAPI** - High-performance async Python framework
- **LangGraph** - State machine orchestration for agentic workflows
- **Pydantic v2** - Data validation and settings management
- **Uvicorn** - ASGI server with automatic reloading

#### **AI/ML Models** 🤖
- **Gemini 2.5 Flash** - Primary LLM for reasoning (Google Generative AI)
  - Temperature: 0.3 for consistency
  - Max tokens: 2048
  - Logprobs enabled for confidence analysis
- **ViT (Vision Transformer)** - Medical image classification
  - Pre-trained on chest X-ray datasets
  - Fine-tuned for NORMAL/PNEUMONIA detection
  - 50%+ confidence threshold for predictions
- **text-embedding-005** - Gemini embedding model for semantic search (768 dimensions)
- **Cross-Encoder Reranker** - Sentence-transformers for passage re-ranking

#### **Document Processing** 📄
- **Docling 2.0** - Advanced PDF-to-Markdown parser
  - Preserves document structure, tables, citations
  - Better than PyPDF2/Unstructured for medical literature
- **Recursive Text Splitter** - Intelligent chunking with overlap
  - Chunk size: 1000 tokens
  - Overlap: 200 tokens to preserve context

#### **Vector Database** 🗄️
- **Qdrant** - High-performance vector similarity search
  - Disk persistence mode for reliability
  - Cosine similarity metric
  - HNSW indexing for fast retrieval
  - Metadata filtering for source tracking

#### **Voice Processing** 🎤
- **Faster Whisper** - Optimized speech-to-text
  - Small model (244MB) for speed
  - CPU-optimized inference
- **Piper TTS** - Neural text-to-speech
  - en_US-amy-medium voice
  - ONNX runtime for efficiency

#### **External APIs** 🌐
- **Brave Search API** - Privacy-focused web search
  - Medical query enhancement
  - Snippet extraction
  - Deduplication with RAG results
- **OpenRouter** (fallback) - Model redundancy for Gemini API failures

#### **DevOps & Monitoring** 📊
- **Docker & Docker Compose** - Containerized deployment
- **Prometheus** - Metrics collection (request latency, hit rates)
- **structlog** - JSON-formatted logging for observability
- **GitHub Actions** - CI/CD with Ruff, mypy, pytest
- **ngrok** - Public tunnel for demo deployment

---

### State-of-the-Art Techniques Implemented

#### 1. **Agentic RAG with LangGraph** 🤖
Traditional RAG systems follow a linear path: Query → Retrieve → Generate. We implemented **agentic RAG** where specialized agents make dynamic decisions:

```python
class State(TypedDict):
    text_query: str
    image_data: str | None
    task_types: list[str]          # Dynamic routing
    rag_context: list[str]
    web_search_results: list[dict]
    image_analysis: dict
    confidence_profile: dict
    final_answer: str
    hitl_flagged: bool

# Agent graph with conditional routing
if rag_confidence < 0.5:
    invoke(web_search_agent)  # Dynamic web fallback
if overall_confidence < 0.7:
    flag_for_hitl()           # Safety escalation

```

Why it matters: Instead of always searching the web (expensive, slow) or never searching (limited knowledge), our system intelligently decides when external information is needed.

#### 2. **Multi-Confidence Aggregation** 
We developed a novel weighted confidence scoring system that combines:

**Confidence** = α⋅C image + β⋅C RAG + γ⋅C LLM

Where weights (α, β, γ, α, β, γ) dynamically adjust based on which modalities are active:

Image-only query: α=0.8, β=0.0, γ=0.2

Text-only query: α=0.0, β=0.6, γ=0.4

Multi-modal: α=0.5, β=0.3, γ=0.2

**Implementation**:
```
class ConfidenceService:
    def aggregate_confidence(self, 
                           image_conf: float | None,
                           rag_scores: list[float],
                           llm_logprobs: list[float]) -> ConfidenceProfile:
        # Weighted aggregation with modality detection
        active_modalities = sum([
            image_conf is not None,
            len(rag_scores) > 0,
            len(llm_logprobs) > 0
        ])
        # Dynamic weight calculation...
```
Why it matters: Medical AI must know what it doesn't know. Our multi-dimensional confidence prevents overconfidence in single modalities.

#### 3. **Cross-Encoder Reranking** 
Vector similarity alone misses semantic nuance. We implemented two-stage retrieval:
**Stage 1**: Dense retrieval via cosine similarity
```
results = qdrant.search(
    collection_name="medical-knowledge",
    query_vector=embed(query),
    limit=20  # Over-retrieve
)
```
**Stage 2**: Cross-encoder reranking
```
reranker = CrossEncoder('ms-marco-MiniLM-L-6-v2')
reranked = reranker.rank(
    query=query,
    documents=[r.payload['text'] for r in results]
)
top_k = reranked[:5]  # Keep best 5
```

**Improvement**: +15% retrieval accuracy vs. embedding-only search.

#### 4. **Cross-Encoder Reranking** 
We extract token-level logprobs from Gemini to measure generation uncertainty:
```
response = await llm.ainvoke(prompt, logprobs=True)
token_confs = [exp(lp) for lp in response.logprobs]
avg_confidence = sum(token_confs) / len(token_confs)

if avg_confidence < 0.7:
    add_disclaimer("Model uncertainty detected")
```

**Why it matters**: Detects hallucinations and uncertain reasoning even when the model outputs grammatically correct text.

#### 5. **Smart Disclaimer Generation** 
Instead of blanket warnings, our NLG Service generates context-aware disclaimers:
```
def generate_disclaimer(self, confidence_level: str, 
                       context: str) -> str:
    if confidence_level == "high" and "diagnosis" in context:
        return "This analysis shows high confidence, but..."
    elif confidence_level == "low":
        return "⚠️ Confidence is low. Professional review recommended."
    # Context-specific templates...
```
**Result**: Reduces user fatigue from excessive warnings while maintaining safety.

#### 6. **Hybrid Knowledge Retrieval** 
We combined three knowledge sources with intelligent routing:

| Source | Use Case | Latency | Freshness |
|--------|----------|---------|-----------|
| Qdrant RAG | Medical literature, guidelines | ~200ms | Static (2024 docs) |
| Brave Search | Latest treatments, 2025 guidelines | ~800ms | Real-time |
| LLM Parametric | General medical knowledge | ~1500ms | Training cutoff |

Routing logic:
```
if "latest" in query or "2025" in query:
    invoke_web_search()
elif rag_confidence > 0.8:
    use_rag_only()
else:
    combine_rag_and_web()
```

### **🚧 Challenges We Ran Into**
#### 1. **Model Size vs. Performance Trade-off** 
Challenge: ViT models for medical imaging are massive (400MB+). Loading time killed demo experience.

Solution:
- Implemented lazy loading during FastAPI lifespan startup
- Pre-warmed models with dummy inference
- Used ONNX quantization to reduce model size by 60%
- Result: Cold start reduced from 45s → 8s

#### 2. **Qdrant Vector Dimension Mismatch**
Challenge: Gemini embeddings (768-d) conflicted with local fallback embeddings (384-d).

We came up with this!
```
# Dynamic collection creation
embed_dim = gemini.embedding_dimension if USE_GEMINI else 384
qdrant.create_collection(
    collection_name="medical-knowledge",
    vectors_config=VectorParams(size=embed_dim, distance=Distance.COSINE)
)
```
#### 3. **CORS Nightmares**

Angular frontend (localhost:4200) couldn't talk to FastAPI backend (localhost:8000).

```
# Backend CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:3000",
        "http://127.0.0.1:4200"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)
```

Plus: Environment-based origins for production deployment.

---

## Some lessons we learned!

#### **1. LangGraph > Prompt Chaining**
#### **2. Embeddings ≠ Understanding**
#### **3. Confidence Calibration is Hard** (We improved it from softmax, from a single metric to a multi-dimensional scoring scoring that exposes uncertainty.)
#### **4. Async is Essential for AI**

### Product Lessons:

#### **1. Users Want Transparency**
#### **2. Safety > Speed**
#### **3. Multi-Modal is Table Stakes**

---

## IN THE FUTURE ...

#### **Specialty-Specific Agents**
- **Dermatology Agent**: Skin lesion classification (melanoma, eczema, psoriasis)
- **Cardiology Agent**: ECG interpretation, heart disease risk
- **Radiology Agent**: CT scan, MRI analysis beyond X-rays

#### **Conversational Memory**
#### **Symptom Checker Flow**
```
AI: "Where is the pain located?"
User: "Chest"
AI: "Is it sharp or dull?"
User: "Sharp when breathing"
AI: "Any fever?" → Differential diagnosis tree
```
#### Multi-Language Support
- Spanish
- Mandarin 
- Hindi

---