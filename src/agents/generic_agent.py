"""Generic configurable agent that reads behavior from registry."""
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any, Optional
from fasta2a import FastA2A, Worker
from fasta2a.schema import TaskIdParams, Message, TaskSendParams, TextPart
from fasta2a.broker import InMemoryBroker
from fasta2a.storage import InMemoryStorage
from src.core import Context
from src.integrations.adk import get_adk_helper
from src.registry import AgentCardSpec
from src.agents.base import get_agent_spec_from_registry


class ConfigurableWorker(Worker[Context]):
    """Generic worker that reads configuration from registry."""
    
    def __init__(self, agent_name: str, storage: InMemoryStorage, broker: InMemoryBroker):
        super().__init__(storage=storage, broker=broker)
        self.agent_name = agent_name
        self._agent_spec: Optional[AgentCardSpec] = None
    
    @property
    def agent_spec(self) -> Optional[AgentCardSpec]:
        """Lazy load agent spec from registry."""
        if self._agent_spec is None:
            self._agent_spec = get_agent_spec_from_registry(self.agent_name)
        return self._agent_spec
    
    async def run_task(self, params: TaskSendParams):
        """Execute task based on agent configuration."""
        try:
            task = await self.storage.load_task(params['id'])
            assert task is not None
            
            await self.storage.update_task(task['id'], state='working')
            
            context = await self.storage.load_context(task['context_id']) or []
            context.extend(task.get('history', []))
            
            text = params.get("message").get("parts")[0].get("text", "")
            
            # Get agent spec
            spec = self.agent_spec
            if not spec:
                raise ValueError(f"Agent spec not found for {self.agent_name}")
            
            # Process based on agent type
            result_text = await self._process_text(text, spec)
            
            # Create response message
            message = Message(
                role='agent',
                parts=[TextPart(text=result_text, kind="text")],
                kind='message',
                message_id=str(uuid.uuid4()),
            )
            
            context.append(message)
            await self.storage.update_context(task["context_id"], context)
            await self.storage.update_task(
                task["id"],
                state="completed",
                new_messages=[message]
            )
            
        except Exception as e:
            print(f"Error in ConfigurableWorker for {self.agent_name}: {e}")
            import traceback
            traceback.print_exc()
            if 'task' in locals():
                await self.storage.update_task(task["id"], state="failed", error=str(e))
    
    async def _process_text(self, text: str, spec: AgentCardSpec) -> str:
        """Process text based on agent configuration."""
        from src.registry.models import AgentType
        
        # Use ADK if configured
        if spec.uses_adk and spec.system_prompt:
            try:
                adk_helper = get_adk_helper()
                agent = adk_helper.create_agent(
                    name=spec.name.lower().replace(" ", "_"),
                    instruction=spec.system_prompt
                )
                response = await adk_helper.run_agent(
                    agent=agent,
                    text=text,
                    session_id=f"{spec.name}-{uuid.uuid4()}"
                )
                
                # Check if LLM is available
                if response and response.strip() and not response.strip().startswith("[LLM"):
                    # Post-process based on agent type
                    return self._post_process_response(response, spec)
            except Exception as e:
                print(f"ADK error for {spec.name}: {e}")
                # Fall through to fallback
        
        # Fallback logic based on agent type
        return self._fallback_process(text, spec)
    
    def _post_process_response(self, response: str, spec: AgentCardSpec) -> str:
        """Post-process LLM response based on agent type."""
        from src.registry.models import AgentType
        
        if spec.agent_type == AgentType.CLASSIFIER:
            # Extract classification label
            response_lower = response.strip().lower()
            categories = spec.config.get("categories", ["insurance", "medical", "general"])
            for category in categories:
                if category in response_lower:
                    return category
            # Return first category as default
            return categories[0] if categories else "general"
        
        # For other types, return as-is
        return response.strip()
    
    def _fallback_process(self, text: str, spec: AgentCardSpec) -> str:
        """Fallback processing when LLM is unavailable."""
        from src.registry.models import AgentType
        
        if spec.agent_type == AgentType.CLASSIFIER:
            # Keyword-based classification
            text_lower = text.lower()
            fallback_keywords = spec.config.get("fallback_keywords", {})
            for label, keywords in fallback_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    return label
            categories = spec.config.get("categories", ["insurance", "medical", "general"])
            return categories[-1] if categories else "general"
        
        elif spec.agent_type == AgentType.SUMMARIZER:
            # Truncation-based summary
            fallback_length = spec.config.get("fallback_length", 100)
            if len(text) > fallback_length:
                return text[:fallback_length] + "..."
            return text
        
        # Default: return original text
        return text
    
    async def cancel_task(self, params: TaskIdParams) -> None: ...
    
    def build_message_history(self, history: list[Message]) -> list[Any]: ...
    
    def build_artifacts(self, result: Any) -> list[Any]: ...


def create_agent_app(agent_name: str) -> tuple[FastA2A, Any]:
    """Create a FastA2A app for an agent from registry."""
    from src.registry.models import AgentType
    
    storage = InMemoryStorage()
    broker = InMemoryBroker()
    
    # Use DirectorWorker for director agents, ConfigurableWorker for others
    spec = get_agent_spec_from_registry(agent_name)
    if spec and spec.agent_type == AgentType.DIRECTOR:
        from src.agents.director_worker import DirectorWorker
        worker = DirectorWorker(storage, broker)
    else:
        worker = ConfigurableWorker(agent_name, storage, broker)
    
    @asynccontextmanager
    async def lifespan(agent_app: FastA2A) -> AsyncIterator[None]:
        """Lifespan for generic agent."""
        async with agent_app.task_manager:
            async with worker.run():
                yield
    
    # Get agent spec for metadata
    app = FastA2A(
        name=agent_name.lower().replace(" ", "-"),
        broker=broker,
        storage=storage,
        lifespan=lifespan,
        description=spec.description if spec else f"{agent_name} agent",
        version=spec.version if spec else "0.0.1",
    )
    # Set worker after app creation
    app.worker = worker
    
    return app, lifespan

