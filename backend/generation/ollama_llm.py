import requests
import json
from typing import List, Dict, Any, Generator

from backend.generation.prompts import build_prompt

class OllamaLLM:
    """
    Handles communication with the local Ollama instance for text generation.
    """
    
    def __init__(self, model_name: str = "qwen2.5:7b", host: str = "http://127.0.0.1:11434"):
        self.model_name = model_name
        self.api_url = f"{host}/api/generate"


    def _log_query_details(self, query: str, context_chunks: List[Dict[str, Any]], answer: str):
        """
        Logs the query, selected model, context, and generated answer to query_log.txt.
        """
        import datetime
        from pathlib import Path
        import json
        
        try:
            # Check settings dynamically (allows editing settings without rebooting the app)
            settings_path = Path("settings.json")
            log_queries = True
            if settings_path.exists():
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                        log_queries = settings.get("log_queries", True)
                except Exception:
                    pass

            if not log_queries:
                return

            log_path = "query_log.txt"
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format context chunks
            context_str = ""
            if not context_chunks:
                context_str = "No relevant context chunks retrieved.\n\n"
            else:
                for i, chunk in enumerate(context_chunks, 1):
                    file_path = chunk.get("file_path", "unknown")
                    start_line = chunk.get("start_line", "?")
                    end_line = chunk.get("end_line", "?")
                    symbol_name = chunk.get("symbol_name", "unknown")
                    code = chunk.get("code", "").strip()
                    context_str += f"--- Chunk {i}: {file_path} (Lines {start_line}-{end_line}, Symbol: {symbol_name}) ---\n{code}\n\n"

            log_entry = (
                f"{'='*80}\n"
                f"TIMESTAMP:       {timestamp}\n"
                f"SELECTED MODEL:  {self.model_name}\n"
                f"QUESTION:\n{query}\n\n"
                f"CONTEXT:\n{context_str}"
                f"ANSWER:\n{answer}\n"
                f"{'='*80}\n\n"
            )
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            # Silently print warning to stderr to avoid interrupting UI or CLI flows
            import sys
            sys.stderr.write(f"[Warning] Failed to write to query_log.txt: {e}\n")


    def _log_query_details_async(self, query: str, context_chunks: List[Dict[str, Any]], answer: str):
        """
        Spawns a background daemon thread to log query details without blocking the main stream or UI thread.
        """
        import threading
        thread = threading.Thread(
            target=self._log_query_details,
            args=(query, context_chunks, answer),
            daemon=True
        )
        thread.start()

    def generate_answer_stream(self, query: str, context_chunks: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """
        Streams the answer token by token. Yields each text fragment as it arrives.
        """
        payload = {
            "model": self.model_name,
            "prompt": build_prompt(query, context_chunks),
            "stream": True,
            "options": {
                "num_predict": 1024,
            },
            "keep_alive": "20m"
        }
        accumulated_answer = []
        try:
            with requests.post(self.api_url, json=payload, stream=True, timeout=(10, 300)) as response:
                response.raise_for_status()
                for raw_line in response.iter_lines():
                    if raw_line:
                        data = json.loads(raw_line)
                        token = data.get("response", "")
                        if token:
                            accumulated_answer.append(token)
                            yield token
                        if data.get("done", False):
                            break
            # Log after successful completion of stream in background
            self._log_query_details_async(query, context_chunks, "".join(accumulated_answer))
        except Exception as e:
            error_msg = f"\n\n*Error communicating with LLM: {e}*"
            accumulated_answer.append(error_msg)
            yield error_msg
            # Log even on error so developer knows what happened in background
            self._log_query_details_async(query, context_chunks, "".join(accumulated_answer))

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Blocking convenience wrapper — joins all streamed tokens.
        """
        return "".join(self.generate_answer_stream(query, context_chunks))




