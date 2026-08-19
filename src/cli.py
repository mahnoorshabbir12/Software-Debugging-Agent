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
def version():
    """
    Print the version of the autonomous debugger.
    """
    typer.echo("0.1.0")

if __name__ == "__main__":
    app()
