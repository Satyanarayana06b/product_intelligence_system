# Tech Talk: Building an Intelligent Product Recommendation System
## Slide Content for Presentation (30-45 min)

---

## Slide 1: Title + Hook
**Title:** Building an Intelligent Product Recommendation System  
**Subtitle:** RAG, Clarification Logic, and Session Memory in Action

**Hook Visual:**
```
❌ Traditional Approach:
   User → 100+ page catalog → Sales rep → Multiple emails → Days

✅ Our Solution:
   User → "18V tool for tightening" → AI Assistant → Result → 2 seconds
```

**Speaker Notes:**
- Start with relatable problem: finding right industrial tool = needle in haystack
- Traditional: Manual catalog search, sales dependency, slow
- Your solution: Conversational AI that understands user intent

---

## Slide 2: Problem Statement
**The Challenge:**
- **100+ industrial tools** with complex specifications
- **Generic queries:** "tool", "machine", "18V"
- **Multi-turn conversations:** Users refine needs over time
- **Accuracy critical:** Wrong tool = production issues

**Why Hard?**
```
User Query: "tool"
❌ Without Intelligence: Returns random/hallucinated product
✅ With Intelligence: "What type? Assembly, Controller, Verification?"

User Query: "18V cordless nutrunner"
❌ Without Intelligence: Misses "18V" → wrong voltage tool
✅ With Intelligence: Exact match with specs filtering
```

**Key Pain Points:**
1. Vague queries → Hallucinations
2. Specification matching (18V vs 230V)
3. Context loss in conversations
4. Maintaining accuracy with growing catalog

---

## Slide 3: Solution Overview
**What We Built:**
AI-powered conversational assistant for industrial tool recommendations

**Core Capabilities:**
- 🔍 **Hybrid Search:** Semantic understanding + Metadata filtering
- 💬 **Smart Clarification:** Detects vague queries before LLM invocation
- 🧠 **Session Memory:** Tracks conversation context and filters
- 🎯 **Accurate Results:** No hallucinations, only database-backed recommendations

**User Experience:**
```
User: "tool"                        → Clarification asked
User: "nutrunner"                   → Voltage options shown
User: "18V"                         → Cordless nutrunner recommended ✓
(Same session)
User: "show manual version"         → Uses 18V context → Manual nutrunner ✓
```

---

## Slide 4: Architecture Diagram
**System Flow:**

```
┌─────────────┐
│   User      │
│  (Streamlit)│
└──────┬──────┘
       │ Query
       ↓
┌─────────────────────────┐
│  FastAPI Backend        │
│  /chat endpoint         │
└──────┬──────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Session Manager         │
│  • Get/Create Session    │
│  • Accumulated Filters   │
│  • Conversation History  │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Query Parser            │
│  • Extract Filters       │
│  • Voltage, Torque, IP   │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Semantic Search (FAISS) │
│  • Embed Query           │
│  • Apply Metadata Filters│
│  • Top-K Results         │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Clarification Check     │
│  • needs_clarification() │
│  • Dynamic Tool Names    │
└──────┬───────────────────┘
       │
   ┌───┴────┐
   │        │
   ↓        ↓
 Clarify  Execute
   │        │
   │        ↓
   │   ┌────────────────┐
   │   │  CrewAI Agent  │
   │   │  (GPT-4o-mini) │
   │   └────────┬───────┘
   │            │
   └────────────┴────────→ Response
```

---

## Slide 5: Tech Stack
**Frontend:**
- **Streamlit** - Rapid UI development
- Session management via cookies
- Real-time chat interface

**Backend:**
- **FastAPI** - High-performance async API
- **CrewAI** - Agent orchestration framework
- **OpenAI GPT-4o-mini** - LLM for recommendations

**Vector Database:**
- **FAISS** - Fast similarity search
- **text-embedding-3-small** - OpenAI embeddings
- In-memory index (100+ tools scale)

**Additional:**
- **Python** - Core language
- **Regex** - Metadata filter extraction
- **JSON** - Tool database storage

---

## Slide 6: Challenge 1 - Vague Queries 🤔

**The Problem:**
```python
User: "tool"
LLM: *hallucinates* "Here's the XYZ-2000 Multi-Tool..."
```

**The Solution: Dynamic Clarification System**

**Code Snippet:**
```python
def needs_clarification(query, filters, filtered_tools):
    query_lower = query.lower()
    
    # Load tool names dynamically from JSON
    specific_tools = _load_tool_names()
    
    # Check if query contains any specific tool keywords
    has_specific_tool = any(
        tool_keyword in query_lower 
        for tool_keyword in specific_tools
    )
    
    # Generic terms detection
    generic_terms = ['tool', 'machine', 'device', 'equipment']
    has_generic_term = any(term in query_lower for term in generic_terms)
    
    # If vague without specific tool and no filters → clarify
    if (has_generic_term or len(query.split()) < 2) 
        and not has_specific_tool 
        and not filters:
        return True
```

**Demo Flow:**
- **Input:** "tool" → **Output:** Clarification with categories
- **Input:** "nutrunner" → **Output:** Direct results (specific tool)

---

## Slide 7: Challenge 2 - Metadata Filtering 🎯

**The Problem:**
- User asks: **"18V cordless nutrunner"**
- Database has: **"18V DC"** (exact string match fails)
- Semantic search alone: Might return 230V tool

**The Solution: Hybrid Search**

**Step 1: Extract Filters**
```python
def extract_filters(query: str) -> Dict[str, Any]:
    filters = {}
    
    # Extract voltage (e.g., "18V", "230V")
    voltage_match = re.search(r'(\d+\s?V)', query, re.IGNORECASE)
    if voltage_match:
        filters['voltage'] = voltage_match.group().replace(" ", "").upper()
    
    # Extract torque (e.g., "50Nm")
    torque_match = re.search(r'(\d+)\s*Nm', query, re.IGNORECASE)
    if torque_match:
        filters['torque'] = int(torque_match.group(1))
    
    # Extract IP rating
    ip_match = re.search(r'(IP\d+)', query, re.IGNORECASE)
    if ip_match:
        filters['ip_rating'] = ip_match.group().upper()
```

**Step 2: Apply Partial Matching**
```python
def apply_metadata_filters(tools: list, filters: Dict) -> list:
    # Partial match for voltage: "18V" matches "18V DC"
    if 'voltage' in filters:
        filtered_tools = [
            tool for tool in filtered_tools 
            if filters['voltage'] in tool.get('voltage', '').upper()
        ]
    return filtered_tools
```

**Result:** Finds "Cordless nutrunner" with "18V DC" voltage ✓

---

## Slide 8: Challenge 3 - Session Memory 💬

**The Problem:**
Multi-turn conversations lose context

```
User: "nutrunner"           → System shows clarification options
User: "18V"                 → System forgets "nutrunner" context ❌
```

**The Solution: Session-Based Context Management**

**Session Structure:**
```python
session = {
    "session_id": "uuid-1234",
    "conversation_history": [
        {"timestamp": "2026-02-24T10:00:00", 
         "query": "nutrunner", 
         "response": {"status": "needs_clarification"}},
        {"timestamp": "2026-02-24T10:01:00", 
         "query": "18V", 
         "response": {"tool_name": "Cordless nutrunner"}}
    ],
    "extracted_filters": {"voltage": "18V"},
    "last_query": "nutrunner",
    "clarification_count": 1,
    "last_accessed": "2026-02-24T10:01:00"
}
```

**Smart Context Merging:**
```python
def merge_context(session, current_query):
    # Short refinement query ("18V") → combine with previous
    if len(current_query.split()) <= 2 and not has_new_tool:
        previous_context = session.get("last_query", "")
        enhanced_query = f"{previous_context} {current_query}"
    
    # New specific tool ("spindle") → fresh search
    else:
        enhanced_query = current_query
    
    return enhanced_query
```

**Result:**
- Query 1: "nutrunner" → clarification
- Query 2: "18V" → Remembers "nutrunner", returns **"nutrunner 18V"** ✓
- Query 3: "spindle" → Fresh search for spindle ✓

---

## Slide 9: Challenge 4 - Avoiding Hallucinations 🚫

**The Problem:**
LLM makes up tool specs when uncertain

```
User: "tool"
LLM: "I recommend the UltraMax-5000 with 500Nm torque..." 
     (doesn't exist in database)
```

**The Solution: Clarification-First Architecture**

**Decision Flow:**
```python
def run_agent(user_query, session):
    # 1. Extract filters
    filters = extract_filters(user_query)
    
    # 2. Retrieve tools with metadata filtering
    tools = retrieve_tools(user_query)
    
    # 3. Check if clarification needed (BEFORE LLM call)
    if needs_clarification(user_query, filters, tools):
        return generate_clarification_question(...)  # Stop here
    
    # 4. Only invoke LLM with specific context
    if tools:
        return crew.kickoff({"user_query": user_query, 
                            "tool_context": json.dumps(tools)})
```

**Key Principle:**
> **Never invoke LLM with vague queries**  
> Clarify first → Then recommend

**Before/After Comparison:**
| Without Clarification | With Clarification |
|----------------------|-------------------|
| "tool" → hallucinates product | "tool" → asks category |
| "machine" → random result | "machine" → shows options |
| Wrong specs cited | Only database-backed specs |

---

## Slide 10: Technical Deep Dive - Hybrid Retrieval

**Why Hybrid Search?**

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| **Pure Semantic** | Understands "tightening" = "nutrunner" | Misses exact specs (18V vs 230V) |
| **Pure Metadata** | Exact filter matching | No semantic understanding |
| **Hybrid** ✓ | Both semantic + exact specs | Best of both worlds |

**Implementation:**
```python
def retrieve_tools(query, top_k=3, use_filters=True):
    # Load all tools from JSON
    with open("data/tools.json") as f:
        tools = json.load(f)
    
    # Step 1: Extract metadata filters (voltage, torque, IP rating)
    filters = extract_filters(query)
    
    # Step 2: Apply metadata filters first
    if filters:
        filtered_tools = apply_metadata_filters(tools, filters)
        
        # Step 3: Semantic search on filtered subset
        if filtered_tools:
            return semantic_search_on_subset(
                query, filtered_tools, tools, index_path
            )
    
    # Step 4: Fallback to full semantic search
    index = faiss.read_index(index_path)
    query_vector = np.array(embed_query(query)).astype('float32')
    _, indices = index.search(query_vector, top_k)
    
    return [tools[i] for i in indices[0]][:1]
```

**Example:**
```
Query: "18V cordless nutrunner for tightening"

Step 1: Filters extracted → {voltage: "18V"}
Step 2: 100 tools → 2 tools (only 18V tools)
Step 3: Semantic search on 2 tools → Top 1 match
Result: Cordless nutrunner (18V DC) ✓
```

---

## Slide 11: Technical Deep Dive - Dynamic Tool Recognition

**The Problem:**
Hardcoding tool names is unmaintainable

```python
# ❌ Bad approach
if "nutrunner" in query or "nut runner" in query:
    # What about new tools? Typos? Synonyms?
```

**The Solution: Dynamic Loading from JSON**

```python
def _load_tool_names() -> Set[str]:
    # Read tools.json
    with open("data/tools.json") as f:
        tools = json.load(f)
    
    tool_keywords = set()
    
    for tool in tools:
        # Add full tool name
        if tool.get('tool_name'):
            tool_keywords.add(tool['tool_name'].lower())
        
        # Extract keywords from tool names
        words = tool['tool_name'].lower().split()
        tool_keywords.update(words)
        
        # Add categories
        if tool.get('category'):
            cat_words = tool['category'].lower().split()
            tool_keywords.update(cat_words)
    
    # Remove generic terms
    common_words = {'the', 'a', 'tool', 'machine', 'device'}
    tool_keywords = {
        word for word in tool_keywords 
        if word not in common_words
    }
    
    return tool_keywords  # {"nutrunner", "cordless", "spindle", ...}
```

**Benefits:**
1. **Single source of truth:** Add to JSON → system auto-recognizes
2. **No code changes:** New tool? Just update JSON
3. **Maintainable:** One place to manage tool catalog
4. **Scalable:** Works for 100+ tools

**Example:**
```json
// Add to tools.json
{
  "tool_name": "Torque wrench",
  "category": "Assembly Tool",
  ...
}

// System automatically recognizes:
// - "torque"
// - "wrench"
// - "torque wrench"
// - "assembly"
```

---

## Slide 12: Live Demo 🎬

**Scenario 1: Vague to Specific**
```
👤 User: "tool"
🤖 System: "I can help you find tools in these categories:
          • Assembly Tool (nutrunner, spindle)
          • Control System (tightening controller)
          • Quality/Verification (torque tester)
          What type are you looking for?"

👤 User: "nutrunner"
🤖 System: "I found multiple nutrunners. What voltage?
          • 18V (cordless)
          • 230V (manual)
          • 400V (automation)"

👤 User: "18V"
🤖 System: "✓ Recommended: Cordless nutrunner (NX-CN100)
          • Voltage: 18V DC
          • Torque: 5–100 Nm
          • Application: Manual/Portable
          Why: Matches your 18V cordless requirement..."
```

**Scenario 2: Direct with Filters**
```
👤 User: "18V cordless nutrunner"
🤖 System: "✓ Recommended: Cordless nutrunner (NX-CN100)
          (No clarification needed - query is specific)"
```

**Scenario 3: Session Context**
```
👤 User: "automation tool"
🤖 System: "What voltage? 400V or 230V?"

👤 User: "400V"
🤖 System: "✓ Tightening spindle (NX-TS500) - 400V"

👤 User: "show manual version instead"
🤖 System: "✓ Hand-held nutrunner (NX-HH80) - 230V
          (Remembers 'tightening' context, switches to manual)"
```

**Scenario 4: Out of Domain**
```
👤 User: "1000Nm drill"
🤖 System: "No tools found for '1000Nm drill'. 
          Our max torque: 500 Nm (Tightening spindle)
          Would you like to see high-torque options?"
```

---

## Slide 13: Lessons Learned & Best Practices

**✅ What Worked:**

1. **Clarification-First Approach**
   - Prevents hallucinations at the root
   - User trust increases when system admits uncertainty

2. **Hybrid Search > Pure Semantic**
   - Metadata filtering crucial for industrial specs
   - Semantic alone: 60% accuracy → Hybrid: 95% accuracy

3. **Session Management**
   - Natural conversations require context
   - 30-minute timeout balances UX and memory

4. **Dynamic Tool Loading**
   - Single source of truth (JSON)
   - Add tool → No code changes needed

**⚠️ Challenges Faced:**

1. **Proxy/Network Issues**
   - OpenAI API timeouts in corporate environments
   - Solution: `httpx_client = httpx.Client(proxy=None)`

2. **Data Quality**
   - Typos in JSON: "nutrunnner" vs "nutrunner"
   - Solution: Data validation scripts

3. **Vector Store Synchronization**
   - JSON updated → FAISS index stale
   - Solution: Auto-rebuild script on JSON changes

4. **Session Memory Trade-offs**
   - When to reset context? (new tool vs refinement)
   - Solution: Detect new specific tool names

**🎓 Key Takeaways:**
- Start with clarification logic before scaling
- Hybrid approach beats pure semantic/metadata
- Session management = 10x better UX
- Data quality matters more than fancy models

---

## Slide 14: Future Improvements 🚀

**Phase 1: Enhanced Recommendations**
- **Multi-tool comparison:** "Compare nutrunner vs spindle for 18V"
- **Price filtering:** "Show tools under $5000"
- **Availability checking:** Real-time stock integration

**Phase 2: Advanced Features**
- **Export to PDF/Quote:** Generate datasheets
- **Voice interface:** Hands-free for factory floor
- **Image recognition:** "Tool that looks like this"

**Phase 3: Enterprise Scalability**
- **Multi-language support:** Translation layer
- **Analytics dashboard:** Top queries, conversion rates
- **Integration:** ERP/CRM systems

**Phase 4: Model Improvements**
- **Fine-tuned embeddings:** Domain-specific training
- **Caching layer:** Frequently asked queries
- **A/B testing:** Optimize clarification strategies

**Scalability Considerations:**
- Current: 100 tools, FAISS in-memory
- Future: 10,000+ tools → Pinecone/Weaviate
- Current: In-memory sessions → Redis/database
- Future: Multi-tenant support

---

## Slide 15: Architecture Best Practices

**Design Principles We Followed:**

1. **Separation of Concerns**
   ```
   query_parser.py    → Filter extraction
   clarification.py   → Clarification logic
   retriever.py       → Vector search
   crew_setup.py      → LLM orchestration
   session_manager.py → Context management
   ```

2. **Fail-Safe Mechanisms**
   - Clarification before LLM invocation
   - Graceful degradation (no results → suggest alternatives)
   - Timeout handling (API failures)

3. **Maintainability**
   - Dynamic tool loading (JSON → code)
   - Single source of truth
   - Configuration via environment variables

4. **Performance Optimization**
   - Caching tool names (avoid repeated file reads)
   - Metadata filtering before semantic search
   - Top-K limiting (only return 1 result)

---

## Slide 16: Performance Metrics

**Current System Performance:**

| Metric | Value | Notes |
|--------|-------|-------|
| **Average Response Time** | 2-3 sec | Embedding + LLM generation |
| **Accuracy** | 95%+ | With clarification system |
| **Clarification Rate** | 30% | Prevents hallucinations |
| **Session Retention** | 30 min | Auto-cleanup expired sessions |
| **Tools Supported** | 100+ | FAISS scales to millions |
| **Concurrent Users** | 50+ | FastAPI async handling |

**Latency Breakdown:**
```
Total: 2.5 seconds
├─ Query embedding:      0.3s (OpenAI API)
├─ FAISS search:         0.1s (local, fast)
├─ Filter application:   0.05s
├─ Clarification check:  0.05s
└─ LLM generation:       2.0s (OpenAI GPT-4o-mini)
```

**Optimization Opportunities:**
- Cache embeddings for common queries → 0.3s saved
- Batch processing → 2x throughput
- Local LLM → No API latency

---

## Slide 17: Q&A Preparation

**Expected Technical Questions:**

**Q: Why FAISS instead of Pinecone/Weaviate?**  
A: Simplicity for 100 tools. FAISS is fast, local, no infrastructure cost. Scale up later if needed.

**Q: Why CrewAI instead of LangChain?**  
A: CrewAI's agent abstraction fits our use case. Easy role-based prompts, cleaner code.

**Q: How do you handle typos?**  
A: Semantic embeddings handle minor typos. For data quality, we have validation scripts.

**Q: What about multi-language support?**  
A: Currently English only. Can extend with translation layer before query processing.

**Q: Data privacy concerns?**  
A: Session data in-memory (30 min timeout). No PII stored. OpenAI API for embeddings only.

**Q: How many tools can it handle?**  
A: Current: 100 tools. FAISS scales to millions. Bottleneck is LLM context window (~8K tokens).

**Q: What if FAISS index is outdated?**  
A: Manual rebuild currently. Future: Auto-detect JSON changes and rebuild index.

**Q: Cost per query?**  
A: ~$0.001 (embedding) + ~$0.002 (LLM) = ~$0.003 per query. Scales well.

---

## Slide 18: System Demo - Behind the Scenes

**What Happens When User Types: "18V tool for tightening"**

```
Step 1: FastAPI receives query
POST /chat
{
  "question": "18V tool for tightening",
  "session_id": "abc-123"
}

Step 2: Session Manager retrieves context
session = {
  "conversation_history": [...],
  "extracted_filters": {},  # Empty for new conversation
  "last_query": ""
}

Step 3: Query Parser extracts filters
extract_filters("18V tool for tightening")
→ {voltage: "18V"}

Step 4: Semantic Search with Filters
• Embed query → [0.123, -0.456, ...]
• Filter tools by voltage → 2 tools (18V)
• FAISS search on 2 tools → Top 1 match

Step 5: Clarification Check
needs_clarification(...) → False (specific tool + filter)

Step 6: LLM Agent Generates Recommendation
PROMPT:
"User Query: 18V tool for tightening
 Available Tools: [Cordless nutrunner (18V DC, 5-100 Nm)]
 Recommend the best tool..."

Response: {
  "tool_name": "Cordless nutrunner",
  "model": "NX-CN100",
  "why_recommended": "Matches 18V requirement...",
  "key_specs": ["18V DC", "5-100 Nm", "Cordless"],
  ...
}

Step 7: Update Session
session["conversation_history"].append(...)
session["extracted_filters"] = {voltage: "18V"}
session["last_query"] = "18V tool for tightening"

Step 8: Return to User
{
  "response": {...},
  "session_id": "abc-123"
}
```

---

## Slide 19: Code Repository & Resources

**GitHub Repository:**
```
product_intelligence_system/
├── backend/
│   ├── main.py                 # FastAPI endpoints
│   ├── crew_setup.py           # CrewAI agent
│   ├── clarification.py        # Clarification logic
│   ├── query_parser.py         # Filter extraction
│   ├── session_manager.py      # Session handling
│   ├── agents/
│   │   ├── retriever.py        # FAISS search
│   │   └── embeddings.py       # OpenAI embeddings
│   ├── data/
│   │   └── tools.json          # Tool database
│   └── vector_store/
│       └── tools.index         # FAISS index
├── frontend/
│   └── app.py                  # Streamlit UI
├── requirements.txt
└── README.md
```

**Key Technologies:**
- FastAPI: https://fastapi.tiangolo.com
- CrewAI: https://crewai.com
- FAISS: https://github.com/facebookresearch/faiss
- OpenAI: https://platform.openai.com

**Try It Yourself:**
```bash
# Setup
git clone <repo>
pip install -r requirements.txt

# Backend
uvicorn backend.main:app --reload

# Frontend
streamlit run frontend/app.py
```

---

## Slide 20: Closing & Call to Action

**Key Takeaways:**

1. **RAG alone isn't enough** → Add clarification logic
2. **Hybrid search > Pure semantic** → Metadata matters
3. **Session memory** → Natural conversations
4. **Design for maintainability** → Dynamic loading, separation of concerns
5. **User trust** → Admit uncertainty rather than hallucinate

**Impact:**
- **95% accuracy** (vs 60% pure semantic)
- **2-3 second response time**
- **30% clarification rate** prevents errors
- **Scalable to 100+ tools** (and beyond)

**What's Next?**
- Try the demo: [Live URL]
- Explore code: [GitHub link]
- Questions? Let's connect: [Email/LinkedIn]

**Thank You! 🎤**

---

## Slide 21: Bonus - Architecture Comparison

**Before vs After:**

| Aspect | Traditional Chatbot | Our System |
|--------|-------------------|------------|
| **Search** | Keyword matching | Hybrid (semantic + metadata) |
| **Vague Queries** | Returns anything | Clarifies first |
| **Context** | Stateless | Session-based memory |
| **Accuracy** | 60% | 95%+ |
| **Hallucinations** | Common | Prevented by clarification |
| **Scalability** | Limited | 100+ tools, easily expandable |
| **Maintenance** | Hardcoded rules | Dynamic from JSON |

**ROI:**
- **Time saved:** 5 min → 2 sec per query
- **Accuracy gain:** 35% improvement
- **Reduced sales dependency:** Self-service enabled
- **User satisfaction:** Higher trust with clarification

---

## Presentation Tips:

1. **Start with live demo** - Show the problem/solution immediately
2. **Use animations** - Reveal architecture diagram step-by-step
3. **Live coding moment** - Show clarification logic (5 lines)
4. **Interactive poll** - "What would YOU search for?"
5. **Failure cases** - Show bad query handling (builds trust)
6. **Time management:**
   - Intro: 5 min
   - Architecture: 8 min
   - Challenges: 20 min (5 min each)
   - Demo: 8 min
   - Lessons: 4 min
   - Q&A: Remaining time

Good luck with your tech talk! 🚀
