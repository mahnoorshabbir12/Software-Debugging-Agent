import json
from pathlib import Path
from ingestion.scanner import RepositoryAnalyzer

def test_repository_analyzer_simple(tmp_path: Path):
    # Create simple repo structure
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "requirements.txt").write_text("typer")
    (tmp_path / ".gitignore").write_text("venv/\n")
    
    # Create ignored file
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()
    (venv_dir / "ignored.py").write_text("ignored")
    
    analyzer = RepositoryAnalyzer(str(tmp_path))
    result = analyzer.analyze()
    
    assert result.is_monorepo is False
    assert "Python" in result.languages
    assert "requirements.txt" in result.dependencies_files
    assert "main.py" in result.entry_points
    assert len(result.sub_projects) == 0

def test_repository_analyzer_monorepo(tmp_path: Path):
    # Create monorepo structure
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir()
    (frontend_dir / "package.json").write_text("{}")
    (frontend_dir / "index.js").write_text("console.log()")
    
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    (backend_dir / "pyproject.toml").write_text("")
    (backend_dir / "main.py").write_text("app = 1")
    
    # Create test directories inside sub-projects
    (backend_dir / "tests").mkdir()
    (backend_dir / "tests" / "test_main.py").write_text("")
    
    analyzer = RepositoryAnalyzer(str(tmp_path))
    result = analyzer.analyze()
    
    assert result.is_monorepo is True
    assert len(result.sub_projects) == 2
    
    sp_names = [sp.name for sp in result.sub_projects]
    assert "frontend" in sp_names
    assert "backend" in sp_names
    
    backend_sp = next(sp for sp in result.sub_projects if sp.name == "backend")
    assert "Python" in backend_sp.languages
    assert "pyproject.toml" in backend_sp.dependencies_files
    assert "main.py" in backend_sp.entry_points
    assert "tests" in backend_sp.tests or "tests/test_main.py" in backend_sp.tests
