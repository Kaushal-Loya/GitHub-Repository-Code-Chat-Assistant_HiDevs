# Product Requirements Document
## GitHub Repository Code Chat Assistant

**Version:** 1.0  
**Date:** June 11, 2026  
**Industry:** Software Development  
**Status:** Draft

---

## 1. Overview

### 1.1 Product Summary

The GitHub Repository Code Chat Assistant is an AI-powered tool that enables developers to interact conversationally with any GitHub repository. By combining GitHub API integration, semantic code search via vector embeddings, and a Large Language Model (LLM), it delivers real-time code explanations, targeted improvement suggestions, and collaborative insights — all within a seamless chat interface.

### 1.2 Problem Statement

Developers frequently struggle with:
- Understanding unfamiliar or legacy codebases quickly
- Navigating large repositories to find relevant logic
- Getting contextual, actionable improvement suggestions without switching tools
- Collaborating effectively during asynchronous code reviews

Existing tools (GitHub's own UI, static linters, manual PR reviews) lack conversational, AI-driven depth. This product bridges that gap.

### 1.3 Goals

- Reduce time-to-understanding for new or complex codebases
- Improve code quality through targeted, AI-generated suggestions
- Support developer collaboration with shared, queryable code context
- Deliver responses in under 2 seconds for repository analysis

---

## 2. Target Users

| User Persona | Description | Primary Need |
|---|---|---|
| New Developer | Onboarding to an existing repo | Understand structure, patterns, conventions |
| Code Reviewer | Reviewing PRs or evaluating third-party code | Quick context, issue spotting, improvement hints |
| Senior Engineer | Auditing architecture or refactoring | Deeper analysis, design pattern suggestions |
| Tech Lead | Evaluating open-source or vendor repos | High-level summaries and risk identification |

---

## 3. Functional Requirements

### 3.1 Data Ingestion (Step 1 — Data Sources)

- Connect to any public or private GitHub repository via GitHub API (OAuth or token-based auth)
- Ingest: source code files, README and documentation, commit history (optional), issue/PR descriptions (optional)
- Support file types: `.py`, `.js`, `.ts`, `.java`, `.go`, `.cpp`, `.md`, `.json`, `.yaml`, and others
- Use **LangChain File Loaders** and **LangChain Web Loaders** for document and API-based ingestion
- Gracefully handle rate limits from GitHub API (retry logic, exponential backoff)

### 3.2 Data Preprocessing (Step 2 — Preprocessing)

- Strip binary files, lock files, and auto-generated artifacts from processing scope
- Normalize whitespace and encoding inconsistencies across files
- Extract metadata per file: language, file path, last modified date, author (from git log where available)
- Deduplicate identical files or boilerplate (e.g. license headers)

### 3.3 Code Chunking (Step 3 — Splitting & Chunking)

- Apply **Code Splitter** (LangChain) to split source files along function and class boundaries, preserving logical units
- Apply **Markdown Header Splitter** for README and documentation files
- Apply **Recursive Character Splitter** as fallback for unsupported or plain-text files
- Chunk size target: ~512 tokens with ~50-token overlap between adjacent chunks to maintain context
- Store chunk metadata: file path, language, start/end line numbers, parent class/function name (where parseable)

### 3.4 Embeddings & Vector Knowledge Base (Step 4 — Embeddings)

- Generate embeddings using `sentence-transformers/all-MiniLM-L6-v2` (via Hugging Face) for cost-free operation
- Store embeddings in **ChromaDB** (primary); fall back to **FAISS** if ChromaDB is unavailable
- Knowledge base is repository-scoped: each repository ingestion creates or updates its own collection
- Support incremental updates: re-embed only changed files on subsequent ingestions (using GitHub commit SHAs as change detection)
- Index metadata alongside vectors for filtered retrieval (e.g. "only search Python files")

### 3.5 Query Processing & AI Engine (Step 5 — AI Engine)

- Convert user queries to embeddings using the same model as document embedding (semantic parity)
- Retrieve top-K relevant chunks (default K=5) from the vector store using cosine similarity
- Construct a structured prompt using **LangChain ChatPromptTemplate** combining: system context (assistant persona + repo summary), retrieved code chunks (with file path and line numbers), and user query
- Use **Groq + LLaMA 3** as the LLM backend for fast, free inference
- Persist conversation history per session in **MongoDB** using LangChain's MongoDB memory integration
- Support multi-turn conversations: each query is contextualized with prior turns

**Supported query types:**
- "What does `[function/class/file]` do?"
- "How is `[feature]` implemented across this repo?"
- "What are potential bugs or issues in `[file]`?"
- "Suggest improvements to `[function/module]`"
- "Explain the architecture of this repository"
- "Find all places where `[pattern]` is used"

### 3.6 User Interface (Step 6 — UI & Deployment)

- Build with **Streamlit** for rapid development and interactive UX
- UI components:
  - Repository input: GitHub URL + optional access token field
  - Ingestion progress indicator (file count, chunk count, embedding status)
  - Chat interface: message history, user input box, send button
  - Source citations panel: display retrieved file paths and line numbers alongside each response
  - Repository overview card: language breakdown, file count, last updated
- Session state management: active repository, conversation history
- Code blocks in responses rendered with syntax highlighting
- Option to clear conversation history and re-query

### 3.7 Testing & Optimization (Step 7 — Testing)

- Functional tests covering: ingestion pipeline, chunking correctness, embedding generation, retrieval accuracy, LLM response quality
- RAG pipeline evaluation using **LangChain Evaluation** (criteria-based: relevance, faithfulness, completeness)
- Performance benchmark: measure and enforce < 2-second end-to-end response latency for query + retrieval + LLM generation
- Hallucination monitoring: flag responses where LLM references code not present in retrieved context
- Optional: **DeepEval** integration for automated retrieval precision/recall measurement

---

## 4. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Response latency | < 2 seconds (query → response) |
| Ingestion time | < 60 seconds for repos up to 500 files |
| Embedding accuracy | Cosine similarity ≥ 0.75 for top-1 retrieved chunk on benchmark queries |
| Uptime (deployed) | 99% during active use |
| GitHub API compliance | Respect rate limits; support authenticated requests for private repos |
| Data privacy | No repository code stored beyond session unless user opts in |

---

## 5. Technical Architecture

```
User Query
    │
    ▼
[Streamlit UI]
    │
    ▼
[Query Embedding] ─── sentence-transformers/all-MiniLM-L6-v2
    │
    ▼
[Vector Search] ────── ChromaDB / FAISS
    │
    ▼
[Prompt Construction] ─ LangChain ChatPromptTemplate
    │                    + MongoDB Conversation Memory
    ▼
[LLM Inference] ─────── Groq + LLaMA 3
    │
    ▼
[Response + Citations]
    │
    ▼
[Streamlit UI → User]

─────────────── Ingestion Pipeline ───────────────

GitHub API → LangChain Loaders → Preprocessing
    → Code Splitter / Markdown Splitter
    → Embeddings (HuggingFace)
    → ChromaDB Knowledge Base
```

---

## 6. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Data Ingestion | GitHub API, LangChain File/Web Loaders | Native GitHub integration; flexible loader ecosystem |
| Code Splitting | LangChain Code Splitter, Recursive Splitter | Language-aware chunking preserves function/class context |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (HuggingFace) | Free, lightweight, semantically strong for code+text |
| Vector Store | ChromaDB (primary), FAISS (fallback) | Open-source, local, no infra cost |
| LLM | LLaMA 3 via Groq | Free for developers, fast inference (<1s), open-source |
| Memory | MongoDB (LangChain integration) | Free tier available; persistent conversation history |
| UI | Streamlit | Minimal code for interactive apps; Python-native |
| Version Control | GitHub | Standard; integrates with deployment platforms |
| Evaluation | LangChain Eval, DeepEval (optional) | RAG-specific metrics; actionable quality insights |

---

## 7. Milestones & Delivery Plan

| Phase | Deliverable | Timeline |
|---|---|---|
| Phase 1 | GitHub ingestion + chunking pipeline | Week 1–2 |
| Phase 2 | Embedding generation + ChromaDB knowledge base | Week 2–3 |
| Phase 3 | Query engine + LLM integration (Groq/LLaMA 3) | Week 3–4 |
| Phase 4 | Streamlit UI + MongoDB memory | Week 4–5 |
| Phase 5 | Testing, evaluation, latency optimization | Week 5–6 |
| Phase 6 | GitHub deployment + documentation | Week 6 |

---

## 8. Success Metrics

- Response latency consistently < 2 seconds across 95% of queries
- Top-1 retrieved chunk relevance score ≥ 0.75 on internal benchmark (20 labelled queries per test repo)
- User satisfaction: > 80% of responses rated "helpful" or "very helpful" in UI feedback widget
- Zero hallucinations referencing non-existent functions or files in 90%+ of responses (validated via LangChain Eval)
- Successful ingestion of repositories with up to 500 source files without errors

---

## 9. Out of Scope (v1.0)

- Real-time webhook-based ingestion on push events (planned for v1.1)
- IDE plugin (VS Code / JetBrains extension)
- Support for GitLab or Bitbucket repositories
- Automated PR comment generation
- Multi-repository cross-search

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| GitHub API rate limiting on large repos | Medium | High | Implement authenticated requests; cache ingestion results by commit SHA |
| LLM response latency exceeds 2s target | Medium | High | Use Groq's fast inference; reduce K (retrieved chunks) if needed |
| Embedding model not capturing code semantics well | Low | Medium | Benchmark against code-specific models (e.g. CodeBERT) and swap if needed |
| ChromaDB instability in containerized environments | Low | Medium | FAISS as ready fallback; document both setup paths |
| User uploads sensitive/private repo code | Medium | High | Display clear data handling notice; implement session-only storage by default |

---

*Document prepared for HiDevs Cohort — GitHub Repository Code Chat Assistant project.*
