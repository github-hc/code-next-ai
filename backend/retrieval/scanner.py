import os
from pathlib import Path
from typing import List, Set, Optional

class FileScanner:
    """
    Recursively scans a repository for source files, ignoring specified directories.
    """
    DEFAULT_IGNORES = {
        ".git", "node_modules", "venv", "env", ".venv",
        "dist", "build", "__pycache__", ".pytest_cache"
    }

    def __init__(self, root_dir: str | Path, ignored_dirs: Optional[Set[str]] = None):
        """
        Initializes the scanner with a root directory and a list of directories to ignore.
        """
        self.root_dir = Path(root_dir)
        self.ignored_dirs = ignored_dirs if ignored_dirs is not None else self.DEFAULT_IGNORES

    def scan(self, extensions: Optional[Set[str]] = None) -> List[Path]:
        """
        Scan the repository and return a list of valid file paths.
        
        Args:
            extensions: Set of valid file extensions (e.g., {".py"}). Defaults to {".py"}.
            
        Returns:
            A list of Path objects representing the discovered source files.
        """
        if extensions is None:
            extensions = {".py", ".js", ".jsx", ".ts", ".tsx"}

        valid_files = []

        for current_path, dirs, files in os.walk(self.root_dir):
            # Modify dirs in-place to prevent os.walk from descending into ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs and not d.startswith('.')]

            for file in files:
                file_path = Path(current_path) / file
                if file_path.suffix in extensions:
                    valid_files.append(file_path)

        return valid_files
