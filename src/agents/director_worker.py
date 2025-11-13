"""Director agent worker - orchestrates other agents."""
import asyncio
import copy
import uuid
from typing import Any
import httpx
from fasta2a.schema import TaskIdParams, Message, TaskSendParams, TextPart
from fasta2a import Worker
from fasta2a.broker import InMemoryBroker
from fasta2a.storage import InMemoryStorage
from src.core import Context
from src.registry.loader import get_agent_url_from_registry
from src.core.config import get_config


A2A_MESSAGE_TEMPLATE = {
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
        "message": {
            "role": "user",
            "kind": "message",
            "messageId": "msg-001",
            "parts": [
                {
                    "kind": "text",
                    "text": None,  # to be filled
                }
            ]
        }
    },
    "id": 1234
}

A2A_GET_TASK_TEMPLATE = {
    "jsonrpc": "2.0",
    "method": "tasks/get",
    "params": {
        "id": None  # to be filled
    },
    "id": "1234"
}


async def get_agent_message(url: str, payload: dict) -> str:
    """
    Send a message to an agent and wait for response.
    
    Args:
        url: Agent endpoint URL
        payload: JSON-RPC payload to send
    
    Returns:
        Response text or error message
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Send message
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "result" not in result:
                return f"[Error: No result in response]"
            
            task_id = result["result"].get("id")
            if not task_id:
                return f"[Error: No task ID in response]"
            
            # Poll for task completion
            get_task_payload = copy.deepcopy(A2A_GET_TASK_TEMPLATE)
            get_task_payload["params"]["id"] = task_id
            
            max_attempts = 30
            for attempt in range(max_attempts):
                await asyncio.sleep(0.3)
                task_response = await client.post(url, json=get_task_payload)
                task_response.raise_for_status()
                task_result = task_response.json()
                
                if "result" not in task_result:
                    continue
                
                task = task_result["result"]
                state = task.get("state", "")
                
                if state == "completed":
                    history = task.get("history", [])
                    if history:
                        last_message = history[-1]
                        parts = last_message.get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    return ""
                
                if state == "failed":
                    error = task.get("error", "Unknown error")
                    return f"[Error: {error}]"
            
            return "[Error: Timeout waiting for response]"
            
        except httpx.HTTPStatusError as e:
            return f"[Error: HTTP {e.response.status_code}]"
        except httpx.RequestError as e:
            return f"[Error: Request failed: {str(e)}]"
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"[Error: {str(e)}]"


class DirectorWorker(Worker[Context]):
    """Director agent that orchestrates other agents."""
    
    def __init__(self, storage: InMemoryStorage, broker: InMemoryBroker):
        super().__init__(storage=storage, broker=broker)
    
    async def run_task(self, params: TaskSendParams):
        """Orchestrate calls to other agents."""
        async with httpx.AsyncClient() as client:
            try:
                task = await self.storage.load_task(params["id"])
                assert task is not None
                await self.storage.update_task(task["id"], state="working")
                
                context = await self.storage.load_context(task["context_id"]) or []
                context.extend(task.get("history", []))
                
                text = params.get("message").get("parts")[0].get("text", "")
                
                # Get agent URLs from registry based on config
                config = get_config()
                agent_names = config.agents.load
                
                # Find summarizer and classifier agents
                summarizer_name = next((n for n in agent_names if "summarizer" in n.lower()), None)
                classifier_name = next((n for n in agent_names if "classifier" in n.lower()), None)
                
                # Get URLs from registry
                summarizer_url = get_agent_url_from_registry(summarizer_name) if summarizer_name else None
                classifier_url = get_agent_url_from_registry(classifier_name) if classifier_name else None
                
                # Fallback to defaults
                if not summarizer_url:
                    summarizer_url = "http://localhost:8000/summarizer/"
                if not classifier_url:
                    classifier_url = "http://localhost:8000/classifier/"
                
                # Create payloads
                summarizer_payload = copy.deepcopy(A2A_MESSAGE_TEMPLATE)
                summarizer_payload["params"]["message"]["parts"][0]["text"] = text
                summarizer_payload["params"]["message"]["messageId"] = f"summarizer-{uuid.uuid4()}"
                summarizer_payload["id"] = 1
                
                classifier_payload = copy.deepcopy(A2A_MESSAGE_TEMPLATE)
                classifier_payload["params"]["message"]["parts"][0]["text"] = text
                classifier_payload["params"]["message"]["messageId"] = f"classifier-{uuid.uuid4()}"
                classifier_payload["id"] = 2
                
                # Call agents in parallel
                summarizer_agent_response, classifier_agent_response = await asyncio.gather(
                    get_agent_message(summarizer_url, summarizer_payload),
                    get_agent_message(classifier_url, classifier_payload),
                    return_exceptions=True
                )
                
                # Handle exceptions
                if isinstance(summarizer_agent_response, Exception):
                    summarizer_agent_response = f"[Error: {str(summarizer_agent_response)}]"
                if isinstance(classifier_agent_response, Exception):
                    classifier_agent_response = f"[Error: {str(classifier_agent_response)}]"
                
                # Handle empty responses
                if not summarizer_agent_response or summarizer_agent_response.strip() == "":
                    summarizer_agent_response = "[No summary available]"
                if not classifier_agent_response or classifier_agent_response.strip() == "":
                    classifier_agent_response = "[No classification available]"
                
                formatted_text = f"""
Our behind-the-scenes bots formed the following conclusions:
## Summary:
{summarizer_agent_response}
## Label:
{classifier_agent_response}
"""
                
                message = Message(
                    role="agent",
                    parts=[TextPart(text=formatted_text.strip(), kind="text")],
                    kind="message",
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
                print(f"Error in DirectorWorker: {e}")
                import traceback
                traceback.print_exc()
                if 'task' in locals():
                    await self.storage.update_task(task["id"], state="failed", error=str(e))
    
    async def cancel_task(self, params: TaskIdParams) -> None: ...
    
    def build_message_history(self, history: list[Message]) -> list[Any]: ...
    
    def build_artifacts(self, result: Any) -> list[Any]: ...

