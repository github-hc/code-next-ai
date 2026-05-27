import requests
import json
from typing import List, Dict, Any, Generator

class OllamaLLM:
    """
    Handles communication with the local Ollama instance for text generation.
    """
    
    def __init__(self, model_name: str = "qwen2.5:7b", host: str = "http://127.0.0.1:11434"):
        self.model_name = model_name
        self.api_url = f"{host}/api/generate"
        
    def _build_prompt(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        context_texts = []
        for i, chunk in enumerate(context_chunks, 1):
            file_path = chunk.get('file_path') or chunk.get('metadata', {}).get('file_path', 'Unknown file')
            code = chunk.get('code', '')
            context_texts.append(f"--- Chunk {i} from {file_path} ---\n{code}\n")

        context_str = "\n".join(context_texts)
        return f"""You are a helpful coding assistant. 
Use the following retrieved code chunks to answer the user's question. 
If the answer is not in the context, say \"I don't have enough context to answer.\"

Context:
{context_str}

Question:
{query}
"""

    def generate_answer_stream(self, query: str, context_chunks: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """
        Streams the answer token by token. Yields each text fragment as it arrives.
        """
        payload = {
            "model": self.model_name,
            "prompt": self._build_prompt(query, context_chunks),
            "stream": True,
            "options": {
                "num_predict": 512,
            },
            "keep_alive": "20m"
        }
        try:
            with requests.post(self.api_url, json=payload, stream=True, timeout=(10, 300)) as response:
                response.raise_for_status()
                for raw_line in response.iter_lines():
                    if raw_line:
                        data = json.loads(raw_line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done", False):
                            break
        except Exception as e:
            yield f"\n\n*Error communicating with LLM: {e}*"

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Blocking convenience wrapper — joins all streamed tokens.
        """
        return "".join(self.generate_answer_stream(query, context_chunks))
