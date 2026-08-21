from langgraph.graph import StateGraph, END
from sandbox.graph_experiments import GraphState, analyze_question, run_search, evaluate_information, generate_answer

def test_langgraph_compilation():
    """
    Test that the LangGraph StateGraph compiles successfully
    and the edges are properly formed.
    """
    workflow = StateGraph(GraphState)
    
    workflow.add_node("analyze", analyze_question)
    workflow.add_node("search", run_search)
    workflow.add_node("answer", generate_answer)
    
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "search")
    
    workflow.add_conditional_edges(
        "search",
        evaluate_information,
        {
            "yes": "answer",
            "no": "search",
            "max_loops": "answer"
        }
    )
    workflow.add_edge("answer", END)
    
    # This will fail if nodes/edges are disconnected or invalid
    app = workflow.compile()
    
    assert app is not None
