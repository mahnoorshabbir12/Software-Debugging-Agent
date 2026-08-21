from backend.agents.triage import InvestigationRequest, TriageAgent

def test_investigation_request_schema():
    """
    Test that the Pydantic schema is correctly defined and accepts valid data.
    """
    req = InvestigationRequest(
        bug_type="runtime_error",
        affected_endpoint="/users",
        suspected_area="request_validation",
        observed_behavior="POST /users returns 500",
        expected_behavior="POST /users should return 201 Created",
        constraints=["Pydantic v2"]
    )
    
    assert req.bug_type == "runtime_error"
    assert req.affected_endpoint == "/users"
    assert "Pydantic v2" in req.constraints

def test_triage_agent_initialization():
    """
    Test that the TriageAgent initializes without throwing exceptions
    (e.g., ensures prompts and chains are properly constructed).
    """
    import os
    # Temporarily set API key so LangChain doesn't complain during init if it's missing
    original = os.environ.get("OPENROUTER_API_KEY")
    os.environ["OPENROUTER_API_KEY"] = "test_key"
    
    try:
        agent = TriageAgent()
        assert agent.llm is not None
        assert agent.structured_llm is not None
    finally:
        if original:
            os.environ["OPENROUTER_API_KEY"] = original
        else:
            del os.environ["OPENROUTER_API_KEY"]
