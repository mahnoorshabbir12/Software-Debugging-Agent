import os
from typing import List
from backend.agents.patch import FilePatch

def apply_patches(patches: List[FilePatch], project_root: str = ".") -> List[str]:
    """
    Applies a list of FilePatches to the filesystem.
    Returns a list of messages detailing success or failure for each patch.
    """
    results = []
    
    for patch in patches:
        full_path = os.path.join(project_root, patch.file_path)
        
        if not os.path.exists(full_path):
            results.append(f"[FAILED]: File {patch.file_path} does not exist.")
            continue
            
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Ensure the snippet actually exists in the file
        count = content.count(patch.original_snippet)
        
        if count == 0:
            results.append(f"[FAILED]: original_snippet not found in {patch.file_path}. (Check whitespace/indentation)")
            continue
        elif count > 1:
            results.append(f"[FAILED]: original_snippet is not unique in {patch.file_path}. Found {count} occurrences.")
            continue
            
        # Perform the replacement
        new_content = content.replace(patch.original_snippet, patch.new_snippet)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        results.append(f"[SUCCESS]: Applied patch to {patch.file_path}. ({patch.explanation})")
        
    return results
