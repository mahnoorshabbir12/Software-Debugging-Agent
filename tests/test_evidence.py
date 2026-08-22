from backend.agents.evidence import Evaluation, EvidenceGraph
from backend.agents.hypothesis import Hypothesis

def test_evaluation_schema():
    """
    Test that the Pydantic schema for Evaluation correctly enforces allowed statuses.
    """
    eval_supported = Evaluation(
        status="SUPPORTED",
        confidence_score=90,
        supporting_evidence=["Found proof X"],
        contradicting_evidence=[]
    )
    assert eval_supported.status == "SUPPORTED"
    
    eval_rejected = Evaluation(
        status="REJECTED",
        confidence_score=95,
        supporting_evidence=[],
        contradicting_evidence=["Found proof Y"]
    )
    assert eval_rejected.status == "REJECTED"
    
    eval_uncertain = Evaluation(
        status="UNCERTAIN",
        confidence_score=50,
        supporting_evidence=["Might be X"],
        contradicting_evidence=["But also Y"]
    )
    assert eval_uncertain.status == "UNCERTAIN"

def test_evidence_graph_initialization():
    """
    Test that the EvidenceGraph initializes correctly.
    """
    import os
    original = os.environ.get("OPENROUTER_API_KEY")
    os.environ["OPENROUTER_API_KEY"] = "test_key"
    
    try:
        graph = EvidenceGraph()
        assert graph.app is not None
    finally:
        if original:
            os.environ["OPENROUTER_API_KEY"] = original
        else:
            del os.environ["OPENROUTER_API_KEY"]

def test_evidence_graph_memory():
    """
    Test that EvidenceGraph uses MemorySaver for persistent state tracking.
    """
    import os
    from langgraph.checkpoint.memory import MemorySaver
    
    original = os.environ.get("OPENROUTER_API_KEY")
    os.environ["OPENROUTER_API_KEY"] = "test_key"
    
    try:
        graph = EvidenceGraph()
        assert hasattr(graph, "memory")
        assert isinstance(graph.memory, MemorySaver)
        
        # Test if it runs without crashing by instantiating the graph
        assert graph.app is not None
    finally:
        if original:
            os.environ["OPENROUTER_API_KEY"] = original
        else:
            if "OPENROUTER_API_KEY" in os.environ:
                del os.environ["OPENROUTER_API_KEY"]
