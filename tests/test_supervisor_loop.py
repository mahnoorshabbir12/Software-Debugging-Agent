import pytest
from langgraph.graph import StateGraph

from backend.agents.supervisor import SupervisorGraph, SupervisorState

def test_supervisor_compiles():
    supervisor = SupervisorGraph()
    # If it compiles without error, the graph is structurally sound
    assert supervisor.app is not None

def test_supervisor_edges():
    # Verify the routing logic manually
    supervisor = SupervisorGraph()
    
    # Test _route_investigation
    state: SupervisorState = {
        "bug_report": "",
        "project_root": "",
        "triage_request": None,
        "hypotheses": [{}, {}], # 2 hypotheses
        "current_hypothesis_index": 0,
        "final_root_cause": None,
        "patches": [],
        "patch_attempts": 0,
        "validation_failures": [],
        "validation_result": None
    }
    
    # If no root cause, should loop to investigate
    assert supervisor._route_investigation(state) == "investigate"
    
    # If out of hypotheses, END
    state["current_hypothesis_index"] = 2
    from langgraph.graph import END
    assert supervisor._route_investigation(state) == END
    
    # If root cause found, go to patch
    state["current_hypothesis_index"] = 0
    from backend.agents.evidence import Evaluation
    state["final_root_cause"] = Evaluation(status="SUPPORTED", supporting_evidence=[])
    assert supervisor._route_investigation(state) == "patch"

def test_supervisor_validation_routing():
    supervisor = SupervisorGraph()
    
    from backend.validator import ValidationResult
    state: SupervisorState = {
        "bug_report": "",
        "project_root": "",
        "triage_request": None,
        "hypotheses": [],
        "current_hypothesis_index": 0,
        "final_root_cause": None,
        "patches": [],
        "patch_attempts": 1,
        "validation_failures": [],
        "validation_result": ValidationResult(passed=False, details="failed")
    }
    
    # Failed, attempts=1 -> retry patch
    assert supervisor._route_validation(state) == "patch"
    
    # Failed, attempts=3 -> discard hypothesis
    state["patch_attempts"] = 3
    assert supervisor._route_validation(state) == "discard_hypothesis"
    
    # Passed -> END
    state["validation_result"] = ValidationResult(passed=True, details="passed")
    from langgraph.graph import END
    assert supervisor._route_validation(state) == END
