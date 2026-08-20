# Module 2: Code Parsing & Structural Chunking

This document logs our learnings from Module 2, focusing on the concepts, architecture, and experiments behind converting raw source code into structured chunks for a debugging agent.

## 1. Code Chunking Strategy: Structural vs. Fixed-Size

**What is the concept?**
Code chunking breaks large source files into smaller segments. These chunks are embedded and indexed in a vector database (like Qdrant) so the agent can perform Retrieval-Augmented Generation (RAG).

**What problem does it solve?**
LLMs have strict limits on how much context they can process. We cannot feed a massive repository or a 10,000-line file into a prompt. However, code is highly structured. If we split text blindly, we risk cutting a function in half, rendering the retrieved chunk useless to the agent.

**Where it is used:** `ingestion/chunker.py`

### The Experiment

To prove why fixed-size text chunking is weak for code, we implemented two chunkers behind a `BaseChunker` interface and ran tests against a mocked Python file (`tests/test_chunker.py`).

**Alternative A: Fixed-Size Text Chunking (`FixedSizeChunker`)**
- **How it works:** Splits the file linearly (e.g., every 5 lines) regardless of syntax.
- **The Result:** The test showed that `FixedSizeChunker` split the `Calculator` class right in the middle of its methods. It did not know the method belonged to a class or what the function was named.
- **When to use it:** For unstructured PDFs or markdown articles (e.g., if we integrated ColPali for reading documentation).
- **When NOT to use it:** When indexing source code.

**Alternative B: AST-Aware Chunking (`ASTChunker`)**
- **How it works:** Uses an Abstract Syntax Tree parser to detect exactly where `function_definition` and `class_definition` nodes start and end. 
- **The Result:** The test showed `ASTChunker` cleanly generated 4 distinct chunks (`hello_world`, `Calculator`, `add`, `subtract`), extracting the exact code boundaries and correctly associating `add` with its parent class `Calculator`.
- **Why it was chosen:** Our debugging agent must have exact code boundaries to patch bugs successfully.

## 2. AST Parser Selection: `tree-sitter`

**What is the concept?**
An engine capable of parsing raw text into an Abstract Syntax Tree based on language grammars.

**Where it is used:** `ingestion/parser.py`

**Identify and Compare Alternatives:**

*Alternative A: Python's built-in `ast` module*
- **Pros:** Fast, zero-dependency, standard library.
- **Cons:** Only works for Python.

*Alternative B: `tree-sitter`*
- **Pros:** The industry standard. Capable of parsing JS, Python, Go, Rust, and more using a unified syntax tree format.
- **Cons:** Requires installing C-extensions.

**Why we chose `tree-sitter`:**
A debugging agent that can only understand Python is fundamentally limited. Modern codebases are almost entirely polyglot (e.g., React frontend + Python backend). By using `tree-sitter` and `tree-sitter-language-pack` from day one, we guarantee that our `RepositoryAnalyzer` and `ASTChunker` can seamlessly adapt to full-stack debugging tasks.

## Next Steps
With code structurally chunked and parsed, we are ready for **Module 3: Embeddings & Vector RAG**, where we will embed these `CodeChunk` models and push them into Qdrant to perform hybrid code retrieval.
