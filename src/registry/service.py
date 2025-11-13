"""Agent registry service."""
from typing import Optional, List
from sqlmodel import Session, select
from src.registry.models import (
    AgentCardSpec,
    AgentCardSpecCreate,
    AgentCardSpecUpdate,
    AgentType,
    AgentStatus,
)
from datetime import datetime


class AgentRegistryService:
    """Service for managing agent registry."""
    
    def __init__(self, session: Session):
        """Initialize registry service with database session."""
        self.session = session
    
    def create_agent(self, agent_data: AgentCardSpecCreate) -> AgentCardSpec:
        """Create a new agent card."""
        agent = AgentCardSpec(**agent_data.model_dump())
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent
    
    def get_agent(self, agent_id: int) -> Optional[AgentCardSpec]:
        """Get agent by ID."""
        return self.session.get(AgentCardSpec, agent_id)
    
    def get_agent_by_name(self, name: str) -> Optional[AgentCardSpec]:
        """Get agent by name."""
        statement = select(AgentCardSpec).where(AgentCardSpec.name == name)
        return self.session.exec(statement).first()
    
    def list_agents(
        self,
        agent_type: Optional[AgentType] = None,
        status: Optional[AgentStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AgentCardSpec]:
        """List agents with optional filtering."""
        statement = select(AgentCardSpec)
        
        if agent_type:
            statement = statement.where(AgentCardSpec.agent_type == agent_type)
        if status:
            statement = statement.where(AgentCardSpec.status == status)
        
        statement = statement.limit(limit).offset(offset)
        return list(self.session.exec(statement).all())
    
    def update_agent(self, agent_id: int, agent_data: AgentCardSpecUpdate) -> Optional[AgentCardSpec]:
        """Update an agent card."""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        update_data = agent_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        for key, value in update_data.items():
            setattr(agent, key, value)
        
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent
    
    def delete_agent(self, agent_id: int) -> bool:
        """Delete an agent card."""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        self.session.delete(agent)
        self.session.commit()
        return True
    
    def get_active_agents_by_type(self, agent_type: AgentType) -> List[AgentCardSpec]:
        """Get all active agents of a specific type."""
        statement = select(AgentCardSpec).where(
            AgentCardSpec.agent_type == agent_type,
            AgentCardSpec.status == AgentStatus.ACTIVE
        )
        return list(self.session.exec(statement).all())

