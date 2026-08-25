import os
import subprocess
from typing import Annotated
from langchain_core.tools import tool, InjectedToolArg
from github import Github

@tool
def create_pull_request(
    branch_name: str,
    title: str,
    body: str,
    target_repo: str,
    project_root: Annotated[str, InjectedToolArg]
) -> str:
    """
    Pushes the current branch to the remote repository and creates a Pull Request on GitHub.
    You must already be on the branch and have committed your changes before calling this tool.
    """
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token or not target_repo:
        return "<file_content>\nError: GITHUB_TOKEN environment variable or target_repo is not set.\n</file_content>"
        
    try:
        # First push the branch to remote
        # We assume 'origin' is the remote name
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if push_result.returncode != 0:
            return f"<file_content>\nError pushing branch to remote:\n{push_result.stderr}\n</file_content>"
            
        # Now create the PR via PyGithub
        g = Github(token)
        repo = g.get_repo(target_repo)
        
        # We assume we want to merge into main or master
        # Let's get the default branch of the repo
        base_branch = repo.default_branch
        
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base=base_branch
        )
        
        return f"<file_content>\nSuccessfully created Pull Request!\nURL: {pr.html_url}\n</file_content>"
        
    except Exception as e:
        return f"<file_content>\nError creating Pull Request: {e}\n</file_content>"
