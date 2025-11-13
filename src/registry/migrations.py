"""Migration utilities for agent registry."""
import json
from pathlib import Path
from typing import List
from src.registry import AgentCardSpecCreate, AgentRegistryService, get_session


def load_agents_from_json(agents_dir: Path) -> List[AgentCardSpecCreate]:
    """Load agent definitions from JSON files."""
    agents = []
    
    if not agents_dir.exists():
        raise FileNotFoundError(f"Directory {agents_dir} does not exist")
    
    json_files = list(agents_dir.glob("*.json"))
    if not json_files:
        raise ValueError(f"No JSON files found in {agents_dir}")
    
    for json_file in json_files:
        with open(json_file, "r") as f:
            agent_data = json.load(f)
            agents.append(AgentCardSpecCreate(**agent_data))
    
    return agents


def migrate_agents(agents_dir: Path, force: bool = False) -> dict:
    """Migrate agents from JSON files to database."""
    session = next(get_session())
    service = AgentRegistryService(session)
    
    agents = load_agents_from_json(agents_dir)
    
    results = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": []
    }
    
    for agent_data in agents:
        try:
            existing = service.get_agent_by_name(agent_data.name)
            
            if existing:
                if force:
                    service.update_agent(existing.id, agent_data)
                    results["updated"] += 1
                else:
                    results["skipped"] += 1
            else:
                service.create_agent(agent_data)
                results["created"] += 1
        except Exception as e:
            results["errors"].append(f"{agent_data.name}: {str(e)}")
    
    return results

