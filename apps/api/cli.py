import typer

app = typer.Typer(help="Autonomous Software Debugging Agent CLI")

@app.command()
def investigate(bug_report: str):
    """
    Investigate a bug report.
    For now, it only prints the investigation request.
    """
    typer.echo(f"Received investigation request for: '{bug_report}'")
    typer.echo("Initializing investigation... (Features to be implemented in later phases)")

@app.command()
def analyze(path: str = "."):
    """
    Analyze a repository to determine its structure, languages, and monorepo status.
    """
    import json
    from ingestion.scanner import RepositoryAnalyzer
    
    typer.echo(f"Analyzing repository at: {path}...")
    try:
        analyzer = RepositoryAnalyzer(path)
        repo_map = analyzer.analyze()
        typer.echo(repo_map.model_dump_json(indent=2))
    except Exception as e:
        typer.echo(f"Error analyzing repository: {e}", err=True)

@app.command()
def version():
    """
    Print the version of the autonomous debugger.
    """
    typer.echo("0.1.0")

if __name__ == "__main__":
    app()
