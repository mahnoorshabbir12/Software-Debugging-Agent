import os
import pytest
from backend.agents.patch import FilePatch
from backend.patcher import apply_patches

def test_apply_patches_success(tmp_path):
    # Create a dummy file in the tmp_path
    dummy_file = tmp_path / "dummy.py"
    original_code = "def add(a, b):\n    return a - b\n"
    dummy_file.write_text(original_code, encoding="utf-8")
    
    # Create a patch
    patch = FilePatch(
        file_path="dummy.py",
        original_snippet="    return a - b\n",
        new_snippet="    return a + b\n",
        explanation="Fixed subtraction to addition"
    )
    
    # Apply patch
    results = apply_patches([patch], project_root=str(tmp_path))
    
    assert len(results) == 1
    assert "[SUCCESS]" in results[0]
    
    # Verify file content
    fixed_code = dummy_file.read_text(encoding="utf-8")
    assert fixed_code == "def add(a, b):\n    return a + b\n"

def test_apply_patches_file_not_found(tmp_path):
    patch = FilePatch(
        file_path="missing.py",
        original_snippet="old",
        new_snippet="new",
        explanation="test"
    )
    
    results = apply_patches([patch], project_root=str(tmp_path))
    assert "[FAILED]" in results[0]
    assert "does not exist" in results[0]

def test_apply_patches_snippet_not_found(tmp_path):
    dummy_file = tmp_path / "dummy.py"
    dummy_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    
    patch = FilePatch(
        file_path="dummy.py",
        original_snippet="return a - b", # This doesn't exist
        new_snippet="return a + b",
        explanation="test"
    )
    
    results = apply_patches([patch], project_root=str(tmp_path))
    assert "[FAILED]" in results[0]
    assert "not found" in results[0]

def test_apply_patches_snippet_not_unique(tmp_path):
    dummy_file = tmp_path / "dummy.py"
    # The snippet exists twice
    dummy_file.write_text("x = 1\nx = 1\n", encoding="utf-8")
    
    patch = FilePatch(
        file_path="dummy.py",
        original_snippet="x = 1",
        new_snippet="x = 2",
        explanation="test"
    )
    
    results = apply_patches([patch], project_root=str(tmp_path))
    assert "[FAILED]" in results[0]
    assert "not unique" in results[0]
