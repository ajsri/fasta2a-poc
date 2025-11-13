"""Agent registry models using SQLModel."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, JSON, Column
from enum import Enum


class AgentType(str, Enum):
    """Agent type enumeration."""
    CLASSIFIER = "classifier"
    SUMMARIZER = "summarizer"
    DIRECTOR = "director"
    GENERAL = "general"


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class AgentCardSpec(SQLModel, table=True):
    """Agent card specification stored in the registry."""
    
    __tablename__ = "agent_cards"
    
    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Agent identification
    name: str = Field(index=True, unique=True, description="Unique agent name")
    agent_type: AgentType = Field(index=True, description="Type of agent")
    version: str = Field(default="0.0.1", description="Agent version")
    
    # Agent metadata
    description: str = Field(description="Agent description")
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, index=True, description="Agent status")
    
    # Agent configuration
    endpoint_url: Optional[str] = Field(default=None, description="Agent endpoint URL (for HTTP calls)")
    system_prompt: Optional[str] = Field(default=None, description="System prompt/instruction for the agent")
    
    # ADK configuration (if using ADK)
    uses_adk: bool = Field(default=False, description="Whether agent uses ADK framework")
    adk_model_name: Optional[str] = Field(default=None, description="ADK model name if using ADK")
    
    # Additional configuration (stored as JSON)
    config: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional agent configuration as JSON"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        """Pydantic config."""
        use_enum_values = True


class AgentCardSpecCreate(SQLModel):
    """Schema for creating an agent card."""
    name: str
    agent_type: AgentType
    version: str = "0.0.1"
    description: str
    status: AgentStatus = AgentStatus.ACTIVE
    endpoint_url: Optional[str] = None
    system_prompt: Optional[str] = None
    uses_adk: bool = False
    adk_model_name: Optional[str] = None
    config: Optional[dict] = None


class AgentCardSpecUpdate(SQLModel):
    """Schema for updating an agent card."""
    name: Optional[str] = None
    agent_type: Optional[AgentType] = None
    version: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AgentStatus] = None
    endpoint_url: Optional[str] = None
    system_prompt: Optional[str] = None
    uses_adk: Optional[bool] = None
    adk_model_name: Optional[str] = None
    config: Optional[dict] = None


class AgentCardSpecRead(SQLModel):
    """Schema for reading an agent card."""
    id: int
    name: str
    agent_type: AgentType
    version: str
    description: str
    status: AgentStatus
    endpoint_url: Optional[str] = None
    system_prompt: Optional[str] = None
    uses_adk: bool
    adk_model_name: Optional[str] = None
    config: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

