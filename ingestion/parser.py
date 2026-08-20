import abc
from typing import List, Dict, Any
from pathlib import Path

class BaseParser(abc.ABC):
    @abc.abstractmethod
    def parse_file(self, file_path: str) -> Any:
        """Parse a file and return the AST or raw tree."""
        pass

class TreeSitterParser(BaseParser):
    def __init__(self):
        import tree_sitter_language_pack as ts_pack
        self.ts_pack = ts_pack
        
    def parse_file(self, file_path: str) -> Any:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Cannot parse non-existent file: {file_path}")
            
        ext = path.suffix.lower()
        lang_str = self._ext_to_lang(ext)
        if not lang_str:
            raise ValueError(f"Unsupported extension for parsing: {ext}")
            
        parser = self.ts_pack.get_parser(lang_str)
        content = path.read_bytes()
        tree = parser.parse(content)
        
        return {
            "tree": tree,
            "content": content,
            "language": lang_str,
            "file_path": file_path
        }
        
    def _ext_to_lang(self, ext: str) -> str:
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust"
        }
        return mapping.get(ext)
