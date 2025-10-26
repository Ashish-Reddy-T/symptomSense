# 🚀 Agentic Medical Assistant - Enhancement Plan

**Date:** October 26, 2025  
**Status:** Planning Phase  
**Priority:** High

---

## 📊 Current State Analysis

### ✅ What's Working
- Multi-modal input processing (text, image, audio)
- RAG pipeline with Qdrant vector retrieval
- ViT-based X-ray pneumonia classification (91% confidence)
- LangGraph orchestration with confidence verification
- Document citations with source tracking

### ⚠️ Issues Identified

1. **Output Quality - Unnatural Language**
   - Current: Structured, technical responses with explicit disclaimers
   - Problem: Reads like a report, not conversational
   - Impact: Poor user experience, sounds robotic

2. **Over-Cautious Disclaimers (Human-in-the-Loop Gap)**
   - Current: "I am an AI and don't listen to what I say"
   - Problem: Undermines confidence in accurate predictions
   - Impact: Users may ignore correct information

3. **Limited Knowledge Scope**
   - Current: Only searches ingested PDFs
   - Problem: Can't answer questions outside knowledge base
   - Impact: Incomplete or outdated information

4. **Citation Format Issues**
   - Current: Image insights not properly numbered (doc1, doc2, etc.)
   - Problem: Inconsistent citation formatting
   - Impact: Confusing for users tracking sources

---

## 🎯 Enhancement Roadmap

### Phase 1: Natural Language Generation (NLG) Enhancement
**Goal:** Transform technical outputs into conversational, natural responses

#### Implementation Strategy
- **Prompt Engineering**: Rewrite system prompts for conversational tone
- **Response Templates**: Create context-aware templates (urgent vs. informational)
- **Confidence-Based Phrasing**: 
  - High confidence (>0.85): Direct, authoritative
  - Medium confidence (0.70-0.85): Balanced, suggestive
  - Low confidence (<0.70): Exploratory, questioning

#### Technical Changes
```python
# New module: backend/app/services/nlg_service.py
- response_naturalizer(raw_output, confidence_scores)
- tone_adjuster(text, confidence_level, urgency_flag)
- medical_phrasing_library()
```

---

### Phase 2: Human-in-the-Loop (HITL) System
**Goal:** Provide confident, accurate answers while maintaining safety

#### Confidence Threshold Strategy
```
High Confidence (>0.85):
  → Provide direct answer
  → Minimal disclaimers
  → Example: "Based on the X-ray analysis, this appears to be pneumonia."

Medium Confidence (0.70-0.85):
  → Provide answer with context
  → Suggest verification
  → Example: "The X-ray shows signs consistent with pneumonia. Additional tests would help confirm."

Low Confidence (<0.70):
  → HITL trigger: Flag for review
  → Provide tentative information
  → Example: "The image analysis is inconclusive. I recommend consulting with a radiologist."
```

#### Implementation
- **HITL Queue**: Store low-confidence queries for expert review
- **Confidence Calibration**: Adjust thresholds based on model performance
- **Smart Disclaimers**: Context-aware warnings (not blanket statements)
- **Fallback Strategies**: When to escalate vs. provide partial answers

#### Technical Changes
```python
# New module: backend/app/services/hitl_service.py
- confidence_evaluator(image_conf, rag_conf, llm_logprobs)
- disclaimer_generator(confidence_profile, query_type)
- hitl_queue_manager()

# New endpoints:
- POST /api/hitl/flag_for_review
- GET /api/hitl/pending_reviews
- POST /api/hitl/expert_feedback
```

---

### Phase 3: Web Search Agent (Brave API Integration)
**Goal:** Augment knowledge base with real-time web search for comprehensive answers

#### Use Cases
1. **Knowledge Gap Detection**: RAG returns low-relevance documents
2. **Recent Information**: Query requires latest research/guidelines
3. **Verification**: Cross-reference RAG results with current web sources
4. **Comprehensive Coverage**: Supplement PDF knowledge base

#### Agent Decision Logic
```python
def should_invoke_web_search(state):
    """
    Triggers:
    - RAG top result score < 0.5
    - Query contains temporal keywords ("latest", "current", "2024")
    - Explicit web search request
    - Zero RAG results
    """
    rag_score = max(state.get('rag_scores', [0]))
    query = state.get('text_query', '').lower()
    temporal_keywords = ['latest', 'current', 'recent', 'new', '2024', '2025']
    
    return (
        rag_score < 0.5 or
        any(kw in query for kw in temporal_keywords) or
        len(state.get('rag_context', [])) == 0
    )
```

#### Brave Search Integration
```python
# New module: backend/app/services/brave_search_service.py
- search_medical_web(query, num_results=5)
- extract_snippets(search_results)
- relevance_filter(results, threshold=0.6)
- deduplicate_sources(rag_results, web_results)
```

#### Technical Changes
- **Environment**: Add `BRAVE_API_KEY` to `.env`
- **Dependencies**: Add `brave-search-python>=1.0.0`
- **New Node**: `web_search_agent` in LangGraph
- **Response Merge**: Combine RAG + Web results with proper attribution

---

### Phase 4: Intelligent Agent Orchestration
**Goal:** Smart routing and combination of specialized agents based on confidence

#### Agent Combine Architecture
```python
# New module: backend/app/agents/agent_combine.py

class AgentOrchestrator:
    """
    Intelligent multi-agent coordinator
    """
    
    agents = {
        'image_analysis': ImageAnalysisAgent,
        'document_rag': DocumentRAGAgent,
        'web_search': WebSearchAgent,
        'medical_reasoning': MedicalReasoningAgent
    }
    
    def route_query(state) -> List[str]:
        """
        Returns list of agents to invoke based on:
        - Query type
        - Confidence scores
        - Previous agent results
        """
        
    def combine_results(agent_outputs) -> FinalOutput:
        """
        Merge multiple agent outputs:
        - Weight by confidence
        - Resolve contradictions
        - Attribute sources
        """
        
    def confidence_weighted_merge(results):
        """
        Priority:
        1. High-confidence image (>0.85)
        2. High-relevance RAG (score >0.6)
        3. Recent web results (published <1yr)
        4. Lower confidence sources
        """
```

#### Routing Logic
```
Input Query
    ↓
[Classifier] → Determine query type + modalities
    ↓
┌─────────────────────────────────┐
│   Agent Selection Logic         │
├─────────────────────────────────┤
│ • Image? → Image Agent          │
│ • Text + Docs? → RAG Agent      │
│ • RAG confidence < 0.5?         │
│   → Web Search Agent            │
│ • Complex medical reasoning?    │
│   → Medical Reasoning Agent     │
└─────────────────────────────────┘
    ↓
[Parallel Execution] → Run selected agents
    ↓
[Confidence Evaluation]
    ↓
┌─────────────────────────────────┐
│ Need more agents?               │
│ • Image conf high but RAG low?  │
│   → Trigger Web Search          │
│ • Contradictory results?        │
│   → Trigger Reasoning Agent     │
└─────────────────────────────────┘
    ↓
[Agent Combine] → Weighted merge
    ↓
[NLG Service] → Natural language output
    ↓
[HITL Check] → Flag if needed
    ↓
Final Response
```

#### Decision Matrix

| Scenario | Agents Invoked | Merge Strategy |
|----------|----------------|----------------|
| Image only, high conf (>0.85) | Image | Direct output + contextual info |
| Image + text, both high conf | Image + RAG | Combine with equal weight |
| Image high, RAG low (<0.5) | Image + RAG + Web | Prioritize image, supplement with web |
| Text only, RAG high (>0.6) | RAG | Direct output with citations |
| Text only, RAG low (<0.5) | RAG + Web | Merge, prefer recent web sources |
| All agents low confidence | All + HITL flag | Present uncertainty, queue review |

---

## 🛠️ Technical Implementation Details

### New File Structure
```
backend/app/
├── agents/
│   ├── agent_combine.py          # NEW: Orchestrator
│   ├── graph.py                  # MODIFIED: Add web agent
│   └── nodes/
│       ├── web_search.py         # NEW: Brave search agent
│       └── medical_reasoning.py  # NEW: Advanced reasoning
├── services/
│   ├── brave_search_service.py   # NEW: Brave API wrapper
│   ├── nlg_service.py            # NEW: Natural language generation
│   ├── hitl_service.py           # NEW: Human-in-the-loop
│   └── confidence_service.py     # NEW: Unified confidence scoring
└── models/
    └── hitl_schema.py            # NEW: HITL data models
```

### Environment Variables to Add
```bash
# Brave Search
BRAVE_API_KEY=your_brave_key_here
BRAVE_SEARCH_ENABLED=true
BRAVE_MAX_RESULTS=5

# HITL Configuration
HITL_ENABLED=true
HITL_CONFIDENCE_THRESHOLD=0.70
HITL_QUEUE_PATH=./data/hitl_queue

# NLG Configuration
NLG_TONE=professional_conversational  # options: clinical, conversational, professional_conversational
NLG_DISCLAIMER_MODE=smart             # options: minimal, smart, verbose

# Agent Orchestration
AGENT_PARALLEL_EXECUTION=true
AGENT_WEB_FALLBACK_THRESHOLD=0.5
AGENT_MAX_RETRIES=2
```

### Dependencies to Add
```toml
# pyproject.toml additions
dependencies = [
    # ... existing deps
    "brave-search-python>=1.0.0",
    "nltk>=3.8.1",              # For NLG text processing
    "spacy>=3.7.0",             # Advanced NLP
    "dateparser>=1.2.0",        # Temporal query parsing
]
```

---

## 📝 Implementation Todo List

### Sprint 1: Foundation & NLG (Days 1-2)
- [ ] Create `nlg_service.py` with response naturalizer
- [ ] Design confidence-based phrasing templates
- [ ] Update `final_generation` node to use NLG service
- [ ] Create medical phrasing library (professional but conversational)
- [ ] Test output quality with sample queries
- [ ] Update confidence verification to generate smart disclaimers

### Sprint 2: HITL System (Days 2-3)
- [ ] Create `hitl_service.py` with confidence evaluator
- [ ] Implement HITL queue manager with persistence
- [ ] Add `hitl_schema.py` data models
- [ ] Create HITL API endpoints (`/api/hitl/*`)
- [ ] Update confidence thresholds in settings
- [ ] Add HITL flag to final response schema
- [ ] Create simple HITL review interface (optional)

### Sprint 3: Brave Search Integration (Days 3-4)
- [ ] Add Brave API key to `.env`
- [ ] Install `brave-search-python` dependency
- [ ] Create `brave_search_service.py`
- [ ] Implement medical-focused search query builder
- [ ] Add snippet extraction and relevance filtering
- [ ] Create `web_search.py` agent node
- [ ] Test Brave API integration
- [ ] Handle rate limits and errors gracefully

### Sprint 4: Agent Orchestration (Days 4-5)
- [ ] Create `agent_combine.py` orchestrator class
- [ ] Implement agent routing logic
- [ ] Add confidence-weighted merge function
- [ ] Update LangGraph to include web search agent
- [ ] Add conditional edges for web search trigger
- [ ] Implement parallel agent execution
- [ ] Create contradiction resolver
- [ ] Add source attribution merging

### Sprint 5: Integration & Testing (Days 5-6)
- [ ] Update `graph.py` with new orchestration logic
- [ ] Connect all services (NLG, HITL, Brave)
- [ ] Update response DTOs to include web sources
- [ ] Fix citation formatting (doc1, doc2, etc.)
- [ ] Add web source citations (web1, web2, etc.)
- [ ] Create unified confidence scoring service
- [ ] Test end-to-end flows with all combinations
- [ ] Update frontend to display new response format

### Sprint 6: Polish & Documentation (Day 6-7)
- [ ] Update API documentation (Swagger)
- [ ] Create agent orchestration diagram
- [ ] Update TESTING_GUIDE.md with new features
- [ ] Add example queries for each scenario
- [ ] Performance optimization (caching, parallel calls)
- [ ] Error handling and fallback strategies
- [ ] Create monitoring dashboard for agent performance
- [ ] Final integration testing

---

## 🎨 Response Format Examples

### Before (Current)
```
Answer
The image insights provided predict PNEUMONIA with a confidence of 0.91.

Sources:
- doc1: data/knowledge_base/influenza_vaccines_PMC.pdf (score=0.331)
...

Warnings:
- The information provided is based on an AI-generated prediction...
```

### After (Enhanced)
```
Based on the X-ray analysis, this appears to be pneumonia. The imaging shows 
characteristic patterns consistent with pneumonic consolidation, with a 91% 
confidence level.

This assessment aligns with current medical literature on pneumonia diagnosis 
[doc1, doc2]. Recent clinical guidelines also emphasize the importance of 
correlating imaging findings with patient symptoms and history [web1].

Next Steps:
• Correlate with clinical symptoms (fever, cough, difficulty breathing)
• Consider sputum culture or blood tests to identify the causative pathogen
• Consult with a healthcare provider for treatment options

Sources:
• doc1: Influenza Vaccines and Pneumonia (PMC, 2024)
• doc2: Upper Respiratory Infections (PMC, 2023)
• web1: ATS Clinical Guidelines - Pneumonia Diagnosis (2024)

Note: While this analysis shows high confidence, a formal diagnosis should 
be confirmed by a qualified healthcare professional who can consider your 
complete clinical picture.
```

---

## 🔍 Success Metrics

### Before/After Comparison

| Metric | Current | Target |
|--------|---------|--------|
| Response naturalness | 3/10 | 8/10 |
| User confidence in answers | Low | High (with appropriate caveats) |
| Knowledge coverage | PDF-only | PDF + Real-time web |
| Citation accuracy | 70% | 95% |
| Response relevance | 75% | 90% |
| Unnecessary disclaimers | Many | Minimal, context-aware |

### KPIs to Track
- Average confidence score per query type
- Web search trigger rate
- HITL queue size and resolution time
- User satisfaction (if feedback mechanism added)
- Response time (should stay <5 seconds)

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Brave API rate limits | Service unavailable | Implement caching, fallback to RAG-only |
| Increased response time | Poor UX | Parallel execution, streaming responses |
| Over-confident incorrect answers | User harm | Maintain smart disclaimers, HITL queue |
| Citation format confusion | Trustworthiness | Unified citation numbering system |
| Web search hallucinations | Misinformation | Relevance filtering, source verification |

---

## 🚀 Future Enhancements (Post-Hackathon)

1. **Multi-turn Conversation**: Remember context across queries
2. **Personalization**: Adapt tone based on user expertise level
3. **Batch Processing**: Analyze multiple images simultaneously
4. **Expert Network**: Connect HITL to real medical professionals
5. **Feedback Loop**: Learn from user corrections
6. **Mobile App**: Native iOS/Android interface
7. **FHIR Integration**: Connect to EHR systems
8. **Multi-language Support**: Translate queries and responses

---

## 📚 References & Resources

- **Brave Search API Docs**: https://brave.com/search/api/
- **LangGraph Multi-Agent Patterns**: https://langchain-ai.github.io/langgraph/
- **Medical NLG Best Practices**: Clinical communication guidelines
- **Human-in-the-Loop ML**: Research papers on confidence calibration

---

**Last Updated:** October 26, 2025  
**Next Review:** After Sprint 3 completion
