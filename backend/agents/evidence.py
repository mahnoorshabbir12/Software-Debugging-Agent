import os
from typing import TypedDict, Annotated, List, Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from backend.agents.hypothesis import Hypothesis
from sandbox.tools import AGENT_TOOLS

class Evaluation(BaseModel):
    """
    Structured grading of a hypothesis based on collected evidence.
    """
    status: Literal["SUPPORTED", "REJECTED", "UNCERTAIN"] = Field(description="The final verdict on the hypothesis")
    confidence_score: int = Field(ge=0, le=100, description="Confidence in the verdict from 0 to 100")
    supporting_evidence: List[str] = Field(description="List of specific facts found that support the hypothesis")
    contradicting_evidence: List[str] = Field(description="List of specific facts found that disprove the hypothesis")

class EvidenceState(TypedDict):
    hypothesis: Hypothesis
    messages: Annotated[list, add_messages]
    evaluation: Evaluation
    loop_count: int

class EvidenceGraph:
    """
    A LangGraph that takes a Hypothesis, uses tools to search the codebase for evidence,
    and returns a structured Evaluation.
    """
    def __init__(self, model_name: str = "meta-llama/llama-3.1-8b-instruct"):
        self.llm = ChatOpenAI(
            model=model_name,
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            temperature=0
        )
        
        # Bind the hybrid search tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(AGENT_TOOLS)
        
        # We also need an LLM specifically bound to our Evaluation schema for the final step
        self.llm_evaluator = self.llm.with_structured_output(Evaluation)
        
        self.memory = MemorySaver()
        self.app = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(EvidenceState)
        
        # 1. Add Nodes
        workflow.add_node("investigate", self._investigate_node)
        workflow.add_node("tools", ToolNode(AGENT_TOOLS))
        workflow.add_node("evaluate", self._evaluate_node)
        
        # 2. Add Edges
        workflow.set_entry_point("investigate")
        
        # 3. Add Conditional Edge: 
        # If the LLM called a tool, go to 'tools'. If it didn't, go to 'evaluate' (or if we looped too much)
        workflow.add_conditional_edges("investigate", self._should_continue)
        
        # After tools run, go back to investigate
        workflow.add_edge("tools", "investigate")
        
        # Evaluate is the end
        workflow.add_edge("evaluate", END)
        
        # Compile with checkpointer and interrupt before executing tools
        return workflow.compile(checkpointer=self.memory, interrupt_before=["tools"])
        
    def _investigate_node(self, state: EvidenceState):
        """
        The LLM decides whether to call a tool to gather evidence or stop.
        """
        # Inject system prompt if it's the first message
        if not state.get("messages"):
            sys_msg = SystemMessage(content=f"""You are an Evidence Gathering Agent.
Your job is to execute the following Investigation Plan to find Expected Evidence in the codebase.
Use your tools to search the code.
If you cannot find the answer in the local codebase or git history, use `web_search` and `fetch_webpage` to check external documentation or GitHub issues.
If you have gathered enough information, or if you can't find anything after a few tries, DO NOT CALL ANY TOOLS.

Hypothesis: {state['hypothesis'].title}
Description: {state['hypothesis'].description}
Expected Evidence: {', '.join(state['hypothesis'].expected_evidence)}
Investigation Plan: {', '.join(state['hypothesis'].investigation_plan)}
""")
            # LLM invocation
            response = self.llm_with_tools.invoke([sys_msg, HumanMessage(content="Start your investigation.")])
            return {"messages": [sys_msg, HumanMessage(content="Start your investigation."), response], "loop_count": 1}
        
        # If we have messages, we just continue the conversation
        loop_count = state.get("loop_count", 1) + 1
        
        # Safety cutoff: if we looped 3 times, force the LLM to stop calling tools by stripping tools
        if loop_count >= 3:
            # Force it to just reply normally
            response = self.llm.invoke(state["messages"])
        else:
            response = self.llm_with_tools.invoke(state["messages"])
            
        return {"messages": [response], "loop_count": loop_count}

    def _should_continue(self, state: EvidenceState) -> Literal["tools", "evaluate"]:
        """
        Checks if the last message has tool calls.
        """
        last_message = state["messages"][-1]
        
        # If there are tool calls, go to the tools node
        if getattr(last_message, "tool_calls", None):
            # Safety limit
            if state.get("loop_count", 1) >= 3:
                return "evaluate"
            return "tools"
            
        # Otherwise, we are done investigating, evaluate the evidence
        return "evaluate"

    def _evaluate_node(self, state: EvidenceState):
        """
        Takes all the collected messages (which contain tool outputs) and forces an Evaluation out of it.
        """
        sys_msg = SystemMessage(content=f"""You are an Evaluation Agent.
Review the conversation history and tool outputs. Grade the hypothesis based on the evidence collected.
You MUST choose one of: SUPPORTED, REJECTED, UNCERTAIN.
If you didn't find strong evidence either way, choose UNCERTAIN. This is acceptable.

Hypothesis: {state['hypothesis'].title}
""")
        # We pass the conversation history to the structured evaluator
        eval_result = self.llm_evaluator.invoke([sys_msg] + state["messages"])
        return {"evaluation": eval_result}
        
    def run(self, hypothesis: Hypothesis, thread_id: str = "default_thread") -> EvidenceState:
        """
        Executes the graph for a single hypothesis.
        """
        config = {"configurable": {"thread_id": thread_id}}
        final_state = self.app.invoke({
            "hypothesis": hypothesis,
            "messages": [],
            "loop_count": 0
        }, config=config)
        return final_state
