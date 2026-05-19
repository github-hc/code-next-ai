<div align="center">

# 🧠 Code Next AI

### Your Codebase. Your Machine. Your Rules.

**A fully offline, privacy-first AI coding assistant that understands your entire codebase — no cloud, no API keys, no subscriptions.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-black?style=flat-square)](https://ollama.com)
[![ChromaDB](https://img.shields.io/badge/Vector%20DB-ChromaDB-orange?style=flat-square)](https://trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

<img width="2880" height="1800" alt="image" src="https://github.com/user-attachments/assets/bc4ff09c-9f1e-4fd2-82bd-49b162db7082" />

---

## 🔒 100% Offline. Zero Tokens. Infinite Queries.

Unlike GitHub Copilot, Cursor, or any cloud-based AI tool, **Code Next AI runs entirely on your local machine**:

| Feature | Code Next AI | Cloud AI Tools |
|---|---|---|
| 🔒 Privacy | **Your code never leaves your machine** | Code sent to remote servers |
| 💰 Cost | **Free forever** | API tokens, monthly subscriptions |
| 🌐 Internet | **No connection required** | Requires internet |
| ⚡ Speed | **No rate limits** | Rate-limited, throttled |
| 🏢 Enterprise | **Works on air-gapped systems** | Not possible |

---

## ✨ What It Does

Ask natural language questions about any codebase and get **AI-generated answers with referenced source code** — all processed locally.

**Example questions you can ask:**
- *"How does the authentication flow work?"*
- *"Where is the database connection configured?"*
- *"What does the `make_nws_request` function do?"*
- *"Which functions handle error responses?"*

---

## 🏗️ Architecture

Code Next AI uses a state-of-the-art **offline RAG (Retrieval-Augmented Generation)** pipeline built specifically for source code:

```
Your Codebase
     │
     ▼
┌─────────────────┐
│  File Scanner   │  Recursively scans files, ignoring .git, node_modules, venv
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AST / Tree-    │  Extracts functions & classes with exact line numbers
│  Sitter Parser  │  (Python via ast, JS/TS via tree-sitter)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chunk Builder  │  Builds semantic CodeChunk objects with metadata
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ollama Embedder │  Generates local vector embeddings (nomic-embed-text)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    ChromaDB     │  Persists embeddings in a local vector database
└─────────────────┘
         │  (Query time)
         ▼
┌─────────────────────────────────┐
│        Hybrid Search Engine     │
│  ┌─────────────┐ ┌───────────┐  │
│  │  Semantic   │ │  Keyword  │  │
│  │  Search     │ │  Search   │  │
│  │ (ChromaDB)  │ │ (ripgrep) │  │
│  └──────┬──────┘ └─────┬─────┘  │
│         └──────┬────────┘       │
│                ▼                │
│           Reranker              │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────┐
│  Ollama LLM     │  Synthesizes answer from retrieved context (local model)
└────────┬────────┘
         │
         ▼
   Answer + References (in the UI)
```

---

## 🖥️ UI: VS Code–Style 3-Pane Interface

The desktop app (powered by [Flet](https://flet.dev)) gives you a familiar IDE-like experience:

- **Left Pane — Explorer**: Browse your indexed repository files. Click any file to instantly open it in the editor.
- **Middle Pane — Code Editor**: Full syntax-highlighted code viewer built into the app.
- **Right Pane — AI Chat**: Ask questions, get streamed answers with collapsible reference panels showing exactly which functions were used.

---

## ⚙️ Prerequisites

| Dependency | Purpose | Install |
|---|---|---|
| **Python 3.10+** | Runtime | [python.org](https://python.org) |
| **Ollama** | Local LLM + Embeddings engine | [ollama.com](https://ollama.com) |
| **ripgrep** | Keyword search | `brew install ripgrep` |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd coding-agent

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Pull Local Models

Ensure Ollama is running (`ollama serve`), then pull the required models:

```bash
# Embedding model (required for indexing & search)
ollama pull nomic-embed-text

# LLM model for answering (pick one)
ollama pull qwen2.5:7b      # Recommended — fast & capable
ollama pull phi3:mini        # Lighter, faster
ollama pull gemma4:latest    # Google's model
```

### 3. Launch the App

```bash
python app.py
```

The desktop UI will open. From there:
1. Click **Browse Folder** → select your codebase
2. Click **Index Repository** → wait for indexing to complete
3. Ask your first question in the chat panel!

---

## 🖥️ CLI Usage (Advanced)

You can also use the agent directly from the terminal:

```bash
# Index a repository
python main.py index --repo /path/to/your/project

# Query it
python main.py query --repo /path/to/your/project --query "How does authentication work?"
```

---

## 📁 Project Structure

```
coding-agent/
├── app.py                      # Desktop UI (Flet, 3-pane VS Code layout)
├── main.py                     # CLI entrypoint + core build_index / query_repo
├── settings.json               # Feature flags (log_chunks, log_ast_parser)
├── requirements.txt
│
├── backend/
│   ├── generation/
│   │   └── ollama_llm.py       # Local LLM answer generation
│   └── retrieval/
│       ├── scanner.py          # File discovery & filtering
│       ├── parser.py           # AST (Python) + Tree-Sitter (JS/TS) parsing
│       ├── chunker.py          # CodeChunk model builder
│       ├── embeddings.py       # Ollama nomic-embed-text client
│       ├── vector_store.py     # ChromaDB integration
│       ├── semantic_search.py  # Vector similarity search
│       ├── keyword_search.py   # ripgrep keyword search
│       ├── hybrid_search.py    # Unified search orchestrator
│       └── reranker.py         # Result scoring & ranking
│
└── chroma_db/                  # Local vector database (auto-created)
```

---

## 🗺️ Roadmap

- [x] AST-based Python parsing
- [x] Tree-Sitter parsing for JS/TS
- [x] Local embeddings via Ollama
- [x] Hybrid search (semantic + keyword)
- [x] LLM answer generation (fully offline)
- [x] 3-pane VS Code–style desktop UI
- [x] In-app file viewer with syntax highlighting
- [x] Collapsible reference panels in chat
- [ ] File watcher for incremental re-indexing on save
- [ ] Support for more languages (Go, Rust, Java)
- [ ] Multi-repo workspace support
- [ ] Chat history persistence

---

## 🛡️ Privacy Guarantee

> **Your code is yours.** Code Next AI performs all computation locally. No code, query, or result is ever transmitted to any external server.

---

<div align="center">
  Built with ❤️ for developers who care about their privacy.
</div>
