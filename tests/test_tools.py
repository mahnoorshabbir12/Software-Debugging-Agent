from sandbox.tools import get_repository_map, search_code, read_file, list_files
import os

def test_get_repository_map():
    # Use current directory
    res = get_repository_map.invoke({"path": "."})
    assert isinstance(res, str)
    assert "language" in res.lower()
    
def test_search_code():
    res = search_code.invoke({"query": "RepositoryAnalyzer", "path": ".", "top_k": 1})
    assert isinstance(res, str)
    # The JSON string should contain 'RepositoryAnalyzer'
    assert "RepositoryAnalyzer" in res

def test_read_file():
    # Write a temporary file just to test read_file tool logic
    test_file = "test_file.txt"
    with open(test_file, "w") as f:
        f.write("Line 1\nLine 2\nLine 3\nLine 4\n")
    
    try:
        res = read_file.invoke({"file_path": test_file, "start_line": 2, "end_line": 3})
        assert "2: Line 2" in res
        assert "3: Line 3" in res
        assert "1:" not in res
        assert "4:" not in res
    finally:
        os.remove(test_file)

def test_list_files():
    res = list_files.invoke({"directory_path": "."})
    assert isinstance(res, str)
    assert "pyproject.toml" in res
