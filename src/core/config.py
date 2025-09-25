"""Configuration management for April Core service."""

import os
import yaml
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    name: str
    weight: int = 100


class ProviderConfig(BaseModel):
    """Configuration for a provider."""
    enabled: bool = True
    api_key: str
    base_url: str
    capabilities: List[str] = Field(default_factory=list)
    models: Dict[str, List[ModelConfig]] = Field(default_factory=dict)


class LokiConfig(BaseModel):
    """Configuration for Loki logging."""
    enabled: bool = True
    url: str = "http://localhost:3100"
    labels: Dict[str, str] = Field(default_factory=dict)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    loki: LokiConfig = Field(default_factory=LokiConfig)


class Config(BaseSettings):
    """Main application configuration."""
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def load_config(config_path: str = "config/providers.yml") -> Config:
    """Load configuration from YAML file with environment variable substitution."""
    
    def substitute_env_vars(obj: Any) -> Any:
        """Recursively substitute environment variables in configuration."""
        if isinstance(obj, dict):
            return {k: substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Handle ${VAR} and ${VAR:default} patterns
            if obj.startswith("${") and obj.endswith("}"):
                var_expr = obj[2:-1]
                if ":" in var_expr:
                    var_name, default_value = var_expr.split(":", 1)
                    return os.getenv(var_name, default_value)
                else:
                    var_name = var_expr
                    env_value = os.getenv(var_name)
                    if env_value is None:
                        raise ValueError(f"Environment variable {var_name} is required but not set")
                    return env_value
        return obj
    
    if not os.path.exists(config_path):
        return Config()
    
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)
    
    # Substitute environment variables
    config_data = substitute_env_vars(raw_config)
    
    # Convert models list to ModelConfig objects
    if "providers" in config_data:
        for provider_name, provider_data in config_data["providers"].items():
            if "models" in provider_data:
                for capability, models in provider_data["models"].items():
                    provider_data["models"][capability] = [
                        ModelConfig(**model) if isinstance(model, dict) else model
                        for model in models
                    ]
    
    return Config(**config_data)


# Global configuration instance - lazy loading
_config = None

def get_config() -> Config:
    """Get the global configuration instance, loading it if necessary."""
    global _config
    if _config is None:
        _config = load_config()
    return _config