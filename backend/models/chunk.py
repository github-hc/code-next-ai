from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class CodeChunk:
    """
    Represents a semantic chunk of code extracted from a source file.
    """
    chunk_id: str
    file_path: str
    symbol_name: str
    chunk_type: str  # e.g., "function", "class"
    start_line: int
    end_line: int
    code: str
    docstring: Optional[str] = None
    embedding: Optional[List[float]] = None

    def to_metadata(self) -> dict:
        """
        Returns a dictionary suitable for ChromaDB metadata payload.
        Chroma metadata values must be strings, ints, or floats.
        """
        return {
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "symbol_name": self.symbol_name,
            "chunk_type": self.chunk_type,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "has_docstring": bool(self.docstring)
        }

    def to_dict(self) -> dict:
        """Serializes the chunk into a dictionary."""
        return asdict(self)
