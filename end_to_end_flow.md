# Code Next AI: End-to-End Flow

This document explains the end-to-end architecture and data flow of the `coding-agent` application, from uploading a repository for indexing to querying it for answers.

## Architecture Diagram

```mermaid
flowchart TD
    %% User Actions
    User((User))

    subgraph UserInterface [UI Layer - app.py]
        direction TB
        UI_Index[Enter Repo Path & Click 'Index']
        UI_Query[Type Query & Click 'Send']
        UI_Display[Display Results in Chat]
    end

    User --> UI_Index
    User --> UI_Query
    UI_Display --> User

    %% Indexing Flow
    subgraph Indexing [Indexing Flow - main.py]
        direction TB
        Scanner[FileScanner: Find Source Files]
        Parser_AST[ASTParser: Parse .py files]
        Parser_TS[TreeSitterParser: Parse other files]
        Chunker[ChunkBuilder: Create Code Chunks]
        Embedder1[OllamaEmbedder: Generate Embeddings]
        DB_Store[(ChromaVectorStore)]
    end

    UI_Index --> Scanner
    Scanner --> |Python Files| Parser_AST
    Scanner --> |Other Files| Parser_TS
    Parser_AST --> Chunker
    Parser_TS --> Chunker
    Chunker --> Embedder1
    Embedder1 --> DB_Store

    %% Querying Flow
    subgraph Querying [Query Flow - main.py]
        direction TB
        Search_Hybrid[HybridSearch Orchestrator]
        Search_Semantic[SemanticSearch]
        Search_Keyword[KeywordSearch]
        Embedder2[OllamaEmbedder: Embed Query]
        DB_Query[(ChromaVectorStore)]
        Repo[Raw Repository Files]
        Rerank[Reranker: Score & Sort]
    end

    UI_Query --> Search_Hybrid
    Search_Hybrid --> Search_Semantic
    Search_Hybrid --> Search_Keyword
    
    Search_Semantic --> Embedder2
    Embedder2 --> DB_Query
    
    Search_Keyword --> Repo
    
    DB_Query --> Rerank
    Repo --> Rerank
    Rerank --> |Top K Results| UI_Display
```

## Step-by-Step Flow Explanation

### 1. Uploading and Indexing a Repository
When you select a repository path and click **"Index Repository"**:
1. **Scanning**: The `FileScanner` walks through the selected directory and identifies valid source code files.
2. **Parsing**: Depending on the file type, a parser extracts meaningful symbols (like functions, classes, etc.):
   - Python files (`.py`) are parsed using `ASTParser`.
   - Other supported files are parsed using `TreeSitterParser`.
3. **Chunking**: The `ChunkBuilder` takes these extracted symbols and breaks the code down into manageable chunks.
4. **Embedding**: The `OllamaEmbedder` generates a vector embedding for each code chunk. These embeddings capture the semantic meaning of the code.
5. **Storage**: Finally, the chunks and their corresponding embeddings are stored in `ChromaVectorStore` (ChromaDB) for fast vector retrieval later.

### 2. Asking a Question
When you type a question and click **Send**:
1. **Hybrid Search Initiation**: The query is passed to `HybridSearch`, which orchestrates both semantic and keyword-based searches to ensure comprehensive results.
2. **Semantic Search**:
   - The user's query is converted into a vector embedding using `OllamaEmbedder`.
   - `ChromaVectorStore` is queried to find code chunks with embeddings most similar to the query's embedding.
3. **Keyword Search**:
   - Simultaneously, `KeywordSearch` performs a lexical search directly against the raw repository files to find exact matches for terms in the query.
4. **Reranking**:
   - The results from both the Semantic and Keyword searches are combined.
   - The `Reranker` scores and sorts these combined results to ensure the most relevant code chunks are ranked highest.
5. **Display**: The top resulting code chunks (Top K) are formatted into Markdown (including file paths, line numbers, and code snippets) and displayed back to you in the UI chat interface (`app.py`).
