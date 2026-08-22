import os
import tempfile
import shutil
from typing import List, Dict, Any
from pydantic import BaseModel

from backend.agents.patch import FilePatch
from backend.patcher import apply_patches
from backend.sandbox import DockerSandbox

class ValidationResult(BaseModel):
    passed: bool
    details: str
    lint_output: str = ""
    type_output: str = ""
    test_output: str = ""

class Validator:
    """
    Takes a proposed patch, copies the project to a temp dir, applies the patch,
    and runs a full CI pipeline (Lint, Type Check, Tests) inside a Docker sandbox.
    """
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)

    def validate_patch(self, patches: List[FilePatch]) -> ValidationResult:
        # 1. Create a temporary directory and copy the project
        with tempfile.TemporaryDirectory() as temp_dir:
            # We copy the codebase to temp_dir/code
            temp_code_dir = os.path.join(temp_dir, "code")
            # shutil.copytree requires the destination not to exist
            shutil.copytree(self.project_root, temp_code_dir, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".venv", "venv"))

            # 2. Apply patches locally to the temp directory
            patch_results = apply_patches(patches, project_root=temp_code_dir)
            for res in patch_results:
                if "[FAILED]" in res:
                    return ValidationResult(
                        passed=False,
                        details=f"Failed to apply patch: {res}"
                    )

            # 3. Spin up Sandbox and run validations
            with DockerSandbox() as sandbox:
                try:
                    sandbox.create_sandbox(temp_code_dir)
                    
                    # Run Ruff
                    exit_code, output = sandbox.run_command("ruff check .")
                    lint_output = output
                    if exit_code != 0:
                        return ValidationResult(passed=False, details="Linting failed", lint_output=output)
                        
                    # Run Mypy
                    exit_code, output = sandbox.run_command("mypy .")
                    type_output = output
                    if exit_code != 0:
                        return ValidationResult(passed=False, details="Type checking failed", type_output=output)
                        
                    # Run Pytest
                    exit_code, output = sandbox.run_command("pytest")
                    test_output = output
                    if exit_code != 0:
                        return ValidationResult(
                            passed=False, 
                            details="Unit tests failed",
                            lint_output=lint_output,
                            type_output=type_output,
                            test_output=output
                        )
                        
                    return ValidationResult(
                        passed=True, 
                        details="Patch successfully validated!",
                        lint_output=lint_output,
                        type_output=type_output,
                        test_output=test_output
                    )
                except Exception as e:
                    return ValidationResult(passed=False, details=f"Sandbox error: {str(e)}")
