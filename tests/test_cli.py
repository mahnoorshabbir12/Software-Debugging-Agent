from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()

def test_investigate_command():
    result = runner.invoke(app, ["investigate", "API returns 500 when creating users"])
    assert result.exit_code == 0
    assert "Received investigation request for: 'API returns 500 when creating users'" in result.stdout
    assert "Initializing investigation" in result.stdout
