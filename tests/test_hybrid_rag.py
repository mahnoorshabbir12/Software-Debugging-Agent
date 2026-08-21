from pathlib import Path
from ingestion.models import CodeChunk
from ingestion.embedder import BaseEmbedder
from ingestion.indexer import QdrantIndexer
from ingestion.retriever import retrieve_code

class MockDenseEmbedder(BaseEmbedder):
    def embed_texts(self, texts):
        return [[0.1] * 384 for _ in texts]
    def embed_query(self, query):
        return [0.1] * 384

class MockSparseEmbedder:
    def embed_texts(self, texts):
        return [{"indices": [1, 2], "values": [0.5, 0.5]} for _ in texts]
    def embed_query(self, query):
        return {"indices": [1, 2], "values": [0.5, 0.5]}

def test_hybrid_rag(tmp_path: Path):
    dense = MockDenseEmbedder()
    sparse = MockSparseEmbedder()
    
    indexer = QdrantIndexer(
        embedder=dense, 
        sparse_embedder=sparse,
        collection_name="test_hybrid_collection", 
        path=str(tmp_path / "qdrant_hybrid")
    )
    
    chunks = [
        CodeChunk(
            file_path="mock.py",
            chunk_type="function",
            language="python",
            start_line=1,
            end_line=5,
            content="def get_secret():\n    return 'JWT_SECRET_401'",
            symbol="get_secret"
        )
    ]
    
    count = indexer.index_chunks(chunks)
    assert count == 1
    
    # Test hybrid retrieve_code
    results = retrieve_code(indexer, "JWT_SECRET_401", top_k=5)
    
    assert len(results) == 1
    assert results[0]["payload"]["symbol"] == "get_secret"
    assert "Keyword found" in results[0]["explanation"] or "semantic" in results[0]["explanation"]
