"""Base utilities for agents to load configuration from registry."""
from typing import Optional
from sqlmodel import Session
from src.registry import AgentCardSpec, AgentRegistryService, get_session


def get_agent_spec_from_registry(agent_name: str) -> Optional[AgentCardSpec]:
    """
    Get agent specification from registry by name.
    
    Args:
        agent_name: Name of the agent to retrieve
    
    Returns:
        AgentCardSpec if found, None otherwise
    """
    try:
        session = next(get_session())
        service = AgentRegistryService(session)
        return service.get_agent_by_name(agent_name)
    except Exception as e:
        print(f"Warning: Could not load agent spec from registry for '{agent_name}': {e}")
        return None
