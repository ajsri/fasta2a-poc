# Fast A2A (Agent-to-Agent) Proof of Concept - Team Poseidon

A proof-of-concept implementation demonstrating Agent-to-Agent (A2A) communication using the FastA2A framework. This project showcases a multi-agent architecture where a **Director Agent** orchestrates tasks between specialized agents (**Summarizer** and **Classifier**) using a standardized JSON-RPC protocol.
## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fasta2a-poc
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Initialize the agent registry**
   ```bash
   uv run python -m src.cli registry init
   uv run python -m src.cli registry migrate
   ```
   
   This loads agent definitions from `migrations/agents/` into the database.

4. **(Optional) Set up Docker Model Runner for LLM support**
   
   To use the LLM features, you'll need Docker Model Runner running:
   ```bash
   # Enable Docker Model Runner in Docker Desktop (Settings > AI)
   # Pull the oss-gpt model
   docker model pull ai/oss-gpt
   ```
   
   If Docker Model Runner is not available, the agents will use fallback logic (keyword matching for classification, truncation for summarization).

5. **Run the unified server**
   ```bash
   uv run python -m src.cli run
   ```
   
   This starts all agents on port 8000. Access the API docs at [http://localhost:8000/director/docs](http://localhost:8000/director/docs)
   
   For development with auto-reload:
   ```bash
   uv run python -m src.cli run --reload
   ```

5. **Test the API**
   
   Send a message to the director agent:
```json
{
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
                    "text": "I need to file a claim for my heart condition"
                }
            ]
        }
    },
    "id": 1
}
```
## Architecture Overview

```
                    User Request
                         |
                         v
            +------------------------+
            |   Director Agent       |
            |   (Port 8003)          |
            |   - Orchestrates tasks |
            |   - Aggregates results |
            +----------+------+------+
                       |      |
          +------------+      +------------+
          |                                |
          v                                v
+-----------------------+      +-----------------------+
| Summarizer Agent      |      | Classifier Agent      |
| (Port 8001)           |      | (Port 8002)           |
| - Text summarization  |      | - Text classification |
| - Returns summary     |      | - Returns label       |
+-----------------------+      +-----------------------+
```

## Features

- **Director Agent**: Central orchestrator that receives user input and coordinates between specialized agents
- **Summarizer Agent**: Processes text and returns a condensed summary using ADK
- **Classifier Agent**: Analyzes text and returns a classification label (insurance, medical, or general) using ADK
- **A2A Protocol**: JSON-RPC 2.0-based standardized communication between agents
- **ADK Integration**: All agents use Google's ADK framework for LLM interactions
- **MCP Support**: Model Context Protocol integration for exposing APIs as LLM-accessible tools
- **Agent Registry**: SQLModel-based dynamic agent discovery and registration system
- **Async Task Management**: Built on asyncio for concurrent task handling
- **Flexible Deployment**: Run agents individually or as a unified service
- **Code Quality**: Integrated Ruff linting and formatting for maintaining code standards

## Technology Stack

- **FastA2A** - Agent-to-Agent protocol framework
- **Google ADK** - Agent Development Kit for building AI agents
- **FastAPI** - Modern web framework for building APIs
- **FastMCP** - Model Context Protocol integration for exposing APIs to LLMs
- **Uvicorn** - ASGI server for running FastAPI applications
- **Python 3.11+** - Core programming language
- **Pydantic** - Data validation using type annotations
- **HTTPX** - Async HTTP client for inter-agent communication
- **Ruff** - Fast Python linter and formatter for code quality

## Prerequisites

- Python 3.11 or higher
- pip or uv package manager

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fasta2a-poc
   ```

2. **Install dependencies**

   Using uv (recommended):
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -e .
   ```

3. **Configure LLM settings** (optional)
   
   Edit `config.json` in the project root to customize the LLM model settings:
   ```json
   {
     "model": {
       "endpoint": "http://localhost:12434/v1/chat/completions",
       "name": "oss-gpt",
       "parameters": {
         "temperature": 0.7,
         "max_tokens": 512
       }
     }
   }
   ```
   
   See the [Configuration](#configuration) section for more details.

## Running the Application

### Option 1: Unified Server (Recommended)

Run all three agents on a single FastAPI instance:

```bash
uv run python -m src.cli run
```

Or with custom host/port:

```bash
uv run python -m src.cli run --host 0.0.0.0 --port 8000
```

For development with auto-reload:

```bash
uv run python -m src.cli run --reload
```

This starts all agents on **port 8000** with the following routes:
- `/director/*` - Director agent endpoints
- `/summarizer/*` - Summarizer agent endpoints (ADK-powered)
- `/classifier/*` - Classifier agent endpoints (ADK-powered)

Access the interactive API documentation at:
- Director: [http://localhost:8000/director/docs](http://localhost:8000/director/docs)
- Summarizer: [http://localhost:8000/summarizer/docs](http://localhost:8000/summarizer/docs)
- Classifier: [http://localhost:8000/classifier/docs](http://localhost:8000/classifier/docs)

### CLI Commands

The CLI provides a unified interface for managing the system:

```bash
# Run the server
uv run python -m src.cli run [--host HOST] [--port PORT] [--reload]

# Registry management
uv run python -m src.cli registry init          # Initialize database
uv run python -m src.cli registry migrate       # Load agents from JSON files
uv run python -m src.cli registry list          # List all agents
uv run python -m src.cli registry show NAME     # Show agent details
uv run python -m src.cli registry delete NAME   # Delete an agent

# Help
uv run python -m src.cli --help
uv run python -m src.cli run --help
uv run python -m src.cli registry --help
```

**Note:** With the new config-driven architecture, agents are dynamically loaded from the registry. The recommended approach is to use the unified server (`src.cli run`).

## Usage

### Sending a Message to the Director

The Director agent receives text input and orchestrates calls to both the Summarizer and Classifier agents.

**Endpoint:** `POST http://localhost:8003/` (or `http://localhost:8000/director/` if using unified server)

**Request Body** (JSON-RPC format):
```json
{
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
                    "text": "I need to file a claim for my heart condition"
                }
            ]
        }
    },
    "id": 1
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "id": "task-uuid-here"
    },
    "id": 1
}
```

### Retrieving Task Results

**Endpoint:** `POST http://localhost:8003/`

**Request Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "tasks/get",
    "params": {
        "id": "task-uuid-here"
    },
    "id": 2
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "id": "task-uuid-here",
        "state": "completed",
        "history": [
            {
                "role": "user",
                "kind": "message",
                "messageId": "msg-001",
                "parts": [{"kind": "text", "text": "I need to file a claim for my heart condition"}]
            },
            {
                "role": "agent",
                "kind": "message",
                "messageId": "msg-002",
                "parts": [{
                    "kind": "text",
                    "text": "\nOur behind-the-scenes bots formed the following conclusions:\n## Summary:\nI need to file a claim for my heart condition\n## Label:\ninsurance\n                "
                }]
            }
        ]
    },
    "id": 2
}
```

The director agent returns a single formatted message that combines both the summary and classification from the specialized agents.

## Agent Behavior

### Director Agent (src/director_agent.py:8003)

1. Receives text input from user
2. Forwards text to Summarizer agent via A2A protocol (HTTP)
3. Forwards text to Classifier agent via A2A protocol (HTTP)
4. Aggregates both responses into a formatted message
5. Returns a single combined response with both summary and classification
6. Updates task context and marks task as completed

### Summarizer Agent (src/agents/summarizer_agent.py:8001)

- **ADK-powered summarization**: Uses Google's ADK framework with oss-gpt model to create concise summaries
- **Fallback behavior**: If ADK/LLM is unavailable, returns first 100 characters of input text
- **Output Format**: Summary text from ADK agent or truncated text

### Classifier Agent (src/agents/classifier_agent.py:8002)

- **ADK-powered classification**: Uses Google's ADK framework with oss-gpt model to classify text into categories
- **Categories**: `insurance`, `medical`, or `general`
- **Fallback behavior**: If ADK/LLM is unavailable, uses keyword matching:
  - `"insurance"` - if text contains "claim" or "insurance"
  - `"medical"` - if text contains "heart", "medical", or "condition"
  - `"general"` - default classification
- **Output Format**: Classification label (e.g., `"insurance"`)

## Project Structure

```
fasta2a-poc/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── core/                    # Core utilities and types
│   │   ├── __init__.py          # Core package exports
│   │   ├── types.py             # Shared context type definition
│   │   └── config.py            # Configuration loader for LLM settings
│   ├── integrations/            # External integrations
│   │   ├── adk/                 # Google ADK integration
│   │   │   ├── __init__.py      # ADK package exports
│   │   │   ├── helper.py        # Shared ADK helper for agent creation
│   │   │   └── model.py         # ADK model adapter for oss-gpt
│   │   └── mcp/                 # Model Context Protocol integration
│   │       ├── __init__.py      # MCP package exports
│   │       ├── api.py           # Example MCP-enabled API
│   │       ├── model.py         # Pydantic models for MCP example
│   │       └── demo.py          # MCP demonstration code
│   ├── cli.py                   # Main CLI entrypoint
│   ├── agents/                  # Agent implementations
│   │   ├── __init__.py          # Agent package exports
│   │   ├── base.py              # Base utilities for agents
│   │   ├── factory.py           # Dynamic agent factory
│   │   ├── generic_agent.py     # Generic configurable agent
│   │   └── director_worker.py   # Director agent worker
│   ├── registry/                # Agent registry
│   │   ├── __init__.py          # Registry package exports
│   │   ├── cli.py               # Registry CLI commands
│   │   ├── models.py            # Database models
│   │   ├── service.py           # Registry service
│   │   ├── api.py               # Registry REST API
│   │   └── database.py          # Database setup
│   └── run_all.py               # Unified multi-agent server
├── migrations/                  # Agent definitions
│   └── agents/                  # Agent JSON files
│       ├── classifier_agent.json
│       ├── summarizer_agent.json
│       └── director_agent.json
├── examples/                    # Example code
│   └── simple_agent_example.py  # Simple agent example
├── tests/                       # Test suite
│   ├── test_agents/             # Agent tests
│   ├── test_integrations/       # Integration tests
│   └── test_core/               # Core utility tests
├── pyproject.toml               # Project dependencies and metadata
├── config.json                  # LLM model and agent configuration
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Configuration

The application uses `config.json` in the project root to configure LLM model settings. All agents use the same model configuration by default.

### Configuration File Structure

```json
{
  "model": {
    "endpoint": "http://localhost:12434/v1/chat/completions",
    "name": "oss-gpt",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 512
    }
  },
  "agents": {
    "summarizer_url": "http://localhost:8000/summarizer/",
    "classifier_url": "http://localhost:8000/classifier/"
  }
}
```

### Configuration Options

- **`model.endpoint`**: The API endpoint URL for the LLM service (OpenAI-compatible API)
  - Default: `http://localhost:12434/v1/chat/completions` (Docker Model Runner)
  - For Docker Model Runner, ensure host-side TCP support is enabled
  - For other services, update to match your endpoint
  - If you experience issues with your Docker endpoint, try the following: `"endpoint": "http://localhost:12434/engines/llama.cpp/v1/chat/completions"`
  - Ensure your model name matches the Docker Model Runner model listing name

- **`model.name`**: The model identifier to use
  - Default: `oss-gpt`
  - Should match the model name available at your endpoint

- **`model.parameters.temperature`**: Controls randomness in model output (0.0-2.0)
  - Default: `0.7`
  - Lower values (0.0-0.3) for more deterministic outputs
  - Higher values (0.7-2.0) for more creative outputs

- **`model.parameters.max_tokens`**: Maximum number of tokens in the response
  - Default: `512`
  - Adjust based on your needs and model limits

- **`agents.summarizer_url`**: The endpoint URL for the summarizer agent
  - Default: `http://localhost:8000/summarizer/` (unified server)
  - Update to `http://localhost:8001/` if running agents individually

- **`agents.classifier_url`**: The endpoint URL for the classifier agent
  - Default: `http://localhost:8000/classifier/` (unified server)
  - Update to `http://localhost:8002/` if running agents individually

### Docker Model Runner Setup

To use the oss-gpt model with Docker Model Runner:

1. **Enable Docker Model Runner**:
   - Open Docker Desktop
   - Go to **Settings** > **AI**
   - Enable **Docker Model Runner**
   - Optionally enable **host-side TCP support** to access from `localhost`

2. **Pull the model**:
   ```bash
   docker model pull ai/oss-gpt
   ```

3. **Verify the model is running**:
   ```bash
   curl http://localhost:12434/v1/models
   ```

4. **Update `config.json`** if needed (defaults should work)

### Using a Different LLM Service

To use a different LLM service (e.g., OpenAI, Anthropic, local model):

1. Update `config.json` with your endpoint and model name:
   ```json
   {
     "model": {
       "endpoint": "https://api.openai.com/v1/chat/completions",
       "name": "gpt-3.5-turbo",
       "parameters": {
         "temperature": 0.7,
         "max_tokens": 512
       }
     }
   }
   ```

2. If authentication is required, you may need to modify `src/integrations/adk/model.py` to add API keys to request headers.

### Fallback Behavior

If the LLM endpoint is unavailable or returns an error:
- **Classifier Agent**: Falls back to keyword-based classification
- **Summarizer Agent**: Falls back to text truncation (first 100 characters)

This ensures the system continues to function even when the LLM service is down.

## MCP (Model Context Protocol) Integration

The project includes FastMCP integration, which allows you to expose FastAPI endpoints as tools that LLMs can discover and use via the Model Context Protocol. This enables AI agents to interact with your APIs in a structured, LLM-friendly way.

### What is MCP?

Model Context Protocol (MCP) is a standard protocol that allows LLMs to discover and interact with external tools and APIs. By exposing your FastAPI endpoints through MCP, you enable:
- **Tool Discovery**: LLMs can automatically discover available API endpoints
- **Structured Interaction**: APIs are exposed with clear schemas and descriptions
- **Seamless Integration**: Works with Claude, GPT, and other MCP-compatible LLMs

### MCP Example

An example MCP integration is provided in `src/integrations/mcp/api.py` that demonstrates:
- Exposing a FastAPI e-commerce API through MCP
- Creating custom MCP tools for LLM interaction
- Combining regular API routes with MCP endpoints

**Running the MCP Example:**

```bash
uv run python -m src.integrations.mcp.api
```

This starts a server with:
- **Regular API**: `http://localhost:8000/products` - Standard REST endpoints
- **MCP Protocol**: `http://localhost:8000/mcp` - LLM-accessible tools

**Key Features:**
- Automatic tool generation from FastAPI routes
- Custom tool definitions with `@mcp.tool` decorator
- Unified server serving both REST API and MCP protocol

**Example MCP Tools:**
```python
@mcp.tool
def get_product_by_id(product_id: int) -> ProductResponse:
    """Get a product by ID."""
    return products_db[product_id]

@mcp.tool
def debug_tool(message: str) -> str:
    """A simple debug tool that echoes the message."""
    return f"Debug: {message}"
```

### Integrating MCP in Your Agents

To add MCP capabilities to your own agents:

1. Import FastMCP: `from fastmcp import FastMCP`
2. Create an MCP instance from your FastAPI app:
   ```python
   mcp = FastMCP.from_fastapi(app=app, name="My Agent MCP")
   ```
3. Optionally add custom tools with the `@mcp.tool` decorator
4. Combine the routes:
   ```python
   combined_app = FastAPI(
       routes=[*mcp.http_app(path='/mcp').routes, *app.routes]
   )
   ```

For more details, see the [FastMCP documentation](https://gofastmcp.com/).

## Development Tools

### Code Quality with Ruff

This project uses **Ruff** for fast Python linting and code formatting. Ruff is an extremely fast Python linter and formatter written in Rust, combining the functionality of multiple tools (Flake8, isort, Black, etc.) into a single binary.

**Installation:**

Ruff is included in the dev dependencies. Install with:
```bash
uv sync --group dev
```

**Common Commands:**

```bash
# Check code for linting issues
uv run ruff check .

# Automatically fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Check formatting without making changes
uv run ruff format --check .
```

**Configuration:**

Ruff can be configured via `pyproject.toml`, `ruff.toml`, or `.ruff.toml`. Add configuration as needed:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]  # Enable specific rule sets
```

**Benefits:**
- **Speed**: 10-100x faster than traditional Python linters
- **All-in-one**: Replaces Flake8, isort, Black, and more
- **Auto-fix**: Automatically fixes many common issues
- **Editor Integration**: Works with VS Code, PyCharm, and other editors

## Development Notes

### In-Memory Storage

The current implementation uses `InMemoryStorage` from FastA2A, which means:
- All task state is stored in memory
- No persistence across server restarts
- Not suitable for production use
- Great for development and testing

**Note:** Each agent (summarizer, classifier, and director) has its own isolated storage and broker instances to prevent task ID collisions and ensure proper isolation between agents.

### Message Format

All inter-agent communication follows the A2A protocol specification:
- **Protocol**: JSON-RPC 2.0
- **Message Structure**: Role, kind, messageId, parts[]
- **Part Types**: text (with support for other types in the future)

### Error Handling

Each agent implements basic error handling:
- Exceptions are caught and logged
- Tasks are marked as `"failed"` with error messages
- Director returns fallback values on downstream agent failures

## Future Enhancements

- [x] **LLM Integration**: Integrated oss-gpt model from Docker Model Runner with configurable settings
- [x] **ADK Integration**: All agents now use Google's Agent Development Kit (ADK) framework
- [x] **MCP Integration**: FastMCP support for exposing APIs as LLM-accessible tools
- [x] **Agent Registry**: Dynamic agent discovery and registration (SQLModel-based)
- [x] **Code Quality Tools**: Integrated Ruff for fast linting and formatting
- [ ] **Persistent Storage**: Add Redis/PostgreSQL for production-ready state management
- [ ] **Authentication**: Implement API key or OAuth for secure agent communication
- [ ] **Monitoring**: Add metrics, logging, and observability (Prometheus, Grafana)
- [ ] **Streaming Responses**: Support real-time streaming for long-running tasks
- [ ] **Parallel Execution**: Optimize Director to call agents in parallel
- [ ] **Advanced Classification**: Multi-label classification with confidence scores
- [ ] **Retry Logic**: Implement exponential backoff for failed agent calls
- [ ] **Rate Limiting**: Add request throttling and quota management

## Testing

To test the `tasks/get` endpoint, first send a message to get a task ID, then retrieve the task:

```bash
# Send a message and get task ID
TASK_ID=$(curl -s -X POST http://localhost:8000/director/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "message/send", "params": {"message": {"role": "user", "kind": "message", "messageId": "msg-001", "parts": [{"kind": "text", "text": "test message"}]}}, "id": 1}' \
  | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

# Get task results
curl -X POST http://localhost:8000/director/ \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\": \"2.0\", \"method\": \"tasks/get\", \"params\": {\"id\": \"$TASK_ID\"}, \"id\": 2}"
```

## Contributing

This is a proof-of-concept project. Contributions, suggestions, and feedback are welcome!

## License

[Specify your license here]

## Support

For questions or issues, please [open an issue](../../issues) on the repository.

---

**Built with [FastA2A](https://github.com/langstack-ai/fasta2a)** - A framework for building Agent-to-Agent systems.
