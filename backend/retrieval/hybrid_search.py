from typing import List, Dict, Any

from backend.retrieval.semantic_search import SemanticSearch
from backend.retrieval.keyword_search import KeywordSearch
from backend.retrieval.reranker import Reranker

class HybridSearch:
    """
    Coordinates semantic search, keyword search, and reranking to produce final results.
    """
    
    def __init__(self, semantic_search: SemanticSearch, keyword_search: KeywordSearch, reranker: Reranker):
        self.semantic_search = semantic_search
        self.keyword_search = keyword_search
        self.reranker = reranker

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes the hybrid search pipeline.
        
        Args:
            query: The user's natural language query.
            top_k: Number of final ranked results to return.
            
        Returns:
            A list of ranked result dictionaries containing code chunks and metadata.
        """
        # 1. Get semantic results (fetch more than top_k to give the reranker room to work)
        semantic_results = self.semantic_search.search(query, top_k=top_k * 3)
        
        # 2. Get keyword results
        keyword_results = self.keyword_search.search(query, top_k=top_k * 3)
        
        # 3. Rerank semantic results using keyword context
        ranked_results = self.reranker.rank(query, semantic_results, keyword_results)
        
        # 4. Return the top K results
        return ranked_results[:top_k]
