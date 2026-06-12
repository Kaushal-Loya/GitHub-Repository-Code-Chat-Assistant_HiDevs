# Implementation Plan
## GitHub Repository Code Chat Assistant

**Version:** 1.0  
**Date:** June 11, 2026  
**Based on:** PRD v1.0  
**Status:** Ready for Execution

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Project Structure](#2-project-structure)
3. [Tech Stack & Dependencies](#3-tech-stack--dependencies)
4. [Phase-by-Phase Implementation](#4-phase-by-phase-implementation)
5. [File-by-File Breakdown](#5-file-by-file-breakdown)
6. [Data Flow & Architecture](#6-data-flow--architecture)
7. [Environment Setup](#7-environment-setup)
8. [Testing Strategy](#8-testing-strategy)
9. [Risks & Mitigations](#9-risks--mitigations)
10. [Milestones Checklist](#10-milestones-checklist)

---

## 1. Project Overview

The **GitHub Repository Code Chat Assistant** is a RAG (Retrieval-Augmented Generation) pipeline that enables developers to have a conversational interface with any GitHub repository. It combines:

- **GitHub API** for code ingestion
- **LangChain** for pipeline orchestration, chunking, and prompt management
- **HuggingFace sentence-transformers** for embeddings
- **ChromaDB / FAISS** as the vector store
- **Groq + LLaMA 3** as the LLM backend
- **MongoDB** for multi-turn conversation memory
- **Streamlit** as the interactive UI

---

## 2. Project Structure

```
GitHub-Repository-Code-Chat-Assistant_HiDevs/
│
├── app.py                        # Streamlit app entry point
├── requirements.txt              # All Python dependencies
├── .env.example                  # Environment variable template
├── .gitignore
├── README.md
├── PRD_GitHub_Code_Chat_Assistant.md
├── IMPLEMENTATION_PLAN.md        # This file
│
├── src/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── github_loader.py      # GitHub API client + LangChain loaders
│   │   └── preprocessor.py       # File filtering, normalization, dedup
│   │
│   ├── chunking/
│   │   ├── __init__.py
│   │   └── splitter.py           # Code, Markdown, and Recursive splitters
│   │
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── embedder.py           # HuggingFace embedding wrapper
│   │
│   ├── vector_store/
│   │   ├── __init__.py
│   │   └── store.py              # ChromaDB + FAISS abstraction layer
│   │
│   ├── query_engine/
│   │   ├── __init__.py
│   │   ├── retriever.py          # Vector similarity retrieval (top-K)
│   │   ├── prompt_builder.py     # LangChain ChatPromptTemplate construction
│   │   └── llm_chain.py          # Groq + LLaMA 3 chain with memory
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   └── mongo_memory.py       # MongoDB conversation memory integration
│   │
│   └── utils/
│       ├── __init__.py
│       ├── github_utils.py       # GitHub URL parsing, metadata helpers
│       └── rate_limiter.py       # GitHub API rate limit handling + backoff
│
├── ui/
│   ├── components.py             # Reusable Streamlit UI components
│   └── styles.css                # Custom CSS for Streamlit theming
│
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_chunking.py
│   ├── test_embeddings.py
│   ├── test_retrieval.py
│   └── test_llm_chain.py
│
├── evaluation/
│   ├── benchmark_queries.json    # 20 labelled queries for RAG evaluation
│   └── evaluate_rag.py           # LangChain Eval + optional DeepEval runner
│
└── docs/
    ├── architecture.md
    └── setup_guide.md
```

---

## 3. Tech Stack & Dependencies

### Core Dependencies (`requirements.txt`)

```
# GitHub & Web Ingestion
PyGithub>=2.1.1
requests>=2.31.0

# LangChain Ecosystem
langchain>=0.2.0
langchain-community>=0.2.0
langchain-core>=0.2.0
langchain-groq>=0.1.0
langchain-huggingface>=0.0.3

# Embedding Model
sentence-transformers>=2.7.0
torch>=2.0.0

# Vector Stores
chromadb>=0.5.0
faiss-cpu>=1.8.0

# LLM Backend
groq>=0.9.0

# Memory / Database
pymongo>=4.6.0
motor>=3.3.0

# UI
streamlit>=1.35.0

# Evaluation (optional)
deepeval>=0.21.0

# Utilities
python-dotenv>=1.0.0
tqdm>=4.66.0
tenacity>=8.2.0       # Retry logic / exponential backoff
```

### Environment Variables (`.env.example`)

```env
# GitHub
GITHUB_TOKEN=your_github_personal_access_token

# Groq
GROQ_API_KEY=your_groq_api_key

# MongoDB
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/
MONGODB_DB_NAME=github_chat_assistant

# ChromaDB (optional: for persistent local storage path)
CHROMA_PERSIST_DIR=./chroma_db

# App Settings
TOP_K_RETRIEVAL=5
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

---

## 4. Phase-by-Phase Implementation

---

### Phase 1 — GitHub Ingestion + Chunking Pipeline (Week 1–2)

**Goal:** Ingest a GitHub repository's source files and split them into semantically meaningful chunks.

#### Step 1.1 — GitHub API Client (`src/ingestion/github_loader.py`)

- Authenticate using a GitHub PAT (Personal Access Token) via `PyGithub`
- Accept both public repo URLs and private repos (with token)
- Recursively fetch all files from a given repository:
  - Filter by supported extensions: `.py`, `.js`, `.ts`, `.java`, `.go`, `.cpp`, `.md`, `.json`, `.yaml`
  - Skip binary files, lock files (`package-lock.json`, `yarn.lock`, `*.lock`), and build artifacts (`dist/`, `build/`, `node_modules/`, `__pycache__/`)
- Collect file metadata: file path, language, size, last modified commit SHA
- Return a list of `Document` objects (LangChain format) with `page_content` and `metadata`
- Implement rate limiting handler via `tenacity` (exponential backoff on HTTP 403/429)

```python
# Key interface
def load_repository(repo_url: str, token: str | None = None) -> list[Document]:
    """Fetches all relevant source files from a GitHub repository."""
```

#### Step 1.2 — Preprocessor (`src/ingestion/preprocessor.py`)

- Strip binary or non-UTF-8 files
- Normalize whitespace (collapse multiple blank lines, fix encoding)
- Deduplicate: hash file content; skip files whose content hash already exists in the batch
- Remove boilerplate (license headers) by detecting standard patterns
- Enrich metadata: extract language from extension, author from git log (if available via commit API)

#### Step 1.3 — Code Chunker (`src/chunking/splitter.py`)

| File Type | Splitter Used | Configuration |
|---|---|---|
| `.py`, `.js`, `.ts`, `.java`, `.go`, `.cpp` | `LangChain CodeTextSplitter` | Chunk=512 tokens, Overlap=50 |
| `.md`, `.rst` | `MarkdownHeaderTextSplitter` | Split on H1, H2, H3 |
| All others (`.json`, `.yaml`, plain text) | `RecursiveCharacterTextSplitter` | Chunk=512 tokens, Overlap=50 |

- Preserve metadata per chunk: `file_path`, `language`, `start_line`, `end_line`, `parent_class`, `parent_function`
- Return list of enriched `Document` chunks ready for embedding

```python
# Key interface
def split_documents(documents: list[Document]) -> list[Document]:
    """Routes each document to the appropriate splitter and returns chunks."""
```

**Phase 1 Deliverable:** A function `ingest_and_chunk(repo_url, token)` that returns a list of annotated `Document` chunks.

---

### Phase 2 — Embedding Generation + ChromaDB Knowledge Base (Week 2–3)

**Goal:** Convert chunks to vector embeddings and store them in a queryable vector database.

#### Step 2.1 — Embedding Model (`src/embeddings/embedder.py`)

- Use `sentence-transformers/all-MiniLM-L6-v2` via HuggingFace
- Wrap in `HuggingFaceEmbeddings` from `langchain-huggingface`
- Singleton pattern: load model once per session to avoid repeated disk I/O

```python
from langchain_huggingface import HuggingFaceEmbeddings

def get_embedder() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
```

#### Step 2.2 — Vector Store (`src/vector_store/store.py`)

- **Primary:** ChromaDB with persistent local storage
  - Collection name = sanitized repository name + commit SHA (for repo-scoped isolation)
  - Store chunks with full metadata for filtered retrieval
- **Fallback:** FAISS in-memory store if ChromaDB is unavailable
- **Incremental update logic:**
  - On re-ingestion, fetch new commit SHA from GitHub
  - If SHA matches stored collection SHA → skip re-embedding
  - If SHA differs → delete old collection, re-embed and store fresh

```python
# Key interface
def build_vector_store(chunks: list[Document], embedder, repo_name: str) -> VectorStore:
    """Builds or updates the ChromaDB collection for the given repo."""

def load_vector_store(repo_name: str, embedder) -> VectorStore | None:
    """Loads an existing ChromaDB collection if present."""
```

**Phase 2 Deliverable:** A persisted, queryable vector knowledge base for any ingested repository.

---

### Phase 3 — Query Engine + LLM Integration (Week 3–4)

**Goal:** Accept natural-language queries, retrieve relevant code chunks, and generate LLM responses.

#### Step 3.1 — Retriever (`src/query_engine/retriever.py`)

- Embed the user query using the same HuggingFace model (semantic parity)
- Query ChromaDB using cosine similarity with `top_k=5` (configurable)
- Support metadata-filtered retrieval (e.g., restrict to `.py` files only)
- Return retrieved chunks with their source metadata (file, lines)

#### Step 3.2 — Prompt Builder (`src/query_engine/prompt_builder.py`)

Construct a structured `ChatPromptTemplate` with three sections:

```
[System Message]
You are an expert code assistant with deep knowledge of software engineering.
You have been given the following repository context: {repo_summary}.
Always cite the file path and line numbers when referencing specific code.
Answer based ONLY on the provided context. If you cannot answer from context, say so.

[Retrieved Context]
--- File: {file_path} (Lines {start}–{end}) ---
{chunk_content}
... (repeated for each of top-K chunks)

[Conversation History]
{history}

[Human Message]
{user_query}
```

#### Step 3.3 — LLM Chain (`src/query_engine/llm_chain.py`)

- Initialize Groq client with `llama3-8b-8192` (fast) or `llama3-70b-8192` (higher quality, fallback)
- Integrate with `ConversationBufferWindowMemory` from LangChain (window of last 10 turns)
- Full chain: `retriever → prompt_builder → Groq LLM → response parser`
- Return: structured object `{ answer: str, sources: list[SourceCitation] }`

```python
# SourceCitation dataclass
@dataclass
class SourceCitation:
    file_path: str
    start_line: int
    end_line: int
    language: str
    snippet: str
```

**Phase 3 Deliverable:** A working `chat(query, session_id)` function that returns answers with citations.

---

### Phase 4 — Streamlit UI + MongoDB Memory (Week 4–5)

**Goal:** Build the complete interactive front-end and wire in persistent session memory.

#### Step 4.1 — MongoDB Memory (`src/memory/mongo_memory.py`)

- Use `MongoDBChatMessageHistory` from `langchain-community`
- Session ID = hash of `(user_session + repo_url)`
- Store: user messages, AI messages, timestamps
- On session start: load prior history if session ID exists
- Implement `clear_history(session_id)` for the UI "Clear Chat" button

#### Step 4.2 — Streamlit App (`app.py`)

**Layout — Three-section design:**

```
┌─────────────────────────────────────────────────┐
│  🔍  GitHub Repository Code Chat Assistant       │
├────────────┬────────────────────────────────────┤
│  SIDEBAR   │         MAIN CHAT AREA             │
│            │                                    │
│ [Repo URL] │  [Chat Message History]            │
│ [Token]    │                                    │
│ [Ingest]   │  [User Input Box]  [Send]          │
│            │                                    │
│ Repo Info: ├────────────────────────────────────┤
│  • Language│         SOURCES PANEL              │
│  • Files   │  File: src/utils.py (L12–45)       │
│  • Updated │  File: src/models.py (L88–102)     │
│            │                                    │
│ [Clear]    │                                    │
└────────────┴────────────────────────────────────┘
```

**Key Streamlit Components (`ui/components.py`):**

| Component | Description |
|---|---|
| `render_repo_sidebar()` | URL input, token field, Ingest button, repo overview card |
| `render_chat_message(role, content)` | Styled message bubbles with syntax-highlighted code blocks |
| `render_sources_panel(citations)` | Collapsible panel showing file path + line range per source |
| `render_ingestion_progress(files, chunks, status)` | `st.progress` bar + status text |

**Session State Keys:**

```python
st.session_state = {
    "repo_url": str,
    "repo_name": str,
    "vector_store": VectorStore,
    "conversation_history": list[dict],
    "session_id": str,
    "ingestion_complete": bool,
    "repo_metadata": dict,    # file count, languages, last updated
}
```

**Phase 4 Deliverable:** Fully functional Streamlit app with persistent chat memory.

---

### Phase 5 — Testing, Evaluation & Latency Optimization (Week 5–6)

**Goal:** Validate the pipeline end-to-end, measure performance, and tune for <2s response time.

#### Step 5.1 — Unit Tests (`tests/`)

| Test File | Coverage |
|---|---|
| `test_ingestion.py` | GitHub API connectivity, file filtering, metadata extraction |
| `test_chunking.py` | Correct chunk boundaries, metadata propagation per language |
| `test_embeddings.py` | Embedding shape, cosine similarity floor on related snippets |
| `test_retrieval.py` | Top-K retrieval, metadata filtering, cosine similarity ≥ 0.75 |
| `test_llm_chain.py` | Prompt construction, citation presence, hallucination check |

#### Step 5.2 — RAG Evaluation (`evaluation/evaluate_rag.py`)

- 20 benchmark query-answer pairs in `benchmark_queries.json` across 2 test repos
- Metrics via `LangChain Evaluation`:
  - **Relevance**: Is the answer grounded in the retrieved context?
  - **Faithfulness**: Does the answer contradict the source code?
  - **Completeness**: Does the answer address all aspects of the query?
- Optional: **DeepEval** for automated retrieval precision/recall

#### Step 5.3 — Latency Optimization

| Bottleneck | Mitigation Strategy |
|---|---|
| Embedding model cold start | Load model once on app startup; cache in `st.cache_resource` |
| ChromaDB query latency | Reduce top-K from 5 to 3 if latency > 1.5s |
| Groq LLM latency | Use `llama3-8b-8192` (faster) over `llama3-70b-8192` by default |
| Re-ingestion on page reload | Cache vector store in `st.session_state`; only re-ingest on explicit button press |

**Phase 5 Deliverable:** Test report + latency profile confirming <2s p95 response time.

---

### Phase 6 — Deployment & Documentation (Week 6)

**Goal:** Deploy to a cloud platform and finalize documentation.

#### Step 6.1 — Deployment Options

| Platform | Notes |
|---|---|
| **Streamlit Community Cloud** | Free; direct GitHub integration; ideal for demo |
| **Hugging Face Spaces** | Supports Streamlit apps; free tier; good for ML-focused audience |
| **Railway / Render** | If MongoDB + persistent storage needed beyond session |

#### Step 6.2 — Documentation

- `README.md`: Project overview, setup instructions, demo GIF, environment variable guide
- `docs/architecture.md`: System diagram + data flow explanation
- `docs/setup_guide.md`: Step-by-step local dev + cloud deployment guide

---

## 5. File-by-File Breakdown

### `src/ingestion/github_loader.py`

```python
"""
Responsibilities:
- Authenticate to GitHub API via PyGithub
- Recursively list and download repository files
- Filter supported file types; skip binary/auto-generated files
- Return list of LangChain Document objects with metadata
- Handle rate limits with tenacity exponential backoff
"""
```

### `src/ingestion/preprocessor.py`

```python
"""
Responsibilities:
- Normalize file content (encoding, whitespace)
- Deduplicate by content hash
- Remove boilerplate patterns (license headers)
- Enrich metadata (language, author from commit history)
"""
```

### `src/chunking/splitter.py`

```python
"""
Responsibilities:
- Route documents to CodeTextSplitter, MarkdownHeaderSplitter, or RecursiveCharacterTextSplitter
- Preserve and enrich chunk metadata (start_line, end_line, parent_class, parent_function)
- Target chunk_size=512 tokens, chunk_overlap=50
"""
```

### `src/embeddings/embedder.py`

```python
"""
Responsibilities:
- Initialize sentence-transformers/all-MiniLM-L6-v2 via HuggingFaceEmbeddings
- Singleton/cached instantiation to avoid repeated loading
"""
```

### `src/vector_store/store.py`

```python
"""
Responsibilities:
- Build ChromaDB collection per repository (repo_name + commit_SHA as collection key)
- FAISS fallback if ChromaDB fails
- Incremental update: detect SHA change, rebuild only on delta
- Expose similarity search with optional metadata filters
"""
```

### `src/query_engine/retriever.py`

```python
"""
Responsibilities:
- Embed user query with same HuggingFace model
- Execute cosine similarity search in vector store (top-K=5)
- Return ranked list of Document chunks with scores and metadata
"""
```

### `src/query_engine/prompt_builder.py`

```python
"""
Responsibilities:
- Construct LangChain ChatPromptTemplate with system, context, history, and human slots
- Format retrieved chunks into readable context blocks with file path + line annotations
"""
```

### `src/query_engine/llm_chain.py`

```python
"""
Responsibilities:
- Initialize Groq LLM (llama3-8b-8192 default)
- Compose full RAG chain: retriever → prompt → LLM → output parser
- Integrate LangChain conversation window memory
- Return structured response with answer + SourceCitation list
"""
```

### `src/memory/mongo_memory.py`

```python
"""
Responsibilities:
- Connect to MongoDB Atlas (or local) via pymongo
- Wrap MongoDBChatMessageHistory for LangChain compatibility
- Create/load sessions by session_id
- Expose clear_history() for UI reset
"""
```

### `app.py`

```python
"""
Responsibilities:
- Streamlit app entry point
- Manage st.session_state for repo, vector store, chat history, session_id
- Render sidebar (repo config + ingestion control)
- Render chat interface (history, input, send)
- Render sources panel per response
- Call ingestion pipeline + chat engine
"""
```

---

## 6. Data Flow & Architecture

```
┌─────────────────────────── INGESTION PIPELINE ──────────────────────────────┐
│                                                                              │
│  GitHub Repo URL                                                             │
│       │                                                                      │
│       ▼                                                                      │
│  [github_loader.py] ──── PyGithub API ──── Rate Limiter                     │
│       │                                                                      │
│       ▼  list[Document] (raw files + metadata)                               │
│  [preprocessor.py] ──── Filter · Normalize · Dedup · Enrich                 │
│       │                                                                      │
│       ▼  list[Document] (clean files)                                        │
│  [splitter.py] ──── CodeSplitter / MarkdownSplitter / RecursiveSplitter      │
│       │                                                                      │
│       ▼  list[Document] (chunks with metadata)                               │
│  [embedder.py] ──── sentence-transformers/all-MiniLM-L6-v2                  │
│       │                                                                      │
│       ▼  list[float[]] (embedding vectors)                                   │
│  [store.py] ──── ChromaDB (primary) / FAISS (fallback)                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────── QUERY PIPELINE ──────────────────────────────────┐
│                                                                              │
│  User Query (natural language)                                               │
│       │                                                                      │
│       ▼                                                                      │
│  [retriever.py] ──── Embed query ──── Cosine similarity search (top-K=5)    │
│       │                                                                      │
│       ▼  list[Document] (top-K relevant chunks)                              │
│  [prompt_builder.py] ──── ChatPromptTemplate + History + Context             │
│       │                                                                      │
│       ▼  Formatted prompt                                                    │
│  [llm_chain.py] ──── Groq API (LLaMA 3) ──── MongoDB Memory                 │
│       │                                                                      │
│       ▼  { answer: str, sources: list[SourceCitation] }                     │
│  [app.py / Streamlit UI] ──── Render response + citations                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Environment Setup

### Prerequisites

- Python 3.11+
- Git
- MongoDB Atlas account (free tier) or local MongoDB instance
- Groq API key (free at [console.groq.com](https://console.groq.com))
- GitHub Personal Access Token (for private repos or higher rate limits)

### Local Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/GitHub-Repository-Code-Chat-Assistant_HiDevs.git
cd GitHub-Repository-Code-Chat-Assistant_HiDevs

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env
# Fill in GITHUB_TOKEN, GROQ_API_KEY, MONGODB_URI in .env

# 5. Run the Streamlit app
streamlit run app.py
```

---

## 8. Testing Strategy

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

### RAG Evaluation

```bash
# Run benchmark evaluation (requires .env configured)
python evaluation/evaluate_rag.py --repo https://github.com/sample/repo
```

### Performance Benchmark

```bash
# Measure p95 latency across 50 queries
python evaluation/benchmark_latency.py
```

### Target Metrics

| Metric | Target |
|---|---|
| p95 query response latency | < 2 seconds |
| Top-1 chunk cosine similarity | ≥ 0.75 |
| Hallucination rate | < 10% of responses |
| User satisfaction (helpful/very helpful) | > 80% |
| Successful ingestion (up to 500 files) | 100% success rate |

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Implementation Mitigation |
|---|---|---|---|
| GitHub API rate limiting on large repos | Medium | High | Use `tenacity` with exponential backoff; cache ingestion by commit SHA; prefer authenticated requests |
| LLM response latency > 2s | Medium | High | Default to `llama3-8b-8192`; tune top-K; use `st.cache_resource` for embedder; stream responses |
| Embedding model not capturing code semantics | Low | Medium | Benchmark `all-MiniLM-L6-v2` vs `CodeBERT`; abstracted embedder interface allows easy swap |
| ChromaDB instability | Low | Medium | FAISS fallback in `store.py`; document both paths in `docs/setup_guide.md` |
| Private repo code exposure | Medium | High | Session-only storage by default; data handling notice in UI sidebar; no logging of file content |

---

## 10. Milestones Checklist

### Phase 1 — Ingestion + Chunking (Week 1–2)
- [ ] `src/ingestion/github_loader.py` — GitHub API client with rate limiter
- [ ] `src/ingestion/preprocessor.py` — File filtering, normalization, dedup
- [ ] `src/chunking/splitter.py` — Multi-strategy code + text splitter
- [ ] `src/utils/rate_limiter.py` — Tenacity-based backoff
- [ ] `src/utils/github_utils.py` — URL parser, metadata helpers
- [ ] Verify: ingest a sample repo (e.g., `langchain-ai/langchain`) and print chunk count

### Phase 2 — Embeddings + Vector Store (Week 2–3)
- [ ] `src/embeddings/embedder.py` — HuggingFace embedding wrapper
- [ ] `src/vector_store/store.py` — ChromaDB primary + FAISS fallback
- [ ] Incremental update logic (commit SHA delta detection)
- [ ] Verify: cosine similarity ≥ 0.75 for top-1 on 5 manual test queries

### Phase 3 — Query Engine + LLM (Week 3–4)
- [ ] `src/query_engine/retriever.py` — Top-K retrieval with metadata filter
- [ ] `src/query_engine/prompt_builder.py` — ChatPromptTemplate with system + context
- [ ] `src/query_engine/llm_chain.py` — Groq + LLaMA 3 chain with window memory
- [ ] `SourceCitation` dataclass defined and returned per response
- [ ] Verify: ask 5 diverse questions; check answers cite correct files

### Phase 4 — Streamlit UI + MongoDB (Week 4–5)
- [ ] `src/memory/mongo_memory.py` — MongoDB session memory
- [ ] `ui/components.py` — Reusable Streamlit components
- [ ] `app.py` — Full Streamlit app with sidebar, chat, sources panel
- [ ] Session state management fully implemented
- [ ] Code blocks render with syntax highlighting
- [ ] "Clear Chat" resets MongoDB history and UI state

### Phase 5 — Testing & Optimization (Week 5–6)
- [ ] `tests/test_ingestion.py` — Unit tests passing
- [ ] `tests/test_chunking.py` — Unit tests passing
- [ ] `tests/test_embeddings.py` — Unit tests passing
- [ ] `tests/test_retrieval.py` — Unit tests passing
- [ ] `tests/test_llm_chain.py` — Unit tests passing
- [ ] `evaluation/benchmark_queries.json` — 20 labelled queries created
- [ ] `evaluation/evaluate_rag.py` — LangChain Eval metrics computed
- [ ] p95 latency confirmed < 2 seconds

### Phase 6 — Deployment & Docs (Week 6)
- [ ] `.env.example` committed (no secrets)
- [ ] `README.md` updated with setup guide + demo
- [ ] `docs/architecture.md` finalized
- [ ] `docs/setup_guide.md` written
- [ ] Deployed to Streamlit Community Cloud (or HuggingFace Spaces)
- [ ] Public URL shared and tested end-to-end

---

*Implementation Plan prepared for HiDevs Cohort — GitHub Repository Code Chat Assistant project.*
