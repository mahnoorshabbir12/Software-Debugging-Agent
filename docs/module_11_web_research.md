# Module 11: External Documentation & Web Research

This module addresses the agent's limitation when debugging issues caused by external factors (e.g., third-party library updates, unexpected API responses, or framework bugs).

## Concepts Learned

### 1. Web Search Integration (`duckduckgo-search`)
**What it is:** A tool that programmatically queries the DuckDuckGo search engine to find relevant URLs and snippets for a given query, returning them in a structured JSON format.
**What problem it solves:** When the local repository lacks the answer (e.g., "Why does FastAPI throw a `ValidationError` on startup in v0.100?"), the agent can search the web for GitHub issues or changelogs.
**Why we used it here:** We chose `duckduckgo-search` over commercial APIs (like Tavily or SerpAPI) because it is free, requires no API keys, and is immediately runnable by anyone using this sandbox. It is the lowest-friction way to add web search capabilities.
**Where it lives:** The `web_search` tool is implemented in `sandbox/web_tools.py`.

### 2. Web Scraping (`BeautifulSoup`)
**What it is:** A Python library for pulling data out of HTML and XML files. It creates parse trees that are helpful to extract readable text.
**What problem it solves:** Search results only give us tiny text snippets. To deeply understand a GitHub issue or documentation page, the agent must read the whole page. `BeautifulSoup` strips out the `<script>`, `<style>`, and HTML tags, returning just the raw text content for the LLM to read.
**Where it lives:** The `fetch_webpage` tool in `sandbox/web_tools.py`.

## Important Decisions & Output Management
Webpages can be massive and easily overflow the LLM's context window. 
- **Decision:** We implemented a hard truncation limit (`max_chars = 15000`) in `fetch_webpage`. If a page exceeds this, the agent is notified that the content was truncated. 
- **Recommendation:** This is a blunt instrument. A more robust approach for a production agent would be to pipe the scraped webpage text through our RAG chunker (Module 2) and let the agent query the page semantically, but truncation is sufficient for this sandbox stage.

## Transferable Rules
> **Use Web Search tools when:** Your agent needs to cross-reference local findings with external reality (e.g., checking standard documentation, error code definitions, or open-source bug trackers).
> 
> **Avoid/reconsider when:** The agent is dealing purely with internal proprietary business logic where the web has zero relevant context. Searching the web for internal issues wastes time and tokens.
