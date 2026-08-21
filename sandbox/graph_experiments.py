import os
from typing import TypedDict, Annotated, List, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END

# Import our tools
from sandbox.tools import search_code

# ==============================================================================
# 1. State Definition
# ==============================================================================
# In LangGraph, we define a TypedDict that holds the state of our agent across nodes.
class GraphState(TypedDict):
    question: str
    search_results: str
    loop_count: int
    answer: str

# ==============================================================================
# 2. Node Functions
# ==============================================================================
# Each function represents a "Node" in the graph. It takes the state, modifies it,
# and returns the updated state fields.

def analyze_question(state: GraphState):
    """Initial node: prepares the state for the loop."""
    print("--- NODE: Analyze Question ---")
    return {"loop_count": 0, "search_results": ""}

def run_search(state: GraphState):
    """Executes a search using our tool."""
    print(f"--- NODE: Search (Loop {state.get('loop_count')}) ---")
    # For this experiment, we just run the search tool.
    query = state["question"]
    # We add the loop count to the query just to simulate expanding the search if it fails
    if state.get("loop_count", 0) > 0:
        query += " (expanded search)"
    
    # We call the python function directly
    results = search_code.invoke({"query": query, "path": ".", "top_k": 3})
    
    return {
        "search_results": results, 
        "loop_count": state.get("loop_count", 0) + 1
    }

def evaluate_information(state: GraphState) -> Literal["yes", "no", "max_loops"]:
    """Conditional Edge: Decides if we have enough info, or need to loop again."""
    print("--- EDGE: Evaluate Information ---")
    
    # Safety mechanism to prevent infinite loops
    if state.get("loop_count", 0) >= 2:
        print("  -> Max loops reached. Forcing Answer.")
        return "max_loops"
        
    llm = ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct", 
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        temperature=0
    )
    prompt = f"""
    Question: {state['question']}
    Search Results: {state['search_results']}
    
    Are the search results sufficient to answer the question?
    Reply with ONLY the word "yes" or "no".
    """
    
    try:
        response = llm.invoke(prompt)
        decision = response.content.strip().lower()
        print(f"  -> LLM decided: {decision}")
        
        if "yes" in decision:
            return "yes"
        return "no"
    except Exception as e:
        print(f"  -> LLM error ({e}). Defaulting to yes to break loop.")
        return "yes"

def generate_answer(state: GraphState):
    """Final node: Generates the answer."""
    print("--- NODE: Generate Answer ---")
    llm = ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct", 
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        temperature=0
    )
    prompt = f"Answer the question based on these results:\n\nQuestion: {state['question']}\n\nResults: {state['search_results']}"
    
    try:
        response = llm.invoke(prompt)
        return {"answer": response.content}
    except Exception as e:
        return {"answer": f"Error generating answer: {e}"}

# ==============================================================================
# 3. Standard Python Implementation (Why it fails)
# ==============================================================================
def run_python_loop(question: str):
    """
    Standard Python while-loop implementation.
    If this crashes in the middle, the entire state is lost.
    """
    print("\n\n" + "="*50)
    print("STARTING PYTHON LOOP EXPERIMENT")
    print("="*50)
    
    state: GraphState = {"question": question, "search_results": "", "loop_count": 0, "answer": ""}
    
    # 1. Analyze
    state.update(analyze_question(state))
    
    # 2. Loop
    while True:
        # Search
        state.update(run_search(state))
        
        # Evaluate
        decision = evaluate_information(state)
        
        if decision == "yes" or decision == "max_loops":
            break
            
    # 3. Answer
    state.update(generate_answer(state))
    print(f"\nFINAL ANSWER:\n{state['answer']}")
    return state

# ==============================================================================
# 4. LangGraph Implementation (The Solution)
# ==============================================================================
def run_langgraph_loop(question: str):
    """
    LangGraph StateGraph implementation.
    The graph manages state transitions, making it resilient, observable, and interruptible.
    """
    print("\n\n" + "="*50)
    print("STARTING LANGGRAPH EXPERIMENT")
    print("="*50)
    
    # 1. Initialize the Graph with our State definition
    workflow = StateGraph(GraphState)
    
    # 2. Add all Nodes
    workflow.add_node("analyze", analyze_question)
    workflow.add_node("search", run_search)
    workflow.add_node("answer", generate_answer)
    
    # 3. Define Edges (The flow)
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "search")
    
    # 4. Define Conditional Edges (The loops)
    # The output of 'evaluate_information' determines the next node.
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
    
    # 5. Compile the graph
    app = workflow.compile()
    
    # 6. Execute the graph
    final_state = app.invoke({"question": question, "search_results": "", "loop_count": 0, "answer": ""})
    print(f"\nFINAL ANSWER:\n{final_state.get('answer')}")
    return final_state

if __name__ == "__main__":
    # Test execution
    q = "Where is the RepositoryAnalyzer class defined?"
    run_python_loop(q)
    run_langgraph_loop(q)
