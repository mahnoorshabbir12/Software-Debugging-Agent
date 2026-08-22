from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.agents.triage import TriageAgent, InvestigationRequest
from backend.agents.hypothesis import HypothesisAgent, Hypothesis
from backend.agents.evidence import EvidenceGraph, Evaluation
from backend.agents.patch import PatchAgent, FilePatch
from backend.validator import Validator, ValidationResult

class SupervisorState(TypedDict):
    """
    The unified state that holds the context across all sub-agents.
    """
    bug_report: str
    project_root: str
    triage_request: Optional[InvestigationRequest]
    hypotheses: List[Hypothesis]
    current_hypothesis_index: int
    final_root_cause: Optional[Evaluation]
    
    # Patch and Validation state
    patches: List[FilePatch]
    patch_attempts: int
    validation_failures: List[str]
    validation_result: Optional[ValidationResult]


class SupervisorGraph:
    """
    The Orchestrator agent that acts as a 'Graph of Graphs'.
    """
    def __init__(self, checkpointer=None):
        self.triage_agent = TriageAgent()
        self.hypothesis_agent = HypothesisAgent()
        self.evidence_graph = EvidenceGraph()
        self.patch_agent = PatchAgent()
        
        self.memory = checkpointer or MemorySaver()
        self.app = self._build_graph()
        
    def _triage_node(self, state: SupervisorState) -> dict:
        request = self.triage_agent.triage(state["bug_report"])
        return {"triage_request": request, "patch_attempts": 0, "validation_failures": []}
        
    def _hypothesis_node(self, state: SupervisorState) -> dict:
        hypo_list = self.hypothesis_agent.generate_hypotheses(state["triage_request"])
        return {
            "hypotheses": hypo_list.hypotheses,
            "current_hypothesis_index": 0
        }
        
    def _investigate_node(self, state: SupervisorState) -> dict:
        idx = state.get("current_hypothesis_index", 0)
        hypotheses = state.get("hypotheses", [])
        
        if idx >= len(hypotheses):
            return {}
            
        current_hypo = hypotheses[idx]
        
        subgraph_thread = f"supervisor_thread_{idx}"
        evidence_state = self.evidence_graph.run(current_hypo, thread_id=subgraph_thread)
        
        snapshot = self.evidence_graph.app.get_state({"configurable": {"thread_id": subgraph_thread}})
        if snapshot.next:
            from langgraph.errors import NodeInterrupt
            raise NodeInterrupt("Child graph paused waiting for tools")
        
        eval_result = evidence_state.get("evaluation")
        
        if eval_result and eval_result.status == "SUPPORTED":
            return {"final_root_cause": eval_result, "patch_attempts": 0, "validation_failures": []}
        
        return {"current_hypothesis_index": idx + 1}
        
    def _patch_node(self, state: SupervisorState) -> dict:
        """Generates a patch based on the confirmed root cause."""
        # Get the history from the evidence graph
        idx = state.get("current_hypothesis_index", 0)
        subgraph_thread = f"supervisor_thread_{idx}"
        
        # We fetch the full history from the subgraph to give the Patch agent context
        evidence_state = self.evidence_graph.app.get_state({"configurable": {"thread_id": subgraph_thread}}).values
        history_messages = evidence_state.get("messages", [])
        
        patch_response = self.patch_agent.generate_patch(
            request=state["triage_request"],
            root_cause=state["final_root_cause"],
            history_messages=history_messages,
            previous_failures=state.get("validation_failures", [])
        )
        
        attempts = state.get("patch_attempts", 0) + 1
        return {"patches": patch_response.patches, "patch_attempts": attempts}
        
    def _validate_node(self, state: SupervisorState) -> dict:
        """Validates the generated patch."""
        validator = Validator(project_root=state["project_root"])
        result = validator.validate_patch(state["patches"])
        
        failures = state.get("validation_failures", [])
        if not result.passed:
            failure_msg = f"Details: {result.details}\nLint Output: {result.lint_output}\nType Output: {result.type_output}\nTest Output: {result.test_output}"
            failures = failures + [failure_msg]
            
        return {"validation_result": result, "validation_failures": failures}

    def _route_investigation(self, state: SupervisorState) -> str:
        if state.get("final_root_cause") is not None:
            return "patch"
            
        idx = state.get("current_hypothesis_index", 0)
        if idx >= len(state.get("hypotheses", [])):
            return END 
            
        return "investigate"
        
    def _route_validation(self, state: SupervisorState) -> str:
        result = state.get("validation_result")
        if result and result.passed:
            return END
            
        attempts = state.get("patch_attempts", 0)
        if attempts >= 3:
            # We failed to patch 3 times. We discard this hypothesis and move to the next.
            return "discard_hypothesis"
            
        return "patch"
        
    def _discard_hypothesis_node(self, state: SupervisorState) -> dict:
        """If patching fails 3 times, we give up on this hypothesis and move to the next."""
        idx = state.get("current_hypothesis_index", 0)
        return {
            "final_root_cause": None, # Reset root cause
            "current_hypothesis_index": idx + 1,
            "patch_attempts": 0,
            "validation_failures": []
        }

    def _build_graph(self):
        workflow = StateGraph(SupervisorState)
        
        workflow.add_node("triage", self._triage_node)
        workflow.add_node("hypothesis", self._hypothesis_node)
        workflow.add_node("investigate", self._investigate_node)
        workflow.add_node("patch", self._patch_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("discard_hypothesis", self._discard_hypothesis_node)
        
        workflow.set_entry_point("triage")
        workflow.add_edge("triage", "hypothesis")
        workflow.add_edge("hypothesis", "investigate")
        
        workflow.add_conditional_edges(
            "investigate",
            self._route_investigation,
            {
                END: END,
                "investigate": "investigate",
                "patch": "patch"
            }
        )
        
        workflow.add_edge("patch", "validate")
        
        workflow.add_conditional_edges(
            "validate",
            self._route_validation,
            {
                END: END,
                "patch": "patch",
                "discard_hypothesis": "discard_hypothesis"
            }
        )
        
        workflow.add_edge("discard_hypothesis", "investigate")
        
        return workflow.compile(checkpointer=self.memory)
        
    def run(self, bug_report: str, project_root: str, thread_id: str = "default_supervisor") -> dict:
        config = {"configurable": {"thread_id": thread_id}}
        return self.app.invoke({"bug_report": bug_report, "project_root": project_root}, config=config)
