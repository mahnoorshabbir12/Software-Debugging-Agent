import abc
from typing import List, Optional
from pathlib import Path

from ingestion.models import CodeChunk
from ingestion.parser import BaseParser, TreeSitterParser

class BaseChunker(abc.ABC):
    @abc.abstractmethod
    def chunk(self, file_path: str) -> List[CodeChunk]:
        """Convert a source file into a list of CodeChunks."""
        pass

class FixedSizeChunker(BaseChunker):
    """Chunks a file purely by splitting lines, ignoring code structure."""
    
    def __init__(self, chunk_size_lines: int = 50, overlap_lines: int = 10):
        self.chunk_size = chunk_size_lines
        self.overlap = overlap_lines

    def chunk(self, file_path: str) -> List[CodeChunk]:
        path = Path(file_path)
        if not path.exists():
            return []
            
        lines = path.read_text(encoding="utf-8").splitlines()
        chunks = []
        
        i = 0
        while i < len(lines):
            end = min(i + self.chunk_size, len(lines))
            chunk_content = "\n".join(lines[i:end])
            
            chunks.append(CodeChunk(
                file_path=file_path,
                chunk_type="text",
                language="unknown",
                start_line=i + 1,
                end_line=end,
                content=chunk_content
            ))
            
            if end == len(lines):
                break
            i += (self.chunk_size - self.overlap)
            
        return chunks

class ASTChunker(BaseChunker):
    """Uses Tree-sitter to intelligently chunk code into functions and classes."""
    
    def __init__(self, parser: Optional[BaseParser] = None):
        self.parser = parser or TreeSitterParser()
        
    def chunk(self, file_path: str) -> List[CodeChunk]:
        try:
            parsed = self.parser.parse_file(file_path)
        except ValueError:
            # Fallback if language unsupported
            return FixedSizeChunker().chunk(file_path)
            
        tree = parsed["tree"]
        content = parsed["content"]
        lang = parsed["language"]
        
        chunks = []
        
        def traverse(node, parent_name=None):
            # Identifying functions and classes
            is_func = node.type in ['function_definition', 'method_definition', 'function_declaration', 'arrow_function']
            is_class = node.type in ['class_definition', 'class_declaration']
            
            if is_func or is_class:
                # Find name node if available
                name_node = None
                for child in node.children:
                    if child.type == 'identifier':
                        name_node = child
                        break
                
                symbol_name = None
                if name_node:
                    # tree-sitter bytes slicing
                    symbol_name = content[name_node.start_byte:name_node.end_byte].decode('utf-8')
                
                # We need the full source of the node
                chunk_content = content[node.start_byte:node.end_byte].decode('utf-8')
                
                chunks.append(CodeChunk(
                    file_path=file_path,
                    symbol=symbol_name,
                    chunk_type="class" if is_class else "function",
                    language=lang,
                    start_line=node.start_point[0] + 1, # Tree-sitter is 0-indexed for rows
                    end_line=node.end_point[0] + 1,
                    content=chunk_content,
                    parent=parent_name
                ))
                
                # Update parent name for children traversal if it's a class
                if is_class and symbol_name:
                    parent_name = symbol_name
            
            for child in node.children:
                traverse(child, parent_name)

        traverse(tree.root_node)
        
        # If no structural chunks found, maybe it's just a script
        if not chunks:
            # Fallback to whole file as one chunk or fixed size
            text_content = content.decode('utf-8')
            chunks.append(CodeChunk(
                file_path=file_path,
                chunk_type="file",
                language=lang,
                start_line=1,
                end_line=text_content.count('\n') + 1,
                content=text_content
            ))
            
        return chunks
