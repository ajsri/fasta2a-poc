# summarizer_agent.py
# uvicorn src.summarizer_agent:app --port 8001 --reload
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pprint import pprint
from typing import Any

from src.base import storage, broker, Context
from fasta2a import FastA2A, Worker
from fasta2a.schema import Artifact, Message, TaskIdParams, TaskSendParams, TextPart


print("Starting Summarizer Agent...")
class SummarizerWorker(Worker[Context]):
    async def run_task(self, params: TaskSendParams):
        try:
            task = await self.storage.load_task(params['id'])
            assert task is not None

            await self.storage.update_task(task['id'], state='working')

            context = await self.storage.load_context(task['context_id']) or []
            context.extend(task.get('history', []))

            text = params.get("message").get("parts")[0].get("text", "")
            truncated_text = text[:50]

            message = Message(
                role='agent',
                parts=[TextPart(text=f'Shortened Summary: {truncated_text}')],
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
            print("Error in SummarizerWorker:", e)
            await self.storage.update_task(task["id"], state="failed", error=str(e))

    async def cancel_task(self, params: TaskIdParams) -> None: ...

    def build_message_history(self, history: list[Message]) -> list[Any]: ...

    def build_artifacts(self, result: Any) -> list[Artifact]: ...

worker = SummarizerWorker(storage=storage, broker=broker)

@asynccontextmanager
async def lifespan(app: FastA2A) -> AsyncIterator[None]:
    async with app.task_manager:
        async with worker.run():
            yield

app = FastA2A(storage=storage, broker=broker, lifespan=lifespan)
