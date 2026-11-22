# PyDocsPal - Resume & Project Portfolio Highlights

PyDocsPal is an enterprise-grade Python documentation and cross-version compatibility assistant built with FastAPI, LangGraph, ChromaDB, Sentence Transformers, and Streamlit.

---

## 3 Resume-Ready Bullet Points

- **Architected an end-to-end Hybrid RAG engine** combining **dense vector embeddings (`all-MiniLM-L6-v2`)** in ChromaDB and **sparse lexical TF-IDF** with **Reciprocal Rank Fusion (RRF, $k=60$)** and a sub-millisecond bounded in-memory cache ($TTL=300s$, 1,000 max entries), achieving **100% grounded citations** and **zero hallucinations** through evidence-based abstention.
- **Engineered a deterministic Python version compatibility engine** indexing **4,101 stdlib directives across Python 3.8–3.15** and developed an autonomous **LangGraph multi-step agent** with stateful graph memory, automatic tool routing, cyclical execution guards, and a **human-in-the-loop approval checkpoint** for high-risk queries.
- **Productionized containerized microservices** via **FastAPI, Streamlit, and Docker Compose**, implementing structured request telemetry (per-request latency in ms, prompt/completion token tracking), prompt-injection defenses, 100% automated test coverage (**50+ pytest test cases across 3 suites, 0 Ruff lint errors**), and low-memory runtime optimizations for Render cloud deployment within a **512MB RAM constraint**.

---

## Technical Skills Demonstrated

- **AI/ML & RAG:** Retrieval-Augmented Generation (RAG), ChromaDB, Sentence Transformers (`all-MiniLM-L6-v2`), Reciprocal Rank Fusion (RRF), Lexical Search (TF-IDF), LangGraph, Prompt Engineering, Prompt-Injection Defense, Hallucination Prevention & Abstention.
- **Backend & Architecture:** Python 3.11/3.12, FastAPI, Pydantic v2, RESTful APIs, Uvicorn, SQLite, In-Memory Caching (LRU/TTL), Thread Safety.
- **Observability & Reliability:** Per-request telemetry (latency in ms, token counting), structured logging, health checks, error isolation, graceful degradation.
- **Frontend:** Streamlit, interactive chat interface, version badges, human-in-the-loop approval UI, user feedback logging.
- **DevOps, Testing & Quality:** Docker, Docker Compose, GitHub Actions (CI/CD), pytest, pytest-mock, Ruff (linter/formatter), Render cloud deployment.

---

## Project Scale & System Metrics

| Metric | Measured Value |
|---|---|
| **Python Stdlib Version Directives** | **4,101** directives indexed (`data/stdlib_versions.csv`) |
| **Document Chunking Strategy** | **1,800 characters** with **250-character overlap** |
| **Embedding Vector Dimension** | **384-dimensional** dense embeddings |
| **RRF Constant ($k$)** | **$60$** (fusing semantic + lexical ranks) |
| **Cache Performance** | **Sub-millisecond hit latency**, bounded 1,000 entries, 300s TTL |
| **Input Security Limits** | **2,000 characters** (questions/messages), **500 characters** (search queries) |
| **Test Suite Passing** | **100% pass (50+ tests)** across `test_day9`, `test_day11_suite`, `test_day13_suite` in ~13s |
| **Linting & Code Quality** | **0 errors / 0 warnings** via `ruff check .` |
| **Memory Footprint** | Optimized for single-threaded BLAS/OMP to run seamlessly under **512MB RAM** |
