import pytest
from langgraph.errors import NodeInterrupt
from backend.agents.supervisor import SupervisorGraph, SupervisorState
from backend.agents.hypothesis import Hypothesis
from backend.agents.evidence import Evaluation

# A mock EvidenceGraph that always pauses (simulating an interrupt)
class MockEvidenceGraphPaused:
    class MockApp:
        def get_state(self, config):
            class MockState:
                next = ["tools"] # Indicates it is paused and has next nodes
            return MockState()
            
    def __init__(self):
        self.app = self.MockApp()
        
    def run(self, hypothesis: Hypothesis, thread_id: str = "default_thread"):
        # Returns empty dict since it's paused
        return {}

def test_supervisor_raises_node_interrupt_on_subgraph_pause():
    import os
    os.environ["OPENROUTER_API_KEY"] = "dummy_test_key"
    
    supervisor = SupervisorGraph()
    
    # Inject our mock
    supervisor.evidence_graph = MockEvidenceGraphPaused()
    
    # Construct a dummy state
    hypo = Hypothesis(
        title="Test",
        description="Test desc",
        reason="Test reason",
        expected_evidence=["evidence 1"],
        investigation_plan=["step 1"]
    )
    
    state: SupervisorState = {
        "bug_report": "test",
        "triage_request": None,
        "hypotheses": [hypo],
        "current_hypothesis_index": 0,
        "final_root_cause": None
    }
    
    # When we run investigate, it should raise a NodeInterrupt
    with pytest.raises(NodeInterrupt, match="Child graph paused waiting for tools"):
        supervisor._investigate_node(state)
