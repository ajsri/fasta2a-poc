# director_agent.py
# uvicorn src.director_agent:app --port 8003 --reload
import copy
from contextlib import asynccontextmanager
from typing import Any
from collections.abc import AsyncIterator
import httpx
from fasta2a.schema import TaskIdParams, Message, Artifact, TaskSendParams, TextPart

from src.base import storage, broker, Context
from fasta2a import FastA2A, Worker

SUMMARIZER_URL = "http://localhost:8001/"
CLASSIFIER_URL = "http://localhost:8002/"

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
                    "kind": "text", # NOT INPUT_TEXT LMFAO
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
    "id": "1234" # does this need to be anything?
}

print("Starting Director Agent...")
class DirectorWorker(Worker[Context]):
    async def run_task(self, params: TaskSendParams):
        async with httpx.AsyncClient() as client:
            try:
                task = await self.storage.load_task(params["id"])
                assert task is not None

                await self.storage.update_task(task["id"], state="working")

                context = await self.storage.load_context(task["context_id"]) or []
                context.extend(task.get("history", []))

                print("calling summarizer and classifier")
                text = params.get("message").get("parts")[0].get("text", "")

                # build proper payloads
                payload = A2A_MESSAGE_TEMPLATE.copy()
                payload["params"]["message"]["parts"][0]["text"] = text

                # summarizer task ask
                sum_resp = await client.post(SUMMARIZER_URL, json=payload)
                summary = sum_resp.json()
                summary_task_id = summary["result"]["id"] # use this to get task

                # get response (doesn't poll bc instantaneous in local dev)
                summary_task_get_payload = copy.deepcopy(A2A_GET_TASK_TEMPLATE)
                summary_task_get_payload["params"]["id"] = summary_task_id
                summary_response = await client.post(SUMMARIZER_URL, json=summary_task_get_payload)
                summary = summary_response.json()

                last_part = summary["result"]["history"][-1]

                await self.storage.update_context(task["context_id"], last_part)
                await self.storage.update_task(
                    task["id"],
                    state="completed",
                    new_messages=[last_part],
                )

                # classifier
                classifier_post = await client.post(CLASSIFIER_URL, json=payload)
                classifier_post_response = classifier_post.json()
                classifier_task_id = classifier_post_response["result"]["id"]

                classifier_get_payload = copy.deepcopy(A2A_GET_TASK_TEMPLATE)

                classifier_get_payload["params"]["id"] = classifier_task_id
                class_resp_raw = await client.post(CLASSIFIER_URL, json=classifier_get_payload)
                class_resp = class_resp_raw.json()


                label = class_resp["result"]["history"][-1]

                await self.storage.update_context(task["context_id"], label)
                await self.storage.update_task(
                    task["id"],
                    state="completed",
                    new_messages=[label],
                )

            except Exception as e:
                print("Error during director task:", e)
                context.result = {
                    "summary": "error",
                    "label": "error",
                }


    async def cancel_task(self, params: TaskIdParams) -> None: ...

    def build_message_history(self, history: list[Message]) -> list[Any]: ...

    def build_artifacts(self, result: Any) -> list[Artifact]: ...

worker = DirectorWorker(storage=storage, broker=broker)

@asynccontextmanager
async def lifespan(app: FastA2A) -> AsyncIterator[None]:
    async with app.task_manager:
        async with worker.run():
            yield

app = FastA2A(storage=storage, broker=broker, lifespan=lifespan)