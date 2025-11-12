# classifier_agent.py
# uvicorn src.classifier_agent:app --port 8002 --reload
import json
import uuid
from contextlib import asynccontextmanager
from typing import Any
from collections.abc import AsyncIterator
from fasta2a.schema import TaskIdParams, Message, Artifact, TaskSendParams, TextPart
from src.base import storage, broker, Context
from fasta2a import FastA2A, Worker

print("Starting Classifier Agent...")
class ClassifierWorker(Worker[Context]):
    async def run_task(self, params: TaskSendParams):
        try:
            task = await self.storage.load_task(params['id'])
            assert task is not None

            await self.storage.update_task(task['id'], state='working')

            context = await self.storage.load_context(task['context_id']) or []
            context.extend(task.get('history', []))

            text = params.get("message").get("parts")[0].get("text", "")
            if "claim" in text:
                classification = "insurance"
            elif "heart" in text:
                classification = "medical"
            else:
                classification = "general"

            message = Message(
                role='agent',
                parts=[TextPart(text=f'Class: {str(classification)}')],
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
            print("Error in ClassifierWorker:", e)
            await self.storage.update_task(task["id"], state="failed", error=str(e))

    async def cancel_task(self, params: TaskIdParams) -> None: ...

    def build_message_history(self, history: list[Message]) -> list[Any]: ...

    def build_artifacts(self, result: Any) -> list[Artifact]: ...

worker = ClassifierWorker(storage=storage, broker=broker)

@asynccontextmanager
async def lifespan(app: FastA2A) -> AsyncIterator[None]:
    async with app.task_manager:
        async with worker.run():
            yield

app = FastA2A(storage=storage, broker=broker, lifespan=lifespan)
