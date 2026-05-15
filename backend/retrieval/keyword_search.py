import subprocess
from pathlib import Path
from typing import List, Dict, Any

class KeywordSearch:
    """
    Uses ripgrep (rg) for exact keyword matching across the repository.
    """
    
    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Executes a ripgrep search for the exact query string.
        Returns a list of files that contain the keyword.
        """
        # Split query into words to find meaningful keywords, or search the whole string
        # For simplicity in the MVP, we just use the raw query as a literal string.
        
        cmd = ["rg", "-l", "--ignore-case", "--fixed-strings", query, str(self.root_dir)]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                # ripgrep returns 1 if no matches found
                return []
                
            matched_files = result.stdout.strip().split('\n')
            matched_files = [f for f in matched_files if f][:top_k]
            
            formatted_results = []
            for file_path in matched_files:
                formatted_results.append({
                    "file_path": file_path,
                    "matched_keyword": query
                })
                
            return formatted_results
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Warning: Keyword search failed (is ripgrep 'rg' installed in PATH?). Error: {e}")
            return []
