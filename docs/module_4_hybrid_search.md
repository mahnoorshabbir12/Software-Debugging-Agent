# Module 4: Hybrid Code Retrieval

This document logs our learnings from Module 4, focusing on the gap between semantic mapping and exact keyword searching, and how Hybrid Search bridges it.

## 1. The Shortcoming of Semantic Search

**What is the concept?**
Semantic search maps concepts. "Authorization check" and "JWT token parsing" map to similar vectors. However, when a developer is debugging, they often have an exact string in their terminal: an error code (`HTTP_401_UNAUTHORIZED`), a stack trace file path, or a randomly generated identifier (`user_uuid`).

**What problem does it cause?**
Dense embedding models like `all-MiniLM-L6-v2` don't "read" exact strings very well. They squash exact sequences of characters into a conceptual cloud. If you search for the exact variable name `JWT_SECRET`, semantic search might return 5 other completely different secrets or authorization functions before it returns the exact file containing `JWT_SECRET`. 

**The Solution:**
We need an algorithm that actually counts exactly how many times `JWT_SECRET` appears in a chunk of code. This is called **Lexical (Keyword) Search**.

## 2. Sparse Vectors & BM25

**What is the concept?**
BM25 (Best Matching 25) is an algorithm that ranks documents based on the frequency of the exact search terms appearing in them. In modern Vector Databases, this is represented as a **Sparse Vector** (a vector with thousands of zeros, where only the indices corresponding to the exact words are non-zero).

**Where it is used:** `ingestion/embedder.py` (`BM25SparseEmbedder`)

**Why we chose `fastembed`:**
We integrated the `fastembed` library because it generates BM25 Sparse Vectors completely locally and instantly without needing a heavy Elasticsearch or Postgres setup. It integrates perfectly with our Qdrant database.

## 3. Hybrid Search (Reciprocal Rank Fusion)

**What is the concept?**
Now that we have *two* scores for every chunk of code (a Semantic Dense Score and a Keyword Sparse Score), we need to combine them. **Reciprocal Rank Fusion (RRF)** is an algorithm used by Qdrant that mathematically fuses the rankings.

**Where it is used:** `ingestion/indexer.py`

If a file has the exact keyword `JWT_SECRET` (high sparse score) *and* is semantically related to "authorization" (high dense score), RRF pushes it to the absolute top of the results.

### The Experiment (`tests/test_hybrid_rag.py`)

We mocked a chunk of code containing the exact string `'JWT_SECRET_401'`. 
When queried, our new `QdrantIndexer` used the `Prefetch` API with `FusionQuery(fusion=Fusion.RRF)` to trigger a Hybrid search. The test proved that this exact keyword is successfully retrieved and identified as a "Keyword match" by our unified retrieval interface (`ingestion/retriever.py`).

## Next Steps
Our Retrieval engine is officially complete and production-grade! We are now ready for **Module 5: Retrieval as Agent Tools**. We will take the `retrieve_code` function we just built and give it to an LLM Agent, empowering it to explore the codebase entirely autonomously!
