"""Shared ADK helper for running ADK agents."""
import uuid
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from src.integrations.adk.model import OssGptLlm


class AdkHelper:
    """Helper class for running ADK agents."""
    
    def __init__(self):
        """Initialize ADK helper with session service."""
        self.session_service = InMemorySessionService()
        self.oss_gpt_model = OssGptLlm(model="oss-gpt")
    
    def create_agent(self, name: str, instruction: str) -> LlmAgent:
        """
        Create an ADK LlmAgent with the given name and instruction.
        
        Args:
            name: Agent name (must be valid identifier)
            instruction: System instruction for the agent
        
        Returns:
            Configured LlmAgent instance
        """
        return LlmAgent(
            name=name,
            description=f"ADK-powered {name} agent",
            model=self.oss_gpt_model,
            instruction=instruction
        )
    
    async def run_agent(self, agent: LlmAgent, text: str, session_id: str | None = None) -> str:
        """
        Run an ADK agent with the given text input.
        
        Args:
            agent: ADK LlmAgent instance
            text: Input text to process
            session_id: Optional session ID (generates new one if not provided)
        
        Returns:
            Agent's response text
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        user_id = "fasta2a-user"
        
        # Create Content object for the user message
        user_message = Content(
            parts=[Part(text=text)],
            role="user"
        )
        
        # Ensure session exists
        existing_session = await self.session_service.get_session(
            app_name="agents",
            user_id=user_id,
            session_id=session_id
        )
        if existing_session is None:
            await self.session_service.create_session(
                app_name="agents",
                user_id=user_id,
                session_id=session_id
            )
        
        # Create runner for this agent
        runner = Runner(
            app_name="agents",
            agent=agent,
            session_service=self.session_service
        )
        
        # Run agent and collect response
        response_text = ""
        event_count = 0
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        ):
            event_count += 1
            # Collect response from events
            if hasattr(event, 'content') and event.content:
                if isinstance(event.content, str):
                    response_text += event.content
                elif isinstance(event.content, Content):
                    if event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
            
            # Check if this is a final response
            if hasattr(event, 'is_final_response') and callable(event.is_final_response):
                if event.is_final_response():
                    break
        
        return response_text.strip() if response_text else ""


# Global ADK helper instance
_adk_helper: AdkHelper | None = None


def get_adk_helper() -> AdkHelper:
    """Get the global ADK helper instance (singleton)."""
    global _adk_helper
    if _adk_helper is None:
        _adk_helper = AdkHelper()
    return _adk_helper

