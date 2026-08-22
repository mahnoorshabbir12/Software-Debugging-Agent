# Module 13: Patch Generation

This module bridges the gap between *understanding* a bug and *fixing* it. We created an agent that can take the confirmed root cause and output exact instructions for modifying the codebase.

## Concepts Learned

### 1. Minimal Code Modifications (Search & Replace)
**What it is:** Instead of asking the LLM to rewrite the entire file or output a traditional git unified diff (which often suffers from hallucinated line numbers), we ask the LLM for an exact substring to replace (`original_snippet`) and what to replace it with (`new_snippet`).
**What problem it solves:** Unified diffs are brittle. LLMs often mess up the number of context lines or miscount line numbers. Search & Replace is robust because it just relies on standard string replacement. It also forces the LLM to make the smallest change possible, reducing regression risk.
**Why we used it here:** To safely apply bug fixes to local files without deleting unrelated code or corrupting syntax.

### 2. The Patcher Applicator
**What it is:** A utility script (`backend/patcher.py`) that reads the file, strictly verifies that the `original_snippet` exists exactly once, performs the string replacement, and saves the file.
**What problem it solves:** It acts as a safeguard. If the LLM hallucinates whitespace or if the snippet exists in multiple places, the patcher rejects the patch rather than corrupting the file.

## Transferable Rules
> **Use Search & Replace for Code Agents:** When building agents that modify code, always prefer exact substring matching (Search & Replace blocks) over git diffs or full-file replacements. It is the industry standard approach for autonomous coding (used by systems like Aider).
> 
> **Always Safeguard File Writes:** Never blindly overwrite a file. Always check that the target string exists and is unique before applying a mutation.
