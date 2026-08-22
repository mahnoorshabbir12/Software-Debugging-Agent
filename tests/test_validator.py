import os
import pytest
from backend.agents.patch import FilePatch
from backend.validator import Validator, ValidationResult

def test_validator_success(tmp_path):
    # Setup dummy project with a test and code
    (tmp_path / "math_funcs.py").write_text("def add(a: int, b: int) -> int:\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_math.py").write_text("from math_funcs import add\n\n\ndef test_add():\n    assert add(2, 2) == 4\n", encoding="utf-8")
    
    # Run the validator with a good patch
    validator = Validator(project_root=str(tmp_path))
    patch = FilePatch(
        file_path="math_funcs.py",
        original_snippet="return a - b",
        new_snippet="return a + b",
        explanation="Fixed addition logic"
    )
    
    result = validator.validate_patch([patch])
    assert result.passed is True
    assert "successfully validated" in result.details

def test_validator_fails_tests(tmp_path):
    # Setup dummy project with a bad patch
    (tmp_path / "math_funcs.py").write_text("def add(a: int, b: int) -> int:\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_math.py").write_text("from math_funcs import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")
    
    validator = Validator(project_root=str(tmp_path))
    patch = FilePatch(
        file_path="math_funcs.py",
        original_snippet="return a - b",
        new_snippet="return a * b", # Wrong logic, should fail the test
        explanation="Multiplication"
    )
    
    result = validator.validate_patch([patch])
    assert result.passed is False
    assert "Unit tests failed" in result.details
    
def test_validator_fails_tests_real(tmp_path):
    # Setup dummy project with a bad patch
    (tmp_path / "math_funcs.py").write_text("def add(a: int, b: int) -> int:\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_math.py").write_text("from math_funcs import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")
    
    validator = Validator(project_root=str(tmp_path))
    patch = FilePatch(
        file_path="math_funcs.py",
        original_snippet="return a - b",
        new_snippet="return a * b", # 2*3 = 6 != 5, fails
        explanation="Multiplication"
    )
    
    result = validator.validate_patch([patch])
    assert result.passed is False
    assert "Unit tests failed" in result.details

def test_validator_fails_types(tmp_path):
    (tmp_path / "math_funcs.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
    
    validator = Validator(project_root=str(tmp_path))
    patch = FilePatch(
        file_path="math_funcs.py",
        original_snippet="return a + b",
        new_snippet='return "hello"', # Type error!
        explanation="Type error"
    )
    
    result = validator.validate_patch([patch])
    assert result.passed is False
    assert "Type checking failed" in result.details
