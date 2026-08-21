from typing import List, Dict, Any, Optional
from ingestion.indexer import QdrantIndexer

def retrieve_code(indexer: QdrantIndexer, query: str, filters: Optional[Dict[str, Any]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Unified retrieval interface that performs search via QdrantIndexer.
    If the indexer has a sparse_embedder, this will automatically be a Hybrid Search.
    
    The function adds an 'explanation' string to each result detailing the reasoning.
    """
    results = indexer.search(query, top_k=top_k, filters=filters)
    
    enriched_results = []
    
    for r in results:
        score = r["score"]
        payload = r["payload"]
        
        # Simple heuristic explanation. In Qdrant Hybrid Search (RRF), scores are typically between 0 and 2.0+
        # RRF fusing happens, but we can't easily extract the sub-scores without deeper Qdrant API hooks.
        # But we can look at the payload to see if there's an exact string match which would explain a high sparse score.
        
        explanation = f"Match score: {score:.4f}."
        
        query_lower = query.lower()
        if payload.get("symbol") and query_lower in payload["symbol"].lower():
            explanation += f" Strong exact/partial match found on symbol '{payload['symbol']}'."
        elif query_lower in payload["content"].lower():
            explanation += " Keyword found in the chunk content."
        else:
            explanation += " Match is likely primarily semantic/conceptual."
            
        r["explanation"] = explanation
        enriched_results.append(r)
        
    return enriched_results
