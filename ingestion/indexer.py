from typing import List, Dict, Any, Optional
import uuid
from ingestion.models import CodeChunk
from ingestion.embedder import BaseEmbedder

class QdrantIndexer:
    """Handles storing and retrieving CodeChunks from Qdrant vector database."""
    
    def __init__(self, embedder: BaseEmbedder, sparse_embedder=None, collection_name: str = "code_chunks", path: str = ".qdrant_data"):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, SparseVectorParams, SparseIndexParams
        
        self.embedder = embedder
        self.sparse_embedder = sparse_embedder
        self.collection_name = collection_name
        
        # Using local disk Qdrant storage for simplicity without Docker requirements
        self.client = QdrantClient(path=path)
        
        # Initialize collection if it doesn't exist
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            # We assume embedding size of 384 for all-MiniLM-L6-v2
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                sparse_vectors_config={"text-sparse": SparseVectorParams(
                    index=SparseIndexParams(
                        on_disk=False,
                    )
                )} if self.sparse_embedder else None
            )
            
    def index_chunks(self, chunks: List[CodeChunk]) -> int:
        """Embed and store a list of CodeChunks."""
        if not chunks:
            return 0
            
        from qdrant_client.models import PointStruct
        
        # We need to chunk the embedding process to avoid memory issues on massive repos
        batch_size = 100
        indexed_count = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [c.content for c in batch]
            
            # 1. Generate embeddings
            vectors = self.embedder.embed_texts(texts)
            
            sparse_vectors = None
            if self.sparse_embedder:
                sparse_vectors = self.sparse_embedder.embed_texts(texts)
            
            # 2. Build Qdrant PointStructs with payloads
            points = []
            from qdrant_client.models import SparseVector
            for j, chunk in enumerate(batch):
                payload = chunk.model_dump()
                
                # Check for sparse
                point_args = {
                    "id": str(uuid.uuid4()),
                    "vector": vectors[j],
                    "payload": payload
                }
                
                if sparse_vectors:
                    point_args["vector"] = {
                        "": vectors[j],  # Default dense vector
                        "text-sparse": SparseVector(
                            indices=sparse_vectors[j]["indices"],
                            values=sparse_vectors[j]["values"]
                        )
                    }
                    
                points.append(PointStruct(**point_args))
                
            # 3. Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            indexed_count += len(points)
            
        return indexed_count
        
    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search the vector database for the closest semantic matches to the query."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # 1. Embed query
        query_vector = self.embedder.embed_query(query)
        
        # 2. Build metadata filters if provided
        query_filter = None
        if filters:
            conditions = []
            for k, v in filters.items():
                conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
            query_filter = Filter(must=conditions)
            
        # 3. Search Qdrant
        if self.sparse_embedder:
            # Hybrid search using Prefetch
            from qdrant_client.models import Prefetch, SparseVector, FusionQuery, Fusion
            
            sparse_query = self.sparse_embedder.embed_query(query)
            
            prefetch_dense = Prefetch(
                query=query_vector,
                filter=query_filter,
                limit=top_k
            )
            
            prefetch_sparse = Prefetch(
                query=SparseVector(indices=sparse_query["indices"], values=sparse_query["values"]),
                using="text-sparse",
                filter=query_filter,
                limit=top_k
            )
            
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[prefetch_dense, prefetch_sparse],
                query=FusionQuery(fusion=Fusion.RRF),
                limit=top_k
            ).points
        else:
            # Dense only search
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k
            ).points

        
        # Format results
        results = []
        for hit in search_result:
            results.append({
                "score": hit.score,
                "payload": hit.payload
            })
            
        return results
