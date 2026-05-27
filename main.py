
import sys
import argparse
import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"
import json
from pathlib import Path

def load_settings():
    settings_path = Path("settings.json")
    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
SETTINGS = load_settings()
LOG_CHUNKS = SETTINGS.get("log_chunks", False)
LOG_AST_PARSER = SETTINGS.get("log_ast_parser", False)

from backend.retrieval.scanner import FileScanner
from backend.retrieval.parser import ASTParser, TreeSitterParser
from backend.retrieval.chunker import ChunkBuilder
from backend.retrieval.embeddings import OllamaEmbedder
from backend.retrieval.vector_store import WeaviateVectorStore

from backend.generation.ollama_llm import OllamaLLM

def build_index(repo_path: str):
    """
    Scans the repository, extracts symbols, generates embeddings, and stores them.
    """
    repo_path_obj = Path(repo_path).expanduser().resolve()
    print(f"[*] Scanning repository: {repo_path_obj} ...")
    
    scanner = FileScanner(repo_path_obj)
    files = scanner.scan()
    print(f"[*] Found {len(files)} valid source files.")

    ast_parser = ASTParser(log_ast_parser=LOG_AST_PARSER)
    ts_parser = TreeSitterParser()
    chunker = ChunkBuilder()
    embedder = OllamaEmbedder()
    
    total_chunks = 0
    with WeaviateVectorStore() as vector_store:
        print("[*] Purging previous index...")
        vector_store.clear()
        
        if LOG_CHUNKS:
            with open("chunks_log.txt", "w", encoding="utf-8") as f:
                f.write(f"=== CHUNK LOG for {repo_path_obj} ===\n\n")

        for i, file in enumerate(files):
            print(f"  [{i+1}/{len(files)}] Parsing {file.name} ...")
            if file.suffix == '.py':
                symbols = ast_parser.parse_file(file)
                if LOG_AST_PARSER:
                    with open("log.txt", "a", encoding="utf-8") as log_f:
                        log_f.write(f"--- Symbols for {file.name} ---\n")
                        log_f.write(json.dumps(symbols, indent=4) + "\n\n")
            else:
                symbols = ts_parser.parse_file(file)
                
            if not symbols:
                continue
            
            chunks = chunker.build_chunks(file, symbols)
            if not chunks:
                continue
                
            # Generate embeddings and assign to chunks
            for chunk in chunks:
                chunk.embedding = embedder.embed_text(chunk.code)
                
                if LOG_CHUNKS:
                    log_msg = (
                        f"\n[DEBUG] --------------------------------------------------\n"
                        f"[DEBUG] Storing Chunk -> Symbol: {chunk.symbol_name}\n"
                        f"[DEBUG] File: {chunk.file_path} (Lines {chunk.start_line}-{chunk.end_line})\n"
                        f"[DEBUG] Code:\n{chunk.code}\n"
                        f"[DEBUG] --------------------------------------------------\n"
                    )
                    print(log_msg)
                    with open("chunks_log.txt", "a", encoding="utf-8") as f:
                        f.write(log_msg + "\n")
                
            vector_store.add_chunks(chunks)
            total_chunks += len(chunks)

    print(f"[*] Indexing complete. Indexed {total_chunks} code chunks into Weaviate.")
    return total_chunks

def query_repo(repo_path: str, query: str, model_name: str = "qwen2.5:7b"):
    """
    Executes a hybrid search query against the indexed repository.
    Returns (token_stream_generator, results_list).
    """
    repo_path_obj = Path(repo_path).expanduser().resolve()
    print(f"\n==================================================")
    print(f"QUERY:\n\"{query}\"\n")
    print(f"RESULTS:")
    
    embedder = OllamaEmbedder()
    with WeaviateVectorStore() as vector_store:
        query_embedding = embedder.embed_text(query)
        results = vector_store.hybrid_search(query, query_embedding, n_results=5)
    
    llm = OllamaLLM(model_name=model_name)
    token_stream = llm.generate_answer_stream(query, results)
    
    return token_stream, results

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
        token_stream, results = query_repo(args.repo, args.query)
        
        print("\n=== AI Answer ===")
        # Print each token as it arrives for a typewriter effect in the terminal
        for token in token_stream:
            print(token, end="", flush=True)
        print()
        print("\n=== References ===")
        
        if not results:
            print("No relevant code chunks found.")
            print("==================================================")
        else:
            repo_path_obj = Path(args.repo).expanduser().resolve()
            for i, res in enumerate(results, 1):
                print(f"{i}.")
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
