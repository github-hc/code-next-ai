import sys
import argparse
import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"
from pathlib import Path

from backend.retrieval.scanner import FileScanner
from backend.retrieval.parser import ASTParser
from backend.retrieval.chunker import ChunkBuilder
from backend.retrieval.embeddings import OllamaEmbedder
from backend.retrieval.vector_store import ChromaVectorStore
from backend.retrieval.semantic_search import SemanticSearch
from backend.retrieval.keyword_search import KeywordSearch
from backend.retrieval.reranker import Reranker
from backend.retrieval.hybrid_search import HybridSearch

def build_index(repo_path: str):
    """
    Scans the repository, extracts symbols, generates embeddings, and stores them.
    """
    repo_path_obj = Path(repo_path).resolve()
    print(f"[*] Scanning repository: {repo_path_obj} ...")
    
    scanner = FileScanner(repo_path_obj)
    files = scanner.scan()
    print(f"[*] Found {len(files)} Python files.")

    parser = ASTParser()
    chunker = ChunkBuilder()
    embedder = OllamaEmbedder()
    vector_store = ChromaVectorStore()

    total_chunks = 0
    for i, file in enumerate(files):
        print(f"  [{i+1}/{len(files)}] Indexing: {file.relative_to(repo_path_obj) if repo_path_obj in file.parents else file.name}")
        
        symbols = parser.parse_file(file)
        if not symbols:
            continue
            
        chunks = chunker.build_chunks(file, symbols)
        if not chunks:
            continue
            
        # Generate embeddings and assign to chunks
        for chunk in chunks:
            chunk.embedding = embedder.embed_text(chunk.code)
            
        vector_store.add_chunks(chunks)
        total_chunks += len(chunks)

    print(f"[*] Indexing complete. Indexed {total_chunks} code chunks into ChromaDB.")

def query_repo(repo_path: str, query: str):
    """
    Executes a hybrid search query against the indexed repository.
    """
    repo_path_obj = Path(repo_path).resolve()
    print(f"\n==================================================")
    print(f"QUERY:\n\"{query}\"\n")
    print(f"RESULTS:")
    
    embedder = OllamaEmbedder()
    vector_store = ChromaVectorStore()
    
    semantic_search = SemanticSearch(embedder, vector_store)
    keyword_search = KeywordSearch(repo_path_obj)
    reranker = Reranker()
    
    hybrid_search = HybridSearch(semantic_search, keyword_search, reranker)
    
    results = hybrid_search.search(query, top_k=5)
    
    if not results:
        print("No relevant code chunks found.")
        print("==================================================")
        return

    for i, res in enumerate(results, 1):
        print(f"{i}.")
        
        # Try to make the file path relative to the repo for cleaner output
        try:
            rel_path = Path(res['file_path']).relative_to(repo_path_obj)
        except ValueError:
            rel_path = res['file_path']
            
        print(f"File: {rel_path}")
        print(f"Symbol: {res['symbol_name']}")
        print(f"Lines: {res['start_line']}-{res['end_line']}")
        print(f"Score: {res['score']}")
        print(f"Code Snippet:\n--------------------------------------------------\n{res['code']}\n--------------------------------------------------")
        print()
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local AI Coding Agent MVP")
    parser.add_argument("command", choices=["index", "query"], help="Command to run: 'index' to build DB, 'query' to search.")
    parser.add_argument("--repo", default=".", help="Path to the repository to scan/query (default: current dir)")
    parser.add_argument("--query", type=str, help="The natural language query (required for 'query' command)")
    
    args = parser.parse_args()
    
    if args.command == "index":
        build_index(args.repo)
    elif args.command == "query":
        if not args.query:
            print("Error: --query argument is required when using the 'query' command.")
            sys.exit(1)
        query_repo(args.repo, args.query)
