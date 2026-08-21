from pathlib import Path
from ingestion.models import CodeChunk
from ingestion.embedder import BaseEmbedder
from ingestion.indexer import QdrantIndexer

class MockEmbedder(BaseEmbedder):
    def embed_texts(self, texts):
        # Return a dummy vector of 384 length for each text
        return [[0.1] * 384 for _ in texts]
        
    def embed_query(self, query):
        return [0.1] * 384

def test_qdrant_indexer(tmp_path: Path):
    embedder = MockEmbedder()
    # Use tmp_path for local storage to avoid persisting test data
    indexer = QdrantIndexer(embedder=embedder, collection_name="test_collection", path=str(tmp_path / "qdrant"))
    
    chunks = [
        CodeChunk(
            file_path="mock.py",
            chunk_type="function",
            language="python",
            start_line=1,
            end_line=5,
            content="def hello():\n    print('hello')",
            symbol="hello"
        )
    ]
    
    count = indexer.index_chunks(chunks)
    assert count == 1
    
    results = indexer.search("where is hello?")
    assert len(results) == 1
    assert results[0]["payload"]["symbol"] == "hello"
    assert results[0]["payload"]["file_path"] == "mock.py"
