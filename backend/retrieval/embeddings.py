import requests
from typing import List

class OllamaEmbedder:
    """
    Generates embeddings using a local Ollama instance.
    """
    
    def __init__(self, model_name: str = "nomic-embed-text", host: str = "http://127.0.0.1:11434"):
        """
        Initialize the Ollama API client for embeddings.
        
        Args:
            model_name: The embedding model to use (default: nomic-embed-text)
            host: The Ollama server URL
        """
        self.model_name = model_name
        self.api_url = f"{host}/api/embeddings"

    def embed_text(self, text: str) -> List[float]:
        """
        Generates an embedding vector for a given string of text.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
        """
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except requests.exceptions.RequestException as e:
            print(f"Error generating embedding for text: {e}")
            return []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a batch of texts.
        
        Note: The standard Ollama /api/embeddings endpoint processes one prompt at a time.
        We process sequentially here. For massive repositories, async requests would be better.
        """
        embeddings = []
        for text in texts:
            embeddings.append(self.embed_text(text))
        return embeddings
