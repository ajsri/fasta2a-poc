"""Configuration loader for LLM model settings."""
import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class ModelParameters(BaseModel):
    """Model generation parameters."""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, gt=0)


class ModelConfig(BaseModel):
    """Model configuration."""
    endpoint: str = Field(default="http://localhost:12434/v1/chat/completions")
    name: str = Field(default="oss-gpt")
    parameters: ModelParameters = Field(default_factory=ModelParameters)


class AgentsConfig(BaseModel):
    """Agent configuration."""
    directory: str = Field(default="migrations/agents", description="Directory containing agent JSON files")
    load: list[str] = Field(default_factory=lambda: ["Summarizer Agent", "Classifier Agent", "Director Agent"], description="List of agent names to load")


class Config(BaseModel):
    """Application configuration."""
    model: ModelConfig = Field(default_factory=ModelConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)


def load_config(config_path: str | Path | None = None) -> Config:
    """
    Load configuration from config.json file.
    
    Args:
        config_path: Path to config.json file. If None, looks for config.json
                     in the project root directory.
    
    Returns:
        Config object with loaded or default values.
    """
    if config_path is None:
        # Find project root (where config.json should be)
        # Go up from src/core/config.py -> src/core -> src -> project root
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        config_path = project_root / "config.json"
    else:
        config_path = Path(config_path)
    
    # If config file doesn't exist, return defaults
    if not config_path.exists():
        print(f"Warning: config.json not found at {config_path}. Using default configuration.")
        return Config()
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Validate and parse configuration
        return Config(**config_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config.json: {e}. Using default configuration.")
        return Config()
    except Exception as e:
        print(f"Error loading config.json: {e}. Using default configuration.")
        return Config()


# Global config instance (lazy-loaded)
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance (singleton)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config

