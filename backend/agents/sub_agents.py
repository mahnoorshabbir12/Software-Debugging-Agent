from sandbox.tools import (
    read_file, list_files, search_code,
    git_log, git_diff, git_show, git_blame, search_commits,
    get_repository_map
)
from sandbox.web_tools import web_search, fetch_webpage
from sandbox.graph_tools import get_function_callers, get_function_dependencies, get_file_imports
from langchain_core.messages import SystemMessage

CODE_AGENT_TOOLS = [
    read_file,
    list_files,
    search_code,
    get_repository_map,
    get_function_callers,
    get_function_dependencies,
    get_file_imports
]

GIT_AGENT_TOOLS = [
    git_log,
    git_diff,
    git_show,
    git_blame,
    search_commits
]

RESEARCH_AGENT_TOOLS = [
    web_search,
    fetch_webpage
]

def get_code_agent_prompt() -> SystemMessage:
    return SystemMessage(content="""You are the Code Agent.
Your job is to navigate the codebase using your file and graph tools.
You can read files, search for code patterns, and use the Code Graph tools to trace dependencies and callers.
Answer the orchestrator's request concisely with facts and evidence found in the code.
IMPORTANT: When you find relevant buggy code, you MUST include the exact, unmodified code snippet in your final response. The downstream patch agent relies on this snippet to generate exact search-and-replace patches.""")

def get_git_agent_prompt() -> SystemMessage:
    return SystemMessage(content="""You are the Git Agent.
Your job is to explore the git history to understand why code changed.
Use your git tools to find relevant commits, view diffs, or blame lines.
Answer the orchestrator's request concisely with facts found in the git history.
""")

def get_research_agent_prompt() -> SystemMessage:
    return SystemMessage(content="""You are the Research Agent.
Your job is to research external information using web search and fetching webpages.
This is useful for looking up documentation, GitHub issues, or external dependencies.
Answer the orchestrator's request concisely with facts found on the web.
""")
