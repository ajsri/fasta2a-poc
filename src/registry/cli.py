"""Typer CLI for agent registry management."""
import json
from pathlib import Path
from typing import Optional
import typer
from sqlmodel import Session
from src.registry import (
    AgentCardSpecCreate,
    AgentRegistryService,
    get_session,
    create_db_and_tables,
    AgentType,
    AgentStatus,
)

app = typer.Typer(help="Agent Registry CLI")


@app.command()
def init():
    """Initialize the database and create tables."""
    typer.echo("Creating database tables...")
    create_db_and_tables()
    typer.echo("✅ Database initialized successfully!")


@app.command()
def migrate(
    agents_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Directory containing agent JSON files (defaults to config.agents.directory)"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force update existing agents"
    )
):
    """Migrate agent definitions from JSON files to database."""
    # Use config directory if not specified
    if agents_dir is None:
        from src.core.config import get_config
        config = get_config()
        agents_dir = config.agents.directory
    
    agents_path = Path(agents_dir)
    typer.echo(f"Loading agents from {agents_path}...")
    
    if not agents_path.exists():
        typer.echo(f"❌ Directory {agents_path} does not exist!", err=True)
        raise typer.Exit(1)
    
    # Get session
    session = next(get_session())
    service = AgentRegistryService(session)
    
    # Find all JSON files
    json_files = list(agents_path.glob("*.json"))
    if not json_files:
        typer.echo(f"❌ No JSON files found in {agents_path}!", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Found {len(json_files)} agent definition(s)")
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                agent_data = json.load(f)
            
            agent_name = agent_data.get("name")
            if not agent_name:
                typer.echo(f"⚠️  Skipping {json_file.name}: missing 'name' field")
                skipped_count += 1
                continue
            
            # Check if agent exists
            existing = service.get_agent_by_name(agent_name)
            
            if existing:
                if force:
                    # Update existing agent
                    from src.registry.models import AgentCardSpecUpdate
                    update_data = AgentCardSpecUpdate(**agent_data)
                    service.update_agent(existing.id, update_data)
                    typer.echo(f"🔄 Updated: {agent_name}")
                    updated_count += 1
                else:
                    typer.echo(f"⏭️  Skipped: {agent_name} (already exists, use --force to update)")
                    skipped_count += 1
            else:
                # Create new agent
                agent_create = AgentCardSpecCreate(**agent_data)
                service.create_agent(agent_create)
                typer.echo(f"✅ Created: {agent_name}")
                created_count += 1
                
        except json.JSONDecodeError as e:
            typer.echo(f"❌ Error parsing {json_file.name}: {e}", err=True)
            skipped_count += 1
        except Exception as e:
            typer.echo(f"❌ Error processing {json_file.name}: {e}", err=True)
            skipped_count += 1
    
    typer.echo(f"\n📊 Migration complete:")
    typer.echo(f"   ✅ Created: {created_count}")
    typer.echo(f"   🔄 Updated: {updated_count}")
    typer.echo(f"   ⏭️  Skipped: {skipped_count}")


@app.command(name="list")
def list_agents(
    agent_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by agent type"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status")
):
    """List all agents in the registry."""
    session = next(get_session())
    service = AgentRegistryService(session)
    
    try:
        agent_type_enum = AgentType(agent_type) if agent_type else None
    except ValueError:
        typer.echo(f"❌ Invalid agent type: {agent_type}. Valid types: {[e.value for e in AgentType]}", err=True)
        raise typer.Exit(1)
    
    try:
        status_enum = AgentStatus(status) if status else None
    except ValueError:
        typer.echo(f"❌ Invalid status: {status}. Valid statuses: {[e.value for e in AgentStatus]}", err=True)
        raise typer.Exit(1)
    
    agents = service.list_agents(agent_type=agent_type_enum, status=status_enum)
    
    if not agents:
        typer.echo("No agents found.")
        return
    
    typer.echo(f"\nFound {len(agents)} agent(s):\n")
    for agent in agents:
        typer.echo(f"  [{agent.id}] {agent.name}")
        typer.echo(f"      Type: {agent.agent_type}")
        typer.echo(f"      Status: {agent.status}")
        typer.echo(f"      Version: {agent.version}")
        if agent.endpoint_url:
            typer.echo(f"      Endpoint: {agent.endpoint_url}")
        typer.echo()


@app.command()
def show(name: str):
    """Show details of a specific agent."""
    session = next(get_session())
    service = AgentRegistryService(session)
    
    agent = service.get_agent_by_name(name)
    if not agent:
        typer.echo(f"❌ Agent '{name}' not found!", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"\nAgent: {agent.name}")
    typer.echo(f"  ID: {agent.id}")
    typer.echo(f"  Type: {agent.agent_type}")
    typer.echo(f"  Version: {agent.version}")
    typer.echo(f"  Status: {agent.status}")
    typer.echo(f"  Description: {agent.description}")
    if agent.endpoint_url:
        typer.echo(f"  Endpoint: {agent.endpoint_url}")
    if agent.system_prompt:
        typer.echo(f"  System Prompt: {agent.system_prompt[:100]}...")
    typer.echo(f"  Uses ADK: {agent.uses_adk}")
    if agent.adk_model_name:
        typer.echo(f"  ADK Model: {agent.adk_model_name}")
    if agent.config:
        typer.echo(f"  Config: {json.dumps(agent.config, indent=2)}")
    typer.echo(f"  Created: {agent.created_at}")
    typer.echo(f"  Updated: {agent.updated_at}")


@app.command()
def delete(name: str, confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")):
    """Delete an agent from the registry."""
    session = next(get_session())
    service = AgentRegistryService(session)
    
    agent = service.get_agent_by_name(name)
    if not agent:
        typer.echo(f"❌ Agent '{name}' not found!", err=True)
        raise typer.Exit(1)
    
    if not confirm:
        confirm_delete = typer.confirm(f"Are you sure you want to delete '{name}'?")
        if not confirm_delete:
            typer.echo("Cancelled.")
            return
    
    success = service.delete_agent(agent.id)
    if success:
        typer.echo(f"✅ Deleted agent: {name}")
    else:
        typer.echo(f"❌ Failed to delete agent: {name}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

