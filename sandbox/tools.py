import os
import json
import subprocess
from typing import Optional, List, Annotated
from pathlib import Path
from langchain_core.tools import tool, InjectedToolArg
from sandbox.web_tools import web_search, fetch_webpage

from ingestion.scanner import RepositoryAnalyzer
from ingestion.embedder import SentenceTransformerEmbedder, BM25SparseEmbedder
from ingestion.indexer import QdrantIndexer
from ingestion.retriever import retrieve_code

# We keep global instances so tools don't re-initialize models on every call
_dense = None
_sparse = None
_indexer = None

def _get_indexer(path: str) -> QdrantIndexer:
    global _dense, _sparse, _indexer
    if _indexer is None:
        _dense = SentenceTransformerEmbedder()
        _sparse = BM25SparseEmbedder()
        _indexer = QdrantIndexer(embedder=_dense, sparse_embedder=_sparse, path=str(Path(path) / ".qdrant_data"))
    return _indexer

def _enforce_safe_path(requested_path: str, project_root: str) -> Path:
    """
    Resolves the requested path and ensures it is within the project_root.
    Also blocks access to sensitive files.
    Raises ValueError if the path is unsafe.
    """
    root = Path(project_root).resolve()
    target = Path(requested_path)
    
    # If the requested path is not absolute, treat it as relative to project_root
    if not target.is_absolute():
        target = (root / target).resolve()
    else:
        target = target.resolve()
        
    if not target.is_relative_to(root):
        raise ValueError(f"Path '{requested_path}' is outside the project root.")
        
    # Block sensitive files
    name = target.name.lower()
    if name == ".env" or "secret" in name or name == ".credentials":
        raise ValueError(f"Access to sensitive file '{name}' is denied.")
        
    return target

@tool
def get_repository_map(project_root: Annotated[str, InjectedToolArg]) -> str:
    """
    Get a high-level map of the repository's structure, including detected sub-projects, languages, and entry points.
    Use this to understand the layout of an unfamiliar repository.
    """
    try:
        analyzer = RepositoryAnalyzer(project_root)
        repo_map = analyzer.analyze()
        return f"<file_content>\n{repo_map.model_dump_json(indent=2)}\n</file_content>"
    except Exception as e:
        return f"Error analyzing repository: {e}"

@tool
def search_code(query: str, project_root: Annotated[str, InjectedToolArg], top_k: int = 5) -> str:
    """
    Search the repository for code snippets matching the query using Hybrid (Semantic + Keyword) search.
    Use this when you need to find where a specific concept, function, error code, or variable is implemented.
    Returns a JSON string of the top matching code chunks.
    """
    try:
        indexer = _get_indexer(project_root)
        results = retrieve_code(indexer, query, top_k=top_k)
        return f"<file_content>\n{json.dumps(results, indent=2)}\n</file_content>"
    except Exception as e:
        return f"Error searching code: {e}"

@tool
def read_file(file_path: str, project_root: Annotated[str, InjectedToolArg], start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """
    Read the contents of a source code file. 
    You can optionally specify a start_line and end_line (1-indexed) to read a specific portion of the file.
    Use this to investigate a file after you have found it via search_code or get_repository_map.
    """
    try:
        path = _enforce_safe_path(file_path, project_root)
    except ValueError as ve:
        return f"Security Error: {ve}"
        
    if not path.exists():
        return f"Error: File '{file_path}' does not exist."
        
    try:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        start = (start_line - 1) if start_line else 0
        end = end_line if end_line else len(lines)
        
        start = max(0, start)
        end = min(len(lines), end)
        
        if (end - start) > 300:
            end = start + 300
            truncated = True
        else:
            truncated = False
        
        snippet_lines = []
        for i in range(start, end):
            snippet_lines.append(f"{i+1}: {lines[i]}")
            
        res = f"<file_content>\n{chr(10).join(snippet_lines)}\n</file_content>"
        if truncated:
            res += f"\n... [Output truncated to 300 lines. Total file lines: {len(lines)}. Please use start_line and end_line to read specific sections.]"
        return res
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"

@tool
def list_files(directory_path: str, project_root: Annotated[str, InjectedToolArg]) -> str:
    """
    List all files and subdirectories in a given directory path.
    Use this to explore the contents of a specific folder.
    """
    try:
        path = _enforce_safe_path(directory_path, project_root)
    except ValueError as ve:
        return f"Security Error: {ve}"
        
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

def _truncate_output(text: str, max_lines: int = 250) -> str:
    lines = text.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n... [Output truncated. Total lines: {len(lines)}]"
    return text

@tool
def git_log(project_root: Annotated[str, InjectedToolArg], max_count: int = 10) -> str:
    """
    Fetch the recent commit history of the repository.
    Use this to see what changes were made recently.
    """
    args = ["git", "log", f"-n", str(max_count), "--oneline"]
    output = _run_git_command(args, project_root)
    return f"<file_content>\n{output}\n</file_content>"

@tool
def git_diff(project_root: Annotated[str, InjectedToolArg], commit_a: Optional[str] = None, commit_b: Optional[str] = None, file_path: Optional[str] = None) -> str:
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
        
    output = _run_git_command(args, project_root)
    return f"<file_content>\n{_truncate_output(output)}\n</file_content>"

@tool
def git_show(commit_hash: str, project_root: Annotated[str, InjectedToolArg]) -> str:
    """
    Show the details and diff of a specific commit.
    Output is truncated if too long.
    """
    args = ["git", "show", commit_hash]
    output = _run_git_command(args, project_root)
    return f"<file_content>\n{_truncate_output(output)}\n</file_content>"

@tool
def git_blame(file_path: str, project_root: Annotated[str, InjectedToolArg]) -> str:
    """
    Show what revision and author last modified each line of a file.
    Output is truncated if too long.
    """
    args = ["git", "blame", file_path]
    output = _run_git_command(args, project_root)
    return f"<file_content>\n{_truncate_output(output, max_lines=250)}\n</file_content>"

@tool
def search_commits(query: str, project_root: Annotated[str, InjectedToolArg]) -> str:
    """
    Search commit logs for a specific query string.
    Use this to find when a specific feature or bug was introduced.
    """
    args = ["git", "log", "-S", query, "--oneline"]
    output = _run_git_command(args, project_root)
    return f"<file_content>\n{_truncate_output(output)}\n</file_content>"

# Export the tools for the agent to use
from sandbox.web_tools import web_search, fetch_webpage
from sandbox.graph_tools import get_function_callers, get_function_dependencies, get_file_imports

# 4. Agent tools registry
AGENT_TOOLS = [
    get_repository_map, search_code, read_file, list_files,
    git_log, git_diff, git_show, git_blame, search_commits,
    web_search, fetch_webpage, get_function_callers, get_function_dependencies, get_file_imports
]
