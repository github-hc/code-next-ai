import ast
from pathlib import Path
from typing import List, Dict, Any

class ASTParser:
    """
    Parses Python source files into abstract syntax trees and extracts functions, methods, and classes
    while preserving the exact source code segments.
    """
    
    def parse_file(self, file_path: Path | str) -> List[Dict[str, Any]]:
        """
        Parses a single file and returns a list of extracted symbols.
        
        Args:
            file_path: The path to the Python file to parse.
            
        Returns:
            A list of dictionaries, where each dict represents an extracted symbol
            (function or class) containing its metadata and raw code.
        """
        file_path = Path(file_path)
        try:
            source = file_path.read_text(encoding='utf-8')
            tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError) as e:
            # Skip files with syntax errors or encoding issues during MVP
            print(f"Warning: Failed to parse {file_path}. Error: {e}")
            return []

        symbols = []

        class SymbolVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                self._extract_symbol(node, "function")
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node):
                self._extract_symbol(node, "function")
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                self._extract_symbol(node, "class")
                self.generic_visit(node)

            def _extract_symbol(self, node, symbol_type):
                docstring = ast.get_docstring(node)
                code_segment = ast.get_source_segment(source, node)
                
                # In rare cases get_source_segment might return None for nodes lacking source info
                if code_segment is None:
                    return

                symbols.append({
                    "name": node.name,
                    "type": symbol_type,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "docstring": docstring,
                    "code": code_segment
                })

        visitor = SymbolVisitor()
        visitor.visit(tree)
        return symbols
