import abc
from typing import List

class BaseEmbedder(abc.ABC):
    @abc.abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of text strings into vectors."""
        pass
        
    @abc.abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string into a vector."""
        pass
        
class SentenceTransformerEmbedder(BaseEmbedder):
    """Local embedder using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Using numpy array to list conversion
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
        
    def embed_query(self, query: str) -> List[float]:
        # Encode a single string, returns a 1D array
        embedding = self.model.encode(query, show_progress_bar=False)
        return embedding.tolist()

class BM25SparseEmbedder:
    """Local sparse embedder using fastembed's SPLADE/BM25."""
    
    def __init__(self, model_name: str = "Qdrant/bm25"):
        from fastembed.sparse.sparse_text_embedding import SparseTextEmbedding
        self.model_name = model_name
        self.model = SparseTextEmbedding(model_name=model_name)
        
    def embed_texts(self, texts: List[str]):
        # fastembed returns an iterator of SparseEmbedding objects
        # We'll convert them to dicts for qdrant client
        embeddings = list(self.model.embed(texts))
        
        result = []
        for emb in embeddings:
            # emb is a SparseEmbedding object with .indices and .values
            result.append({
                "indices": emb.indices.tolist(),
                "values": emb.values.tolist()
            })
        return result
        
    def embed_query(self, query: str):
        # A generator with 1 element
        emb = next(self.model.embed([query]))
        return {
            "indices": emb.indices.tolist(),
            "values": emb.values.tolist()
        }
