import json
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from langchain_core.tools import tool

@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for external documentation, GitHub issues, or package changelogs.
    Returns a JSON string of results with 'title', 'href', and 'body' (a short snippet).
    Use this when the local repository knowledge is insufficient.
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(r)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error performing web search: {e}"

@tool
def fetch_webpage(url: str) -> str:
    """
    Fetch the text content of a webpage (e.g., a documentation page or GitHub issue).
    Use this after web_search to read the full contents of a relevant URL.
    Returns the parsed text of the webpage.
    """
    try:
        # Use a generic user agent to prevent basic blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator="\n")
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Truncate to avoid context limit overflow
        max_chars = 15000
        if len(text) > max_chars:
            return text[:max_chars] + f"\n... [Content truncated. Total length: {len(text)} chars]"
            
        return text
    except Exception as e:
        return f"Error fetching webpage: {e}"
