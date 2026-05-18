import ast
from pathlib import Path
from typing import List, Dict, Any

class ASTParser:
    """
    Parses Python source files into abstract syntax trees and extracts functions, methods, and classes
    """
    
    def __init__(self, log_ast_parser: bool = False):
        self.log_ast_parser = log_ast_parser

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
            # Log the AST tree to a file
            if self.log_ast_parser:
                with open("tree_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"=== AST Tree for {file_path} ===\n")
                    f.write(ast.dump(tree, indent=2) + "\n\n")
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

class TreeSitterParser:
    """
    Parses JS/TS files using Tree-Sitter to extract functions, classes, and methods.
    """
    def __init__(self):
        try:
            from tree_sitter import Language, Parser
            import tree_sitter_javascript as tsjavascript
            import tree_sitter_typescript as tstypescript
            
            self.js_lang = Language(tsjavascript.language())
            self.ts_lang = Language(tstypescript.language_typescript())
            self.tsx_lang = Language(tstypescript.language_tsx())
            
            self.js_parser = Parser(self.js_lang)
            self.ts_parser = Parser(self.ts_lang)
            self.tsx_parser = Parser(self.tsx_lang)
            self.available = True
        except ImportError as e:
            print(f"Tree-sitter not installed properly: {e}")
            self.available = False

    def parse_file(self, file_path: Path | str) -> List[Dict[str, Any]]:
        if not self.available:
            return []
            
        file_path = Path(file_path)
        try:
            source = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return []

        suffix = file_path.suffix.lower()
        if suffix in ['.js', '.jsx']:
            parser = self.js_parser
            lang = self.js_lang
        elif suffix == '.ts':
            parser = self.ts_parser
            lang = self.ts_lang
        elif suffix == '.tsx':
            parser = self.tsx_parser
            lang = self.tsx_lang
        else:
            return []

        tree = parser.parse(bytes(source, "utf8"))
        
        query_str = """
        (function_declaration) @function
        (method_definition) @method
        (class_declaration) @class
        (arrow_function) @arrow
        """
        
        from tree_sitter import Query, QueryCursor
        try:
            query = Query(lang, query_str)
            cursor = QueryCursor(query)
            captures = cursor.captures(tree.root_node)
        except Exception as e:
            print(f"Warning: Failed to execute tree-sitter query on {file_path}. Error: {e}")
            return []

        symbols = []

        for capture_name, nodes in captures.items():
            for n in nodes:
                start_line = n.start_point[0] + 1
                end_line = n.end_point[0] + 1
                
                name_node = n.child_by_field_name('name')
                if name_node:
                    name = source[name_node.start_byte:name_node.end_byte]
                else:
                    name = "anonymous_" + capture_name
                    
                code_segment = source[n.start_byte:n.end_byte]
                
                if len(code_segment.strip()) < 5:
                    continue

                symbols.append({
                    "name": name,
                    "type": "class" if capture_name == "class" else "function",
                    "start_line": start_line,
                    "end_line": end_line,
                    "docstring": None,
                    "code": code_segment
                })

        return symbols
