import os
from langsmith import evaluate
from backend.agents.supervisor import SupervisorGraph
from backend.llm import traced_config
from backend.evaluation.evaluators import recall_evaluator, reasoning_evaluator, patch_evaluator

def target_graph(inputs: dict) -> dict:
    """
    The target function that LangSmith will evaluate.
    It takes dataset inputs and returns the final agent state/outputs.
    """
    bug_report = inputs.get("bug_report", "")
    project_root = inputs.get("project_root", os.path.abspath("."))
    
    # Initialize the graph
    graph = SupervisorGraph()
    
    # We generate a unique thread ID so memory checkpoints don't collide during concurrent evaluation
    thread_id = f"eval_{os.urandom(4).hex()}"
    config = traced_config({"configurable": {"thread_id": thread_id}})
    
    # Run the graph
    print(f"Starting investigation for bug: {bug_report[:50]}...")
    
    # We invoke it fully to get the final state
    # In a real heavy evaluation, you might want a timeout or graph limits
    final_state = graph.app.invoke(
        {"bug_report": bug_report, "project_root": project_root}, 
        config=config
    )
    
    return final_state

def run_evaluation(dataset_name: str = "Debugger Benchmark", experiment_prefix: str = "debugger-eval"):
    """
    Runs the evaluation on the specified dataset using LangSmith.
    """
    print(f"Starting evaluation on dataset: {dataset_name}")
    
    # The evaluate() function handles fetching dataset examples, running the target function concurrently,
    # and passing the traces/results to the evaluators.
    results = evaluate(
        target_graph,
        data=dataset_name,
        evaluators=[
            recall_evaluator,
            reasoning_evaluator,
            patch_evaluator
        ],
        experiment_prefix=experiment_prefix,
        # max_concurrency=2 # Keep it low so we don't overwhelm OpenRouter or local resources
    )
    
    print("\nEvaluation launched! Check the LangSmith UI for detailed trace results.")
    return results

if __name__ == "__main__":
    run_evaluation()
