"""Utilities for loading agents from registry based on configuration."""
from typing import List, Optional
from sqlmodel import Session
from src.core.config import get_config
from src.registry import AgentCardSpec, AgentRegistryService, get_session, AgentType


def get_agents_to_load() -> List[str]:
    """Get list of agent names to load from configuration."""
    config = get_config()
    return config.agents.load


def get_agent_url_from_registry(agent_name: str) -> Optional[str]:
    """
    Get agent endpoint URL from registry.
    
    Args:
        agent_name: Name of the agent
    
    Returns:
        Endpoint URL if found, None otherwise
    """
    try:
        session = next(get_session())
        service = AgentRegistryService(session)
        agent = service.get_agent_by_name(agent_name)
        return agent.endpoint_url if agent else None
    except Exception:
        return None


def get_agents_by_type_from_registry(agent_type: AgentType) -> List[AgentCardSpec]:
    """Get all active agents of a specific type from registry."""
    try:
        session = next(get_session())
        service = AgentRegistryService(session)
        return service.get_active_agents_by_type(agent_type)
    except Exception:
        return []

