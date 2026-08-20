from pathlib import Path
from ingestion.chunker import FixedSizeChunker, ASTChunker

MOCK_PYTHON_CODE = """
def hello_world():
    print("Hello")
    return True

class Calculator:
    def add(self, a, b):
        return a + b
        
    def subtract(self, a, b):
        return a - b
"""

def test_fixed_size_chunker(tmp_path: Path):
    file_path = tmp_path / "mock.py"
    file_path.write_text(MOCK_PYTHON_CODE.strip())
    
    # 5 lines per chunk
    chunker = FixedSizeChunker(chunk_size_lines=5, overlap_lines=2)
    chunks = chunker.chunk(str(file_path))
    
    assert len(chunks) > 1
    assert chunks[0].chunk_type == "text"
    assert chunks[0].end_line == 5

def test_ast_chunker(tmp_path: Path):
    file_path = tmp_path / "mock.py"
    file_path.write_text(MOCK_PYTHON_CODE.strip())
    
    chunker = ASTChunker()
    chunks = chunker.chunk(str(file_path))
    
    # We expect:
    # 1. hello_world (function)
    # 2. Calculator (class)
    # 3. Calculator.add (function)
    # 4. Calculator.subtract (function)
    
    assert len(chunks) == 4
    
    types = [c.chunk_type for c in chunks]
    assert types.count("function") == 3
    assert types.count("class") == 1
    
    symbols = [c.symbol for c in chunks]
    assert "hello_world" in symbols
    assert "Calculator" in symbols
    assert "add" in symbols
    
    # Check parent tracking
    add_chunk = next(c for c in chunks if c.symbol == "add")
    assert add_chunk.parent == "Calculator"
