"""Agent registry API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from src.registry import (
    AgentCardSpec,
    AgentCardSpecCreate,
    AgentCardSpecUpdate,
    AgentCardSpecRead,
    AgentType,
    AgentStatus,
    AgentRegistryService,
    get_session,
)

router = APIRouter(prefix="/registry", tags=["registry"])


def get_registry_service(session: Session = Depends(get_session)) -> AgentRegistryService:
    """Get registry service instance."""
    return AgentRegistryService(session)


@router.post("/agents", response_model=AgentCardSpecRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCardSpecCreate,
    service: AgentRegistryService = Depends(get_registry_service)
):
    """Create a new agent card."""
    # Check if agent with same name already exists
    existing = service.get_agent_by_name(agent_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent with name '{agent_data.name}' already exists"
        )
    
    agent = service.create_agent(agent_data)
    return agent


@router.get("/agents", response_model=List[AgentCardSpecRead])
async def list_agents(
    agent_type: Optional[AgentType] = None,
    status: Optional[AgentStatus] = None,
    limit: int = 100,
    offset: int = 0,
    service: AgentRegistryService = Depends(get_registry_service)
):
    """List all agents with optional filtering."""
    agents = service.list_agents(agent_type=agent_type, status=status, limit=limit, offset=offset)
    return agents


@router.get("/agents/{agent_id}", response_model=AgentCardSpecRead)
async def get_agent(
    agent_id: int,
    service: AgentRegistryService = Depends(get_registry_service)
):
    """Get agent by ID."""
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    return agent


@router.get("/agents/name/{name}", response_model=AgentCardSpecRead)
async def get_agent_by_name(
    name: str,
    service: AgentRegistryService = Depends(get_registry_service)
):
    """Get agent by name."""
    agent = service.get_agent_by_name(name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with name '{name}' not found"
        )
    return agent


@router.put("/agents/{agent_id}", response_model=AgentCardSpecRead)
async def update_agent(
    agent_id: int,
    agent_data: AgentCardSpecUpdate,
    service: AgentRegistryService = Depends(get_registry_service)
):
    """Update an agent card."""
    agent = service.update_agent(agent_id, agent_data)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    return agent


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    service: AgentRegistryService = Depends(get_registry_service)
):
    """Delete an agent card."""
    success = service.delete_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )


@router.get("/agents/type/{agent_type}", response_model=List[AgentCardSpecRead])
async def get_agents_by_type(
    agent_type: AgentType,
    service: AgentRegistryService = Depends(get_registry_service)
):
    """Get all active agents of a specific type."""
    agents = service.get_active_agents_by_type(agent_type)
    return agents

