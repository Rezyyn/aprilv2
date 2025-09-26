"""Configuration management for April v2."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    name: str
    max_tokens: int = 4096
    capabilities: List[str] = Field(default_factory=list)
    max_size: Optional[str] = None
    max_duration: Optional[int] = None


class ProviderConfig(BaseModel):
    """Configuration for a provider."""
    enabled: bool = False
    weight: float = 0.0
    models: List[ModelConfig] = Field(default_factory=list)
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    voices: Optional[List[Dict[str, str]]] = None


class ProvidersConfig(BaseModel):
    """Configuration for all providers."""
    llm: Dict[str, ProviderConfig] = Field(default_factory=dict)
    speech: Dict[str, ProviderConfig] = Field(default_factory=dict)
    image: Dict[str, ProviderConfig] = Field(default_factory=dict)
    video: Dict[str, ProviderConfig] = Field(default_factory=dict)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    loki: Dict[str, Any] = Field(default_factory=dict)


class CoreConfig(BaseModel):
    """Core manager configuration."""
    memory: Dict[str, Any] = Field(default_factory=dict)
    persona: Dict[str, Any] = Field(default_factory=dict)
    system_prompts: Dict[str, Any] = Field(default_factory=dict)


class Settings(BaseSettings):
    """Application settings."""
    
    # FastAPI settings
    app_name: str = "April v2"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Provider configuration file path
    providers_config_path: str = "providers.yml"
    
    # Loaded provider configuration
    providers: Optional[ProvidersConfig] = None
    logging: Optional[LoggingConfig] = None
    core: Optional[CoreConfig] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def load_providers_config(self) -> None:
        """Load providers configuration from YAML file."""
        config_path = Path(self.providers_config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Providers config file not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        # Parse providers configuration
        if "providers" in config_data:
            self.providers = ProvidersConfig.model_validate(config_data["providers"])
        
        # Parse logging configuration
        if "logging" in config_data:
            self.logging = LoggingConfig.model_validate(config_data["logging"])
        
        # Parse core configuration
        if "core" in config_data:
            self.core = CoreConfig.model_validate(config_data["core"])

    def get_enabled_providers(self, provider_type: str) -> Dict[str, ProviderConfig]:
        """Get enabled providers for a specific type."""
        if not self.providers:
            return {}
        
        provider_configs = getattr(self.providers, provider_type, {})
        return {
            name: config
            for name, config in provider_configs.items()
            if config.enabled
        }

    def get_provider_api_key(self, provider_config: ProviderConfig) -> Optional[str]:
        """Get API key for a provider from environment variables."""
        if not provider_config.api_key_env:
            return None
        return os.getenv(provider_config.api_key_env)


# Global settings instance
settings = Settings()