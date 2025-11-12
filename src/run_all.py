# run_all.py
import asyncio
import uvicorn
from fastapi import FastAPI
from src.summarizer_agent import app as summarizer_app
from src.classifier_agent import app as classifier_app
from src.director_agent import app as director_app

main_app = FastAPI()

@main_app.on_event("startup")
async def start_agents():
    # Manually run each FastA2A startup hook (initialize TaskManager + Worker)
    await summarizer_app.router.startup()
    await classifier_app.router.startup()
    await director_app.router.startup()

@main_app.on_event("shutdown")
async def stop_agents():
    await summarizer_app.router.shutdown()
    await classifier_app.router.shutdown()
    await director_app.router.shutdown()

# Mount them AFTER startup handlers are defined
main_app.mount("/summarizer", summarizer_app)
main_app.mount("/classifier", classifier_app)
main_app.mount("/director", director_app)

if __name__ == "__main__":
    uvicorn.run(main_app, host="0.0.0.0", port=8000)
