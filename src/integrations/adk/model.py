"""Custom ADK model adapter for oss-gpt (OpenAI-compatible API)."""
import httpx
from typing import AsyncGenerator
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.genai.types import Content, Part
from src.core.config import get_config


class OssGptLlm(BaseLlm):
    """ADK model adapter for oss-gpt using OpenAI-compatible API."""
    
    def __init__(self, model: str = "oss-gpt", **kwargs):
        """
        Initialize oss-gpt LLM adapter.
        
        Args:
            model: Model name (default: "oss-gpt")
            **kwargs: Additional arguments passed to BaseLlm
        """
        super().__init__(model=model, **kwargs)
        # Store config in model's __dict__ to avoid Pydantic validation
        object.__setattr__(self, '_config', get_config())
    
    @property
    def config(self):
        """Get the configuration."""
        return self._config
    
    async def generate_content_async(
        self, 
        llm_request: LlmRequest, 
        stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        Generate content from oss-gpt API.
        
        Args:
            llm_request: The LLM request containing messages and tools
            stream: Whether to stream the response (not yet supported)
        
        Yields:
            LlmResponse objects containing the generated content
        """
        # Convert ADK LlmRequest to OpenAI-compatible format
        messages = []
        
        # Add system instruction if present (check if it exists)
        if hasattr(llm_request, 'instruction') and llm_request.instruction:
            messages.append({
                "role": "system",
                "content": llm_request.instruction
            })
        
        # Convert contents to OpenAI format
        for content in llm_request.contents:
            if isinstance(content, Content):
                # Extract text from Content
                text_parts = []
                for part in content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                
                if text_parts:
                    role = "user"  # Default role
                    # Try to determine role from content
                    if hasattr(content, 'role'):
                        role = content.role
                    elif hasattr(content, 'parts') and content.parts:
                        # Check if it's an assistant message
                        pass
                    
                    messages.append({
                        "role": role if role in ["user", "assistant", "system"] else "user",
                        "content": " ".join(text_parts)
                    })
            elif isinstance(content, str):
                messages.append({
                    "role": "user",
                    "content": content
                })
        
        # Prepare OpenAI-compatible payload
        payload = {
            "model": self.config.model.name,
            "messages": messages,
            "temperature": self.config.model.parameters.temperature,
            "max_tokens": self.config.model.parameters.max_tokens,
        }
        
        # Add tools if present (convert ADK tools to OpenAI format)
        if hasattr(llm_request, 'tools') and llm_request.tools:
            # TODO: Convert ADK tools to OpenAI function calling format
            pass
        
        # Make request to oss-gpt API
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.config.model.endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract response text
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        response_text = choice["message"]["content"].strip()
                    elif "text" in choice:
                        response_text = choice["text"].strip()
                    else:
                        response_text = ""
                    
                    # Create ADK LlmResponse
                    content = Content(
                        parts=[Part(text=response_text)],
                        role="model"
                    )
                    
                    llm_response = LlmResponse(
                        content=content
                    )
                    
                    yield llm_response
                else:
                    # Empty response
                    content = Content(
                        parts=[Part(text="")],
                        role="model"
                    )
                    yield LlmResponse(
                        content=content
                    )
                    
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
                # Return empty response instead of raising error (fallback behavior)
                print(f"Warning: Failed to call oss-gpt API: {error_msg}")
                content = Content(
                    parts=[Part(text=f"[LLM unavailable: {error_msg}]")],
                    role="model"
                )
                yield LlmResponse(
                    content=content
                )
                return
            except httpx.RequestError as e:
                # Return empty response instead of raising error (fallback behavior)
                print(f"Warning: Request error calling oss-gpt API: {str(e)}")
                content = Content(
                    parts=[Part(text=f"[LLM unavailable: Connection failed. Please ensure oss-gpt is running.]")],
                    role="model"
                )
                yield LlmResponse(
                    content=content
                )
                return
            except Exception as e:
                # Return error message instead of raising
                print(f"Warning: Unexpected error calling oss-gpt API: {str(e)}")
                content = Content(
                    parts=[Part(text=f"[LLM error: {str(e)}]")],
                    role="model"
                )
                yield LlmResponse(
                    content=content
                )
                return

