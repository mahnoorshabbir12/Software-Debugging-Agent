from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.agents.triage import TriageAgent, InvestigationRequest
from backend.agents.hypothesis import HypothesisAgent, Hypothesis
from backend.agents.evidence import EvidenceGraph, Evaluation

class SupervisorState(TypedDict):
    """
    The unified state that holds the context across all sub-agents.
    """
    bug_report: str
    triage_request: Optional[InvestigationRequest]
    hypotheses: List[Hypothesis]
    current_hypothesis_index: int
    final_root_cause: Optional[Evaluation]

class SupervisorGraph:
    """
    The Orchestrator agent that acts as a 'Graph of Graphs'.
    It delegates work to Triage, Hypothesis, and Evidence agents, controlling the overall loop.
    """
    def __init__(self, checkpointer=None):
        self.triage_agent = TriageAgent()
        self.hypothesis_agent = HypothesisAgent()
        # We initialize the evidence graph here. It's an entire compiled graph itself!
        self.evidence_graph = EvidenceGraph()
        
        self.memory = checkpointer or MemorySaver()
        self.app = self._build_graph()
        
    def _triage_node(self, state: SupervisorState) -> dict:
        """Calls the TriageAgent to convert text into a structured request."""
        request = self.triage_agent.triage(state["bug_report"])
        return {"triage_request": request}
        
    def _hypothesis_node(self, state: SupervisorState) -> dict:
        """Calls the HypothesisAgent to brainstorm possible causes."""
        # We assume triage_request is not None because triage_node ran right before this
        hypo_list = self.hypothesis_agent.generate_hypotheses(state["triage_request"])
        return {
            "hypotheses": hypo_list.hypotheses,
            "current_hypothesis_index": 0
        }
        
    def _investigate_node(self, state: SupervisorState) -> dict:
        """
        Takes the current hypothesis and delegates the actual tool-calling investigation
        to the nested EvidenceGraph.
        """
        idx = state.get("current_hypothesis_index", 0)
        hypotheses = state.get("hypotheses", [])
        
        if idx >= len(hypotheses):
            return {}
            
        current_hypo = hypotheses[idx]
        
        # Invoke the SUB-GRAPH
        # We pass a composite thread_id so the subgraph's memory is namespaced properly
        # but is still isolated per hypothesis.
        subgraph_thread = f"supervisor_thread_{idx}"
        evidence_state = self.evidence_graph.run(current_hypo, thread_id=subgraph_thread)
        
        # Check if the child graph paused
        snapshot = self.evidence_graph.app.get_state({"configurable": {"thread_id": subgraph_thread}})
        if snapshot.next:
            from langgraph.errors import NodeInterrupt
            raise NodeInterrupt("Child graph paused waiting for tools")
        
        eval_result = evidence_state.get("evaluation")
        
        if eval_result and eval_result.status == "SUPPORTED":
            return {"final_root_cause": eval_result}
        
        # Otherwise, move to the next hypothesis
        return {"current_hypothesis_index": idx + 1}
        
    def _route_investigation(self, state: SupervisorState) -> str:
        """
        Determines whether to loop to the next hypothesis or end the process.
        """
        # If we found a supported root cause, stop!
        if state.get("final_root_cause") is not None:
            return END
            
        # If we ran out of hypotheses to check, stop!
        idx = state.get("current_hypothesis_index", 0)
        if idx >= len(state.get("hypotheses", [])):
            return END 
            
        # Otherwise, loop back to the investigate node for the next hypothesis
        return "investigate"

    def _build_graph(self):
        workflow = StateGraph(SupervisorState)
        
        workflow.add_node("triage", self._triage_node)
        workflow.add_node("hypothesis", self._hypothesis_node)
        workflow.add_node("investigate", self._investigate_node)
        
        workflow.set_entry_point("triage")
        workflow.add_edge("triage", "hypothesis")
        workflow.add_edge("hypothesis", "investigate")
        
        # The conditional edge creates the looping behavior
        workflow.add_conditional_edges(
            "investigate",
            self._route_investigation,
            {
                END: END,
                "investigate": "investigate"
            }
        )
        
        return workflow.compile(checkpointer=self.memory)
        
    def run(self, bug_report: str, thread_id: str = "default_supervisor") -> dict:
        """
        Executes the entire investigation pipeline.
        """
        config = {"configurable": {"thread_id": thread_id}}
        return self.app.invoke({"bug_report": bug_report}, config=config)
