from backend.agents.supervisor import SupervisorGraph
import traceback

def test_recursion_limit():
    supervisor = SupervisorGraph()
    
    print("Running Supervisor Graph with recursion_limit=1...")
    try:
        # Triage -> Hypothesis -> Investigate would take at least 3 steps.
        # A recursion limit of 1 should fail.
        supervisor.run(bug_report="Test bug", project_root=".", thread_id="test_recursion", recursion_limit=1)
        print("FAIL: Did not hit recursion limit.")
    except Exception as e:
        print(f"SUCCESS: Hit recursion limit as expected: {e.__class__.__name__}: {e}")

if __name__ == "__main__":
    test_recursion_limit()
