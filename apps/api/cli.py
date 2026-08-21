import typer

app = typer.Typer(help="Autonomous Software Debugging Agent CLI")

@app.command()
def investigate(bug_report: str):
    """
    Investigate a bug report.
    For now, it only prints the investigation request.
    """
    typer.echo(f"Received investigation request for: '{bug_report}'")
    typer.echo("Initializing investigation... (Features to be implemented in later phases)")

@app.command()
def analyze(path: str = "."):
    """
    Analyze a repository to determine its structure, languages, and monorepo status.
    """
    import json
    from ingestion.scanner import RepositoryAnalyzer
    
    typer.echo(f"Analyzing repository at: {path}...")
    try:
        analyzer = RepositoryAnalyzer(path)
        repo_map = analyzer.analyze()
        typer.echo(repo_map.model_dump_json(indent=2))
    except Exception as e:
        typer.echo(f"Error analyzing repository: {e}", err=True)

@app.command()
def chunk(path: str, method: str = typer.Option("ast", help="Chunking method: 'ast' or 'fixed'")):
    """
    Chunk a source code file using the specified method and print the chunks.
    """
    from ingestion.chunker import ASTChunker, FixedSizeChunker
    import json
    
    typer.echo(f"Chunking {path} using {method} method...")
    try:
        if method == "ast":
            chunker = ASTChunker()
        else:
            chunker = FixedSizeChunker()
            
        chunks = chunker.chunk(path)
        typer.echo(f"Generated {len(chunks)} chunks.")
        
        for c in chunks:
            typer.echo("-" * 40)
            typer.echo(c.model_dump_json(indent=2))
            
    except Exception as e:
        typer.echo(f"Error chunking file: {e}", err=True)

@app.command()
def index(path: str = "."):
    """
    Scan, chunk, embed, and index a repository into Qdrant.
    """
    from ingestion.scanner import RepositoryAnalyzer
    from ingestion.chunker import ASTChunker
    from ingestion.embedder import SentenceTransformerEmbedder
    from ingestion.indexer import QdrantIndexer
    
    typer.echo(f"Starting ingestion pipeline for {path}...")
    
    # 1. Scan
    analyzer = RepositoryAnalyzer(path)
    repo_map = analyzer.analyze()
    
    # 2. Chunk
    chunker = ASTChunker()
    all_chunks = []
    
    # Helper to gather files (simplification for MVP)
    import os
    from pathlib import Path
    
    for root, dirs, files in os.walk(path):
        current = Path(root)
        dirs[:] = [d for d in dirs if not analyzer._is_ignored(current / d)]
        for f in files:
            file_path = current / f
            if not analyzer._is_ignored(file_path):
                ext = file_path.suffix.lower()
                # Only chunk supported languages for now
                if ext in [".py", ".js", ".ts", ".go", ".rs"]:
                    file_chunks = chunker.chunk(str(file_path))
                    all_chunks.extend(file_chunks)
                    
    typer.echo(f"Generated {len(all_chunks)} chunks. Indexing into Qdrant...")
    
    # 3. Embed & Index
    embedder = SentenceTransformerEmbedder()
    indexer = QdrantIndexer(embedder=embedder)
    
    count = indexer.index_chunks(all_chunks)
    typer.echo(f"Successfully indexed {count} chunks into Qdrant!")

@app.command()
def search(query: str, top_k: int = 5):
    """
    Search the indexed repository for semantic matches to the query.
    """
    from ingestion.embedder import SentenceTransformerEmbedder
    from ingestion.indexer import QdrantIndexer
    import json
    
    typer.echo(f"Searching for: '{query}'...")
    
    embedder = SentenceTransformerEmbedder()
    indexer = QdrantIndexer(embedder=embedder)
    
    results = indexer.search(query, top_k=top_k)
    
    typer.echo(f"Found {len(results)} matches:\n")
    for hit in results:
        payload = hit["payload"]
        score = hit["score"]
        typer.echo(f"[{score:.4f}] {payload.get('file_path')} (Symbol: {payload.get('symbol')})")
        
        # Print a snippet of the code
        content = payload.get('content', '')
        lines = content.splitlines()
        snippet = "\n".join(lines[:5])
        if len(lines) > 5:
            snippet += "\n..."
            
        typer.echo(snippet)
        typer.echo("-" * 40)

@app.command()
def hybrid_search(query: str, top_k: int = 5):
    """
    Search using Hybrid Retrieval (Dense + Sparse/BM25) and provide reasoning.
    """
    from ingestion.embedder import SentenceTransformerEmbedder, BM25SparseEmbedder
    from ingestion.indexer import QdrantIndexer
    from ingestion.retriever import retrieve_code
    
    typer.echo(f"Starting Hybrid Search for: '{query}'...")
    
    dense = SentenceTransformerEmbedder()
    sparse = BM25SparseEmbedder()
    indexer = QdrantIndexer(embedder=dense, sparse_embedder=sparse)
    
    results = retrieve_code(indexer, query, top_k=top_k)
    
    typer.echo(f"Found {len(results)} matches:\n")
    for hit in results:
        payload = hit["payload"]
        
        typer.echo(f"File: {payload.get('file_path')} (Symbol: {payload.get('symbol')})")
        typer.echo(f"Reasoning: {hit.get('explanation')}")
        
        content = payload.get('content', '')
        lines = content.splitlines()
        snippet = "\n".join(lines[:5])
        if len(lines) > 5:
            snippet += "\n..."
            
        typer.echo(snippet)
        typer.echo("=" * 60)

@app.command()
def test_tools(query: str = typer.Argument("What does the repository look like?")):
    """
    Test that an LLM can understand and select our tools.
    Defaults to using Ollama (llama3 model) running locally.
    """
    from langchain_ollama import ChatOllama
    from sandbox.tools import AGENT_TOOLS
    import json
    
    typer.echo(f"Testing tools with query: '{query}'")
    
    try:
        # Initialize open-source model running on local Ollama
        llm = ChatOllama(model="llama3", temperature=0)
        
        # Bind the tools to the model
        llm_with_tools = llm.bind_tools(AGENT_TOOLS)
        
        # Invoke the model
        response = llm_with_tools.invoke(query)
        
        typer.echo("\n--- LLM Response ---")
        if response.tool_calls:
            typer.echo(f"SUCCESS: The LLM decided to call {len(response.tool_calls)} tool(s)!")
            for tc in response.tool_calls:
                typer.echo(f"Tool Name: {tc['name']}")
                typer.echo(f"Arguments: {json.dumps(tc['args'], indent=2)}")
        else:
            typer.echo("FAILURE: The LLM did not call any tools. It responded with:")
            typer.echo(response.content)
            
    except Exception as e:
        typer.echo(f"Error testing tools. Ensure Ollama is running with 'llama3' installed. Details: {e}", err=True)

@app.command()
def test_graph(query: str = typer.Argument("Where is the RepositoryAnalyzer class defined?")):
    """
    Test the LangGraph fundamental experiments (Python loop vs LangGraph loop).
    Requires OPENROUTER_API_KEY environment variable.
    """
    from sandbox.graph_experiments import run_python_loop, run_langgraph_loop
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if not os.environ.get("OPENROUTER_API_KEY"):
        typer.echo("Error: OPENROUTER_API_KEY environment variable is missing.", err=True)
        typer.echo("Please add it to your .env file or export it.", err=True)
        return
        
    try:
        run_python_loop(query)
        run_langgraph_loop(query)
    except Exception as e:
        typer.echo(f"Graph experiment failed: {e}", err=True)

@app.command()
def triage(bug_report: str = typer.Argument(..., help="The unstructured bug report text.")):
    """
    Run the Triage Agent to convert a bug report into a structured InvestigationRequest.
    """
    from backend.agents.triage import TriageAgent
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if not os.environ.get("OPENROUTER_API_KEY"):
        typer.echo("Error: OPENROUTER_API_KEY environment variable is missing.", err=True)
        return
        
    try:
        typer.echo(f"Processing bug report: '{bug_report}'...\n")
        agent = TriageAgent()
        result = agent.triage(bug_report)
        typer.echo("--- Structured Investigation Request ---")
        typer.echo(result.model_dump_json(indent=2))
    except Exception as e:
        typer.echo(f"Error during triage: {e}", err=True)

@app.command()
def hypothesis(bug_report: str = typer.Argument(..., help="The unstructured bug report text.")):
    """
    Run the Triage Agent and then the Hypothesis Agent to generate debugging theories.
    """
    from backend.agents.triage import TriageAgent
    from backend.agents.hypothesis import HypothesisAgent
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if not os.environ.get("OPENROUTER_API_KEY"):
        typer.echo("Error: OPENROUTER_API_KEY environment variable is missing.", err=True)
        return
        
    try:
        typer.echo(f"--- 1. Triaging Bug Report ---\n")
        triage_agent = TriageAgent()
        investigation_req = triage_agent.triage(bug_report)
        typer.echo(investigation_req.model_dump_json(indent=2))
        
        typer.echo(f"\n--- 2. Generating Hypotheses ---\n")
        hypothesis_agent = HypothesisAgent()
        hypotheses_list = hypothesis_agent.generate_hypotheses(investigation_req)
        
        for i, h in enumerate(hypotheses_list.hypotheses, 1):
            typer.echo(f"Hypothesis {i}: {h.title}")
            typer.echo(f"  Description: {h.description}")
            typer.echo(f"  Reason: {h.reason}")
            typer.echo(f"  Expected Evidence: {', '.join(h.expected_evidence)}")
            typer.echo(f"  Investigation Plan: {', '.join(h.investigation_plan)}")
            typer.echo("")
            
    except Exception as e:
        typer.echo(f"Error during hypothesis generation: {e}", err=True)

@app.command()
def evidence(bug_report: str = typer.Argument(..., help="The unstructured bug report text.")):
    """
    Run Triage -> Hypothesis -> Evidence Collection on the first hypothesis.
    """
    from backend.agents.triage import TriageAgent
    from backend.agents.hypothesis import HypothesisAgent
    from backend.agents.evidence import EvidenceGraph
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if not os.environ.get("OPENROUTER_API_KEY"):
        typer.echo("Error: OPENROUTER_API_KEY environment variable is missing.", err=True)
        return
        
    try:
        typer.echo(f"--- 1. Triaging Bug Report ---\n")
        triage_agent = TriageAgent()
        investigation_req = triage_agent.triage(bug_report)
        
        typer.echo(f"\n--- 2. Generating Hypotheses ---\n")
        hypothesis_agent = HypothesisAgent()
        hypotheses_list = hypothesis_agent.generate_hypotheses(investigation_req)
        
        if not hypotheses_list.hypotheses:
            typer.echo("No hypotheses generated.")
            return
            
        first_hypothesis = hypotheses_list.hypotheses[0]
        typer.echo(f"Evaluating Hypothesis: {first_hypothesis.title}")
        typer.echo(f"Plan: {first_hypothesis.investigation_plan}")
        
        typer.echo(f"\n--- 3. Collecting Evidence ---\n")
        evidence_graph = EvidenceGraph()
        result_state = evidence_graph.run(first_hypothesis)
        
        eval_result = result_state.get("evaluation")
        if eval_result:
            typer.echo(f"Status: {eval_result.status}")
            typer.echo(f"Confidence: {eval_result.confidence_score}%")
            typer.echo(f"Supporting Evidence: {eval_result.supporting_evidence}")
            typer.echo(f"Contradicting Evidence: {eval_result.contradicting_evidence}")
        else:
            typer.echo("No evaluation returned.")
            
    except Exception as e:
        typer.echo(f"Error during evidence collection: {e}", err=True)

@app.command()
def version():
    """
    Print the version of the autonomous debugger.
    """
    typer.echo("0.1.0")

if __name__ == "__main__":
    app()
