# run_all.py
"""Dynamically load and run agents from configuration."""
import uvicorn
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI
from src.registry import create_db_and_tables
from src.registry.api import router as registry_router
from src.agents.factory import create_agents_from_config, get_agent_mount_path


# Create and mount agents dynamically (before lifespan)
agents = create_agents_from_config()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Combined lifespan for all agents."""
    # Initialize database and create tables
    create_db_and_tables()
    
    # Start all agents in parallel
    if agents:
        # Create context managers for all agent lifespans
        from contextlib import AsyncExitStack
        async with AsyncExitStack() as stack:
            for agent_name, (agent_app, agent_lifespan) in agents.items():
                await stack.enter_async_context(agent_lifespan(agent_app))
            yield
    else:
        yield


main_app = FastAPI(lifespan=lifespan)

# Mount agents
for agent_name, (agent_app, _) in agents.items():
    mount_path = get_agent_mount_path(agent_name)
    main_app.mount(mount_path, agent_app)
    print(f"📌 Mounted {agent_name} at {mount_path}")

# Include registry API
main_app.include_router(registry_router)

# Export main_app for CLI
__all__ = ["main_app"]

if __name__ == "__main__":
    # Allow direct execution for backwards compatibility
    import uvicorn
    uvicorn.run(main_app, host="0.0.0.0", port=8000)
