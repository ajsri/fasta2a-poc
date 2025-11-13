"""Seed initial agent data into the registry (deprecated - use migrate command instead)."""
from pathlib import Path
from src.registry import create_db_and_tables
from src.registry.migrations import migrate_agents


def seed_agents():
    """Seed initial agent cards from JSON files (uses migration)."""
    # Create database tables
    create_db_and_tables()
    
    # Use migration to load from JSON files
    agents_dir = Path("migrations/agents")
    if not agents_dir.exists():
        print(f"⚠️  Directory {agents_dir} does not exist. Skipping seed.")
        return 0
    
    results = migrate_agents(agents_dir, force=False)
    print(f"✅ Seeded {results['created']} agents")
    if results['updated'] > 0:
        print(f"🔄 Updated {results['updated']} agents")
    if results['skipped'] > 0:
        print(f"⏭️  Skipped {results['skipped']} agents (already exist)")
    if results['errors']:
        print(f"❌ Errors: {results['errors']}")
    
    return results['created']


# Legacy function - kept for backwards compatibility
def seed_agents_legacy():
        AgentCardSpecCreate(
            name="Classifier Agent",
            agent_type=AgentType.CLASSIFIER,
            version="0.0.1",
            description="Classifies input text using ADK with fallback to keyword matching",
            status=AgentStatus.ACTIVE,
            endpoint_url="http://localhost:8000/classifier/",
            system_prompt="""You are a text classification assistant. Your task is to classify the given text into one of these categories:
- insurance: Text related to insurance claims, policies, coverage, etc.
- medical: Text related to medical conditions, health issues, treatments, etc.
- general: Any other text that doesn't fit the above categories

Respond with ONLY the classification label (insurance, medical, or general) and nothing else.""",
            uses_adk=True,
            adk_model_name="oss-gpt",
            config={
                "categories": ["insurance", "medical", "general"],
                "fallback_keywords": {
                    "insurance": ["claim", "insurance"],
                    "medical": ["heart", "medical", "condition"]
                }
            }
        ),
        AgentCardSpecCreate(
            name="Summarizer Agent",
            agent_type=AgentType.SUMMARIZER,
            version="0.0.1",
            description="Summarizes input text using ADK with fallback to truncation",
            status=AgentStatus.ACTIVE,
            endpoint_url="http://localhost:8000/summarizer/",
            system_prompt="""You are a text summarization assistant. Your task is to create a concise summary of the given text. 
The summary should:
- Capture the main points and key information
- Be clear and concise
- Preserve important details
- Be significantly shorter than the original text

Provide only the summary without any additional commentary or labels.""",
            uses_adk=True,
            adk_model_name="oss-gpt",
            config={
                "fallback_length": 100,
                "max_tokens": 256
            }
        ),
        AgentCardSpecCreate(
            name="Director Agent",
            agent_type=AgentType.DIRECTOR,
            version="0.0.1",
            description="Central orchestrator that receives user input and coordinates between specialized agents",
            status=AgentStatus.ACTIVE,
            endpoint_url="http://localhost:8000/director/",
            system_prompt=None,
            uses_adk=False,
            config={
                "orchestrates": ["Summarizer Agent", "Classifier Agent"]
            }
        ),
    ]
    
    # Create agents (skip if already exists)
    created_count = 0
    for agent_data in initial_agents:
        existing = service.get_agent_by_name(agent_data.name)
        if not existing:
            service.create_agent(agent_data)
            created_count += 1
            print(f"✅ Created agent: {agent_data.name}")
        else:
            print(f"⏭️  Agent already exists: {agent_data.name}")
    
    print(f"\n📊 Seeded {created_count} new agents")
    return created_count


if __name__ == "__main__":
    # Use new migration-based seeding
    seed_agents()

