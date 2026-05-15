import hashlib
from typing import List, Dict, Any
from pathlib import Path

from backend.models.chunk import CodeChunk

class ChunkBuilder:
    """
    Converts parsed AST symbols into standardized CodeChunk models.
    """
    
    def build_chunks(self, file_path: Path | str, symbols: List[Dict[str, Any]]) -> List[CodeChunk]:
        """
        Takes raw symbols extracted by ASTParser and converts them into CodeChunks.
        
        Args:
            file_path: The origin file path of the symbols.
            symbols: List of extracted symbol dictionaries from the ASTParser.
            
        Returns:
            A list of instantiated CodeChunk dataclasses.
        """
        file_str = str(file_path)
        chunks = []

        for symbol in symbols:
            # Generate a unique deterministic ID for the chunk
            # Combining file path, symbol name, and line numbers ensures uniqueness
            unique_str = f"{file_str}::{symbol['name']}::{symbol['start_line']}::{symbol['end_line']}"
            chunk_id = hashlib.sha256(unique_str.encode('utf-8')).hexdigest()

            chunk = CodeChunk(
                chunk_id=chunk_id,
                file_path=file_str,
                symbol_name=symbol["name"],
                chunk_type=symbol["type"],
                start_line=symbol["start_line"],
                end_line=symbol["end_line"],
                docstring=symbol["docstring"],
                code=symbol["code"]
            )
            chunks.append(chunk)

        return chunks
