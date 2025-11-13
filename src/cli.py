#!/usr/bin/env python3
"""Main CLI entry point."""
import sys
import typer
import uvicorn
from src.registry.cli import app as registry_app

# Create main CLI app
app = typer.Typer(help="FastA2A Agent System CLI")

# Include registry commands
app.add_typer(registry_app, name="registry", help="Agent registry management")

@app.command()
def run(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """Run the unified multi-agent server."""
    typer.echo(f"🚀 Starting FastA2A agent server on {host}:{port}")
    if reload:
        typer.echo("🔄 Auto-reload enabled")
    typer.echo("")
    
    uvicorn.run(
        "src.run_all:main_app",
        host=host,
        port=port,
        reload=reload,
    )

if __name__ == "__main__":
    app()

