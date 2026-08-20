import os
import pathspec
from pathlib import Path
from typing import List, Dict, Set, Optional

from ingestion.models import RepositoryMap, SubProjectMap

# Extension to language mapping
LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".html": "HTML",
    ".css": "CSS",
}

DEPENDENCY_FILES = {
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "package.json": "JavaScript/TypeScript",
    "go.mod": "Go",
    "pom.xml": "Java",
    "Cargo.toml": "Rust",
}

class RepositoryAnalyzer:
    """
    Analyzes a given repository directory to extract its structural map.
    It applies gitignore filtering and detects languages, frameworks, and sub-projects (monorepo).
    """

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.ignore_spec = self._load_ignore_patterns()

    def _load_ignore_patterns(self) -> pathspec.PathSpec:
        """Loads .gitignore patterns and combines them with defaults."""
        patterns = [
            ".git/", ".venv/", "venv/", "env/", "__pycache__/", 
            "node_modules/", "dist/", "build/", "*.pyc"
        ]
        
        gitignore_path = self.root_path / ".gitignore"
        if gitignore_path.is_file():
            with open(gitignore_path, "r", encoding="utf-8") as f:
                patterns.extend(f.read().splitlines())
                
        return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

    def _is_ignored(self, path: Path) -> bool:
        """Checks if a path should be ignored according to the pathspec."""
        try:
            rel_path = path.relative_to(self.root_path)
            # pathspec expects posix paths
            posix_path = rel_path.as_posix()
            if path.is_dir() and not posix_path.endswith("/"):
                posix_path += "/"
            return self.ignore_spec.match_file(posix_path)
        except ValueError:
            return True # If not relative to root, ignore

    def analyze(self) -> RepositoryMap:
        """Scans the repository and builds the structural map."""
        if not self.root_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {self.root_path}")

        all_files = []
        for root, dirs, files in os.walk(self.root_path):
            current_dir = Path(root)
            
            # Filter directories in-place to prevent walking down ignored trees
            dirs[:] = [d for d in dirs if not self._is_ignored(current_dir / d)]
            
            for file in files:
                file_path = current_dir / file
                if not self._is_ignored(file_path):
                    all_files.append(file_path)

        # Basic analysis variables
        overall_languages: Set[str] = set()
        root_dependencies: List[str] = []
        sub_projects: Dict[str, SubProjectMap] = {}
        
        # Determine monorepo structure by looking for dependency files in depth 1 directories
        for f in all_files:
            rel_path = f.relative_to(self.root_path)
            
            # Detect overall language
            ext = f.suffix.lower()
            if ext in LANGUAGE_MAP:
                overall_languages.add(LANGUAGE_MAP[ext])
                
            # Check for dependency files
            if f.name in DEPENDENCY_FILES:
                parts = rel_path.parts
                if len(parts) == 1:
                    # Root dependency file
                    root_dependencies.append(f.name)
                elif len(parts) == 2:
                    # Depth 1 dependency file -> indicates a subproject in a monorepo
                    sub_dir = parts[0]
                    if sub_dir not in sub_projects:
                        sub_projects[sub_dir] = SubProjectMap(
                            name=sub_dir,
                            path=sub_dir
                        )
                    if f.name not in sub_projects[sub_dir].dependencies_files:
                        sub_projects[sub_dir].dependencies_files.append(f.name)

        # Now enrich the sub_projects with languages and tests
        for f in all_files:
            rel_path = f.relative_to(self.root_path)
            parts = rel_path.parts
            
            if len(parts) > 1 and parts[0] in sub_projects:
                sub_dir = parts[0]
                sp = sub_projects[sub_dir]
                
                # Language
                ext = f.suffix.lower()
                if ext in LANGUAGE_MAP and LANGUAGE_MAP[ext] not in sp.languages:
                    sp.languages.append(LANGUAGE_MAP[ext])
                    
                # Tests detection (heuristic)
                if "test" in f.name.lower() or "tests" in parts:
                    test_str = "/".join(parts[1:3]) # simplified relative to subproject
                    if test_str not in sp.tests:
                        sp.tests.append(test_str)
                        
                # Entry points (heuristic)
                if f.name in ["main.py", "index.js", "manage.py", "app.py"]:
                    if f.name not in sp.entry_points:
                        sp.entry_points.append(f.name)

        # Root level tests and entry points for simple repos
        root_tests = []
        root_entry_points = []
        for f in all_files:
            rel_path = f.relative_to(self.root_path)
            parts = rel_path.parts
            # Only consider files not belonging to a recognized sub-project
            if len(parts) > 0 and parts[0] not in sub_projects:
                if "test" in f.name.lower() or "tests" in parts:
                    root_tests.append(rel_path.as_posix())
                if f.name in ["main.py", "index.js", "manage.py", "app.py"] and len(parts) == 1:
                    root_entry_points.append(f.name)
                    
        # Limit the number of tracked test files to avoid massive outputs
        root_tests = list(set(root_tests))[:5]
        
        is_monorepo = len(sub_projects) > 0

        return RepositoryMap(
            root_path=str(self.root_path),
            is_monorepo=is_monorepo,
            languages=list(overall_languages),
            frameworks=[], # Will be detected based on parsing requirements/package.json later
            sub_projects=list(sub_projects.values()),
            dependencies_files=root_dependencies,
            entry_points=list(set(root_entry_points)),
            tests=root_tests
        )
