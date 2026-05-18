import requests
from typing import List, Dict, Any

class OllamaLLM:
    """
    Handles communication with the local Ollama instance for text generation.
    """
    
    def __init__(self, model_name: str = "qwen2.5:7b", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.api_url = f"{host}/api/generate"
        
    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generates an answer using the provided query and context chunks.
        """
        context_texts = []
        for i, chunk in enumerate(context_chunks, 1):
            file_path = chunk.get('metadata', {}).get('file_path', 'Unknown file')
            code = chunk.get('code', '')
            context_texts.append(f"--- Chunk {i} from {file_path} ---\n{code}\n")
            
        context_str = "\n".join(context_texts)
        
        prompt = f"""You are a helpful coding assistant. 
Use the following retrieved code chunks to answer the user's question. 
If the answer is not in the context, say "I don't have enough context to answer."

Context:
{context_str}

Question:
{query}
"""
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "No response generated.")
        except Exception as e:
            return f"Error communicating with LLM: {e}"
