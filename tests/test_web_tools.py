from sandbox.web_tools import web_search, fetch_webpage

def test_web_search():
    res = web_search.invoke({"query": "fastapi documentation", "max_results": 2})
    assert isinstance(res, str)
    # Check that it returns a JSON array
    assert res.strip().startswith("[")
    assert res.strip().endswith("]")
    
def test_fetch_webpage():
    # Fetching a simple robust page like example.com
    res = fetch_webpage.invoke({"url": "http://example.com"})
    assert isinstance(res, str)
    assert "Example Domain" in res
