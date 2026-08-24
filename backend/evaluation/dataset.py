import os
from langsmith import Client

# A small set of synthetic bugs for evaluating the agent
BUGS = [
    {
        "inputs": {
            "bug_report": "The application returns a 500 Internal Server Error when trying to fetch the /observability/overview endpoint because the database table 'spanevent' is missing some columns during the query.",
            "project_root": os.path.abspath(".")
        },
        "outputs": {
            "expected_files": ["backend/observability/store.py", "backend/database/models.py"],
            "expected_root_cause_keywords": ["SpanEvent", "overview", "SQL", "column"]
        }
    },
    {
        "inputs": {
            "bug_report": "The triage agent is failing to parse the InvestigationRequest properly when the bug report is extremely short.",
            "project_root": os.path.abspath(".")
        },
        "outputs": {
            "expected_files": ["backend/agents/triage.py"],
            "expected_root_cause_keywords": ["InvestigationRequest", "pydantic", "validation", "short"]
        }
    }
]

def ensure_dataset(dataset_name: str = "Debugger Benchmark") -> str:
    """Creates or updates the benchmark dataset in LangSmith."""
    client = Client()
    
    if client.has_dataset(dataset_name=dataset_name):
        print(f"Dataset '{dataset_name}' already exists. Deleting to recreate with fresh examples...")
        client.delete_dataset(dataset_name=dataset_name)
        
    print(f"Creating dataset '{dataset_name}'...")
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="A benchmark of known bugs for testing the autonomous debugger's retrieval and reasoning."
    )
    
    inputs = [b["inputs"] for b in BUGS]
    outputs = [b["outputs"] for b in BUGS]
    
    client.create_examples(
        inputs=inputs,
        outputs=outputs,
        dataset_id=dataset.id,
    )
    print(f"Added {len(BUGS)} examples to '{dataset_name}'.")
    return dataset_name

if __name__ == "__main__":
    ensure_dataset()
