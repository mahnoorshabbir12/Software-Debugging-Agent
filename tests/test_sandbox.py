import os
import pytest
from backend.sandbox import DockerSandbox

@pytest.fixture
def dummy_project(tmp_path):
    # Create a small python script
    code = tmp_path / "hello.py"
    code.write_text('print("Hello from sandbox!")', encoding="utf-8")
    return str(tmp_path)

def test_sandbox_execution(dummy_project):
    with DockerSandbox() as sandbox:
        sandbox.create_sandbox(dummy_project)
        
        # Test safe execution
        exit_code, output = sandbox.run_command("python hello.py")
        assert exit_code == 0
        assert "Hello from sandbox!" in output

def test_sandbox_network_isolation(dummy_project):
    with DockerSandbox() as sandbox:
        sandbox.create_sandbox(dummy_project)
        
        # Test that network is disabled (curl should fail)
        exit_code, output = sandbox.run_command("curl -I https://google.com")
        assert exit_code != 0
        assert "Could not resolve host" in output or "timeout" in output or "curl: command not found" in output
        # If curl isn't installed in the slim image, it will exit != 0 anyway, but let's test ping
        exit_code, output = sandbox.run_command("ping -c 1 8.8.8.8")
        assert exit_code != 0

def test_sandbox_timeout(dummy_project):
    with DockerSandbox() as sandbox:
        sandbox.create_sandbox(dummy_project)
        
        # Run a command that sleeps longer than the timeout
        exit_code, output = sandbox.run_command("sleep 10", timeout=2)
        # The `timeout` command in alpine/debian exits with 143 (SIGTERM) or 124 when it kills a process
        assert exit_code in (124, 143, 137)
