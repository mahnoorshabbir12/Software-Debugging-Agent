from sandbox.tools import git_log, git_diff, git_show, git_blame, search_commits

def test_git_log():
    res = git_log.invoke({"path": ".", "max_count": 2, "project_root": "."})
    assert isinstance(res, str)
    assert len(res) > 0

def test_git_diff():
    res = git_diff.invoke({"path": ".", "file_path": "sandbox/tools.py", "project_root": "."})
    assert isinstance(res, str)

def test_git_show():
    # We can just get the latest commit and pass it
    log_res = git_log.invoke({"path": ".", "max_count": 1, "project_root": "."})
    if log_res and not log_res.startswith("Error") and not log_res.startswith("Git error"):
        latest_commit = log_res.split()[0]
        res = git_show.invoke({"commit_hash": latest_commit, "path": ".", "project_root": "."})
        assert isinstance(res, str)
        assert latest_commit in res

def test_git_blame():
    res = git_blame.invoke({"file_path": "sandbox/tools.py", "path": ".", "project_root": "."})
    assert isinstance(res, str)

def test_search_commits():
    res = search_commits.invoke({"query": "module", "path": ".", "project_root": "."})
    assert isinstance(res, str)
