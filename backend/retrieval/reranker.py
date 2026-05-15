from typing import List, Dict, Any
from pathlib import Path

class Reranker:
    """
    Scores and ranks the combined results from semantic and keyword searches.
    """
    
    def rank(self, query: str, semantic_results: List[Dict[str, Any]], keyword_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ranks results based on semantic similarity, exact keyword matches in the file,
        and symbol name matching.
        """
        # Create a set of files matched by keyword search for O(1) lookup
        keyword_matched_files = {kw_res['file_path'] for kw_res in keyword_results}
        
        # Lowercase query for symbol/filename matching
        query_lower = query.lower()
        
        ranked_results = []
        
        for result in semantic_results:
            metadata = result['metadata']
            file_path = metadata['file_path']
            symbol_name = metadata['symbol_name']
            
            # Base score is semantic similarity (scaled up slightly for easier reading)
            final_score = result['score'] * 10 
            
            # Boost if file was also matched by keyword search (ripgrep)
            if file_path in keyword_matched_files:
                final_score += 2.0
                
            # Boost if the symbol name exactly matches or is contained in the query
            if symbol_name.lower() in query_lower or query_lower in symbol_name.lower():
                final_score += 3.0
                
            # Boost if the query is in the file path (e.g., "jwt refresh" matching "auth/jwt.py")
            path_parts = Path(file_path).parts
            for part in path_parts:
                if part.lower() in query_lower:
                    final_score += 1.0
                    break
            
            ranked_results.append({
                "chunk_id": result['chunk_id'],
                "file_path": file_path,
                "symbol_name": symbol_name,
                "start_line": metadata['start_line'],
                "end_line": metadata['end_line'],
                "score": round(final_score, 4),
                "code": result['code']
            })
            
        # Sort by final score descending
        ranked_results.sort(key=lambda x: x['score'], reverse=True)
        return ranked_results
