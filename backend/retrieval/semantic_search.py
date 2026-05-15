from typing import List, Dict, Any
from backend.retrieval.embeddings import OllamaEmbedder
from backend.retrieval.vector_store import ChromaVectorStore

class SemanticSearch:
    """
    Handles converting natural language queries into embeddings and searching the vector store.
    """
    
    def __init__(self, embedder: OllamaEmbedder, vector_store: ChromaVectorStore):
        self.embedder = embedder
        self.vector_store = vector_store

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Executes a semantic search for a given query.
        """
        query_embedding = self.embedder.embed_text(query)
        if not query_embedding:
            return []
            
        results = self.vector_store.similarity_search_by_vector(query_embedding, n_results=top_k)
        
        formatted_results = []
        if not results or not results['ids'] or not results['ids'][0]:
            return formatted_results
            
        # ChromaDB returns a list of lists for each include type
        ids = results['ids'][0]
        distances = results['distances'][0]
        metadatas = results['metadatas'][0]
        documents = results['documents'][0]
        
        for i in range(len(ids)):
            # Convert distance to a similarity score. 
            # Chroma L2 distance: lower is better. We invert it for a "score" where higher is better.
            distance = distances[i]
            score = 1.0 / (1.0 + distance)
            
            formatted_results.append({
                "chunk_id": ids[i],
                "score": score,
                "metadata": metadatas[i],
                "code": documents[i]
            })
            
        return formatted_results
