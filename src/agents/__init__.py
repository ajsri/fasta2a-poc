"""Agent implementations for the FastA2A POC.

Agents are now dynamically created from registry configuration.
See src/agents/factory.py for agent creation logic.
"""

from src.agents.factory import create_agents_from_config, get_agent_mount_path
from src.agents.generic_agent import ConfigurableWorker, create_agent_app
from src.agents.director_worker import DirectorWorker

__all__ = [
    "create_agents_from_config",
    "get_agent_mount_path",
    "ConfigurableWorker",
    "create_agent_app",
    "DirectorWorker",
]

