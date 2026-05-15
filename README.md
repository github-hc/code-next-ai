# Local AI Coding Agent (MVP)

This project is a repository intelligence system focused on allowing developers to perform natural language semantic queries over their codebase entirely locally and offline.

This is Phase 1 of the agent: Natural language query → relevant files/functions/code chunks.

## Architecture

The system uses a state-of-the-art offline RAG (Retrieval-Augmented Generation) pipeline adapted specifically for source code:

1. **Repository Scanner**: Recursively scans standard repositories, ignoring `.git`, `node_modules`, `venv`, etc.
2. **AST Parser**: Instead of naive text chunking, uses Python's built-in `ast` to extract discrete functions and classes, preserving exact source formatting and context.
3. **Chunk Builder**: Maps AST nodes to semantic `CodeChunk` models containing metadata like exact line numbers.
4. **Embeddings**: Uses a local Ollama instance running `nomic-embed-text` to generate vector representations of the code.
5. **Vector Store**: Persists embeddings locally using ChromaDB.
6. **Hybrid Search Engine**:
   - **Semantic Search**: Uses ChromaDB to find conceptually similar code.
   - **Keyword Search**: Uses `ripgrep` (`rg`) to find exact symbol and keyword matches.
7. **Reranker**: Combines the results, boosting scores for exact symbol matches, file path relevance, and keyword occurrences to provide a highly accurate Top K ranking.

## Prerequisites

- **Python 3.11+**
- **Ollama**: Installed and running locally.
- **ripgrep**: The `rg` command-line tool must be installed and available in your system's PATH.
  - Mac: `brew install ripgrep`

## Setup Instructions

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Pull the Ollama embedding model:**
   Ensure Ollama is running (`ollama serve`), then pull the model:
   ```bash
   ollama pull nomic-embed-text
   ```

## Usage

The agent has two primary modes: `index` and `query`.

### 1. Indexing a Repository

Before you can query a repository, you must build the semantic index. This will scan the files, parse the AST, generate embeddings via Ollama, and store them in a local ChromaDB folder (`chroma_db/`).

```bash
python main.py index --repo /path/to/your/repository
```
*(If `--repo` is omitted, it defaults to the current directory).*

### 2. Querying the Repository

Once indexed, you can perform hybrid searches using natural language.

```bash
python main.py query --repo /path/to/your/repository --query "Fix JWT refresh issue"
```

**Example Output:**
```
==================================================
QUERY:
"Fix JWT refresh issue"

RESULTS:
1.
File: auth/jwt.py
Symbol: refresh_token
Lines: 22-48
Score: 13.92

2.
File: auth/session.py
Symbol: validate_session
Lines: 10-32
Score: 11.87
==================================================
```

## Project Structure

- `main.py`: The CLI entrypoint.
- `backend/models/`: Contains the core data structures (`CodeChunk`).
- `backend/retrieval/`:
  - `scanner.py`: File discovery.
  - `parser.py`: AST extraction.
  - `chunker.py`: Model building.
  - `embeddings.py`: Ollama integration.
  - `vector_store.py`: ChromaDB integration.
  - `semantic_search.py`, `keyword_search.py`, `hybrid_search.py`: The retrieval engine.
  - `reranker.py`: The final scoring logic.

## Future Roadmap
- Expand AST parsing to multiple languages via `tree-sitter`.
- Add an LLM layer to synthesize the retrieved chunks into conversational answers.
- Implement file-watching to update the ChromaDB index incrementally on file save.
