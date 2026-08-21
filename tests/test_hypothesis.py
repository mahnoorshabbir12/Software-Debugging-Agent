from backend.agents.hypothesis import Hypothesis, HypothesisList, HypothesisAgent
from backend.agents.triage import InvestigationRequest

def test_hypothesis_schema():
    """
    Test that the Pydantic schema for Hypotheses is correctly defined.
    """
    h = Hypothesis(
        title="Test Hypothesis",
        description="A description",
        reason="A reason",
        expected_evidence=["file.py has X"],
        investigation_plan=["check file.py"]
    )
    
    h_list = HypothesisList(hypotheses=[h])
    
    assert len(h_list.hypotheses) == 1
    assert h_list.hypotheses[0].title == "Test Hypothesis"
    assert h_list.hypotheses[0].expected_evidence[0] == "file.py has X"

def test_hypothesis_agent_initialization():
    """
    Test that the HypothesisAgent initializes without errors.
    """
    import os
    original = os.environ.get("OPENROUTER_API_KEY")
    os.environ["OPENROUTER_API_KEY"] = "test_key"
    
    try:
        agent = HypothesisAgent()
        assert agent.llm is not None
        assert agent.structured_llm is not None
    finally:
        if original:
            os.environ["OPENROUTER_API_KEY"] = original
        else:
            del os.environ["OPENROUTER_API_KEY"]
