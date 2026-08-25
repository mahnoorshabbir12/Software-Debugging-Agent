import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage
from backend.agents.hypothesis import Hypothesis
from backend.agents.evidence import EvidenceGraph, EvidenceState

@pytest.fixture
def hypothesis():
    return Hypothesis(
        title="Database lock issue",
        description="The app freezes when saving a user.",
        reason="Might be a lock contention.",
        expected_evidence=["A long running transaction in save_user"],
        investigation_plan=["Search for save_user", "Check git history for recent changes to save_user"]
    )

@patch("backend.agents.evidence.build_llm")
def test_orchestrator_routes_to_code_agent(mock_build_llm, hypothesis):
    # Mock the LLM
    mock_llm = MagicMock()
    mock_build_llm.return_value = mock_llm
    
    # Mock the Orchestrator Decision
    mock_orchestrator_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_orchestrator_llm
    
    # Configure it to route to CodeAgent
    from backend.agents.evidence import OrchestratorDecision
    mock_orchestrator_llm.invoke.return_value = OrchestratorDecision(
        reasoning="I need to see the code for save_user.",
        next_agent="CodeAgent",
        instructions_for_agent="Find save_user in the codebase."
    )
    
    graph = EvidenceGraph()
    
    # Call the orchestrator node directly to test its routing output
    state: EvidenceState = {
        "hypothesis": hypothesis,
        "messages": [],
        "loop_count": 0,
        "next_agent": "",
        "evaluation": None
    }
    
    updates = graph._orchestrator_node(state)
    
    assert updates["next_agent"] == "CodeAgent"
    assert updates["loop_count"] == 1
    # Check if instructions were appended
    assert len(updates["messages"]) == 1
    assert "Find save_user" in updates["messages"][0].content
    assert "[CodeAgent]" in updates["messages"][0].content

@patch("backend.agents.evidence.build_llm")
def test_orchestrator_routes_to_git_agent(mock_build_llm, hypothesis):
    mock_llm = MagicMock()
    mock_build_llm.return_value = mock_llm
    
    mock_orchestrator_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_orchestrator_llm
    
    from backend.agents.evidence import OrchestratorDecision
    mock_orchestrator_llm.invoke.return_value = OrchestratorDecision(
        reasoning="I need to check git history.",
        next_agent="GitAgent",
        instructions_for_agent="Check git blame for save_user."
    )
    
    graph = EvidenceGraph()
    state: EvidenceState = {
        "hypothesis": hypothesis,
        "messages": [],
        "loop_count": 0,
        "next_agent": "",
        "evaluation": None
    }
    
    updates = graph._orchestrator_node(state)
    
    assert updates["next_agent"] == "GitAgent"
    assert updates["loop_count"] == 1

@patch("backend.agents.evidence.build_llm")
def test_orchestrator_loop_limit(mock_build_llm, hypothesis):
    mock_llm = MagicMock()
    mock_build_llm.return_value = mock_llm
    
    mock_orchestrator_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_orchestrator_llm
    
    # Even if it wants to keep delegating...
    from backend.agents.evidence import OrchestratorDecision
    mock_orchestrator_llm.invoke.return_value = OrchestratorDecision(
        reasoning="I still need to check stuff.",
        next_agent="ResearchAgent",
        instructions_for_agent="Keep searching."
    )
    
    graph = EvidenceGraph()
    state: EvidenceState = {
        "hypothesis": hypothesis,
        "messages": [],
        "loop_count": 4, # Max is 5, so this will trigger the cutoff (4+1=5)
        "next_agent": "",
        "evaluation": None
    }
    
    updates = graph._orchestrator_node(state)
    
    # Should force evaluate
    assert updates["next_agent"] == "evaluate"
    assert updates["loop_count"] == 5
