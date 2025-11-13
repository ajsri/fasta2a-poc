"""Factory for creating agents dynamically from registry."""
from typing import Dict, Tuple
from fastapi import FastAPI
from fasta2a import FastA2A
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from src.core.config import get_config
from src.registry.loader import get_agents_to_load
from src.agents.base import get_agent_spec_from_registry
from src.agents.generic_agent import create_agent_app


def create_agents_from_config() -> Dict[str, Tuple[FastA2A, any]]:
    """
    Create agent apps dynamically from configuration.
    
    Returns:
        Dictionary mapping agent names to (app, lifespan) tuples
    """
    agents = {}
    agent_names = get_agents_to_load()
    
    for agent_name in agent_names:
        # Verify agent exists in registry
        spec = get_agent_spec_from_registry(agent_name)
        if not spec:
            print(f"Warning: Agent '{agent_name}' not found in registry, skipping")
            continue
        
        # Create app and lifespan
        app, lifespan = create_agent_app(agent_name)
        agents[agent_name] = (app, lifespan)
        print(f"✅ Created agent: {agent_name} at {spec.endpoint_url}")
    
    return agents


def get_agent_mount_path(agent_name: str) -> str:
    """Get mount path for an agent based on its endpoint URL."""
    spec = get_agent_spec_from_registry(agent_name)
    if spec and spec.endpoint_url:
        # Extract path from URL (e.g., http://localhost:8000/summarizer/ -> /summarizer)
        from urllib.parse import urlparse
        parsed = urlparse(spec.endpoint_url)
        return parsed.path.rstrip('/') or f"/{agent_name.lower().replace(' ', '-')}"
    # Default: use agent name
    return f"/{agent_name.lower().replace(' ', '-')}"

