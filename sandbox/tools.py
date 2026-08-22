import os
import json
import subprocess
from typing import Optional, List
from pathlib import Path
from langchain_core.tools import tool
from sandbox.web_tools import web_search, fetch_webpage

from ingestion.scanner import RepositoryAnalyzer
from ingestion.embedder import SentenceTransformerEmbedder, BM25SparseEmbedder
from ingestion.indexer import QdrantIndexer
from ingestion.retriever import retrieve_code

# We keep global instances so tools don't re-initialize models on every call
_dense = None
_sparse = None
_indexer = None

def _get_indexer(path: str = ".") -> QdrantIndexer:
    global _dense, _sparse, _indexer
    if _indexer is None:
        _dense = SentenceTransformerEmbedder()
        _sparse = BM25SparseEmbedder()
        # Ensure it points to the path's qdrant data or default
        _indexer = QdrantIndexer(embedder=_dense, sparse_embedder=_sparse, path=str(Path(path) / ".qdrant_data"))
    return _indexer

@tool
def get_repository_map(path: str = ".") -> str:
    """
    Get a high-level map of the repository's structure, including detected sub-projects, languages, and entry points.
    Use this to understand the layout of an unfamiliar repository.
    """
    analyzer = RepositoryAnalyzer(path)
    repo_map = analyzer.analyze()
    return repo_map.model_dump_json(indent=2)

@tool
def search_code(query: str, path: str = ".", top_k: int = 5) -> str:
    """
    Search the repository for code snippets matching the query using Hybrid (Semantic + Keyword) search.
    Use this when you need to find where a specific concept, function, error code, or variable is implemented.
    Returns a JSON string of the top matching code chunks.
    """
    indexer = _get_indexer(path)
    results = retrieve_code(indexer, query, top_k=top_k)
    return json.dumps(results, indent=2)

@tool
def read_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """
    Read the contents of a source code file. 
    You can optionally specify a start_line and end_line (1-indexed) to read a specific portion of the file.
    Use this to investigate a file after you have found it via search_code or get_repository_map.
    """
    path = Path(file_path)
    if not path.exists():
        return f"Error: File '{file_path}' does not exist."
        
    try:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        start = (start_line - 1) if start_line else 0
        end = end_line if end_line else len(lines)
        
        start = max(0, start)
        end = min(len(lines), end)
        
        # Add line numbers for context
        snippet_lines = []
        for i in range(start, end):
            snippet_lines.append(f"{i+1}: {lines[i]}")
            
        return "\n".join(snippet_lines)
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"

@tool
def list_files(directory_path: str) -> str:
    """
    List all files and subdirectories in a given directory path.
    Use this to explore the contents of a specific folder.
    """
    path = Path(directory_path)
    if not path.exists():
        return f"Error: Directory '{directory_path}' does not exist."
        
    if not path.is_dir():
        return f"Error: '{directory_path}' is not a directory."
        
    try:
        items = os.listdir(path)
        items.sort()
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory '{directory_path}': {e}"

def _run_git_command(args: List[str], path: str = ".") -> str:
    try:
        result = subprocess.run(
            args,
            cwd=path,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return f"Git error: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"Error executing git command: {e}"

def _truncate_output(text: str, max_lines: int = 500) -> str:
    lines = text.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n... [Output truncated. Total lines: {len(lines)}]"
    return text

@tool
def git_log(path: str = ".", max_count: int = 10) -> str:
    """
    Fetch the recent commit history of the repository.
    Use this to see what changes were made recently.
    """
    args = ["git", "log", f"-n", str(max_count), "--oneline"]
    return _run_git_command(args, path)

@tool
def git_diff(path: str = ".", commit_a: Optional[str] = None, commit_b: Optional[str] = None, file_path: Optional[str] = None) -> str:
    """
    Show changes between commits or the working tree.
    If commit_a and commit_b are not provided, shows working tree changes.
    If file_path is provided, shows diff only for that file.
    Output is truncated if too long.
    """
    args = ["git", "diff"]
    if commit_a:
        args.append(commit_a)
    if commit_b:
        args.append(commit_b)
    if file_path:
        args.append("--")
        args.append(file_path)
        
    output = _run_git_command(args, path)
    return _truncate_output(output)

@tool
def git_show(commit_hash: str, path: str = ".") -> str:
    """
    Show the details and diff of a specific commit.
    Output is truncated if too long.
    """
    args = ["git", "show", commit_hash]
    output = _run_git_command(args, path)
    return _truncate_output(output)

@tool
def git_blame(file_path: str, path: str = ".") -> str:
    """
    Show what revision and author last modified each line of a file.
    Output is truncated if too long.
    """
    args = ["git", "blame", file_path]
    output = _run_git_command(args, path)
    return _truncate_output(output, max_lines=1000)

@tool
def search_commits(query: str, path: str = ".") -> str:
    """
    Search commit logs for a specific query string.
    Use this to find when a specific feature or bug was introduced.
    """
    args = ["git", "log", "-S", query, "--oneline"]
    output = _run_git_command(args, path)
    return _truncate_output(output)

# Export the tools for the agent to use
AGENT_TOOLS = [
    get_repository_map, search_code, read_file, list_files,
    git_log, git_diff, git_show, git_blame, search_commits,
    web_search, fetch_webpage
]
