"""Pydantic models for configuration validation.

Enhancement 017: Production Architecture - Phase 0.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Literal
from enum import Enum


class ProviderTier(str, Enum):
    """Provider cost tier."""
    FREE = "free"
    PAID = "paid"


class ProviderPriority(str, Enum):
    """Provider priority level."""
    HIGHEST = "highest"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProviderBackend(str, Enum):
    """LLM backend type."""
    OLLAMA = "ollama"
    VLLM = "vllm"
    API = "api"


class Environment(str, Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    requests_per_minute: Optional[int] = Field(None, ge=1)
    requests_per_day: Optional[int] = Field(None, ge=1)
    tokens_per_minute: Optional[int] = Field(None, ge=1)


class HealthCheckConfig(BaseModel):
    """Health check configuration."""
    enabled: bool = Field(default=True)
    interval_seconds: int = Field(default=60, ge=10, le=3600)
    endpoint: Optional[str] = None
    timeout_seconds: int = Field(default=5, ge=1, le=30)


class ModelConfig(BaseModel):
    """Individual model configuration."""
    name: str
    use_case: str  # code, general, chat, etc.
    context_window: Optional[int] = Field(None, ge=1024)
    max_tokens: Optional[int] = Field(None, ge=100)


class ProviderConfig(BaseModel):
    """Provider configuration."""
    enabled: bool = Field(default=True)
    priority: ProviderPriority = Field(default=ProviderPriority.MEDIUM)
    tier: ProviderTier
    backend: Optional[ProviderBackend] = None
    cost_per_1k_tokens: float = Field(ge=0.0)
    endpoint: Optional[str] = None
    models: List[ModelConfig] = Field(default_factory=list)
    rate_limit: Optional[RateLimitConfig] = None
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    notes: Optional[str] = None


class RoutingConfig(BaseModel):
    """Routing configuration."""
    prefer_free: bool = Field(default=True)
    fallback_to_paid: bool = Field(default=True)
    default_chain: List[str] = Field(default_factory=list)
    intent_overrides: Dict[str, List[str]] = Field(default_factory=dict)

    @field_validator('default_chain')
    @classmethod
    def validate_chain_not_empty(cls, v):
        """Ensure default chain has at least one provider."""
        if not v:
            raise ValueError("default_chain must have at least one provider")
        return v


class FeaturesConfig(BaseModel):
    """Feature flags configuration."""
    verbose_logging: bool = Field(default=False)
    debug_mode: bool = Field(default=False)
    mock_github: bool = Field(default=False)
    mock_docker: bool = Field(default=False)
    prometheus_enabled: bool = Field(default=True)
    prometheus_port: int = Field(default=9090, ge=1024, le=65535)
    tracing_enabled: bool = Field(default=True)
    tracing_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    mongodb_enabled: bool = Field(default=False)
    mongodb_connection: Optional[str] = None
    redis_enabled: bool = Field(default=False)
    redis_connection: Optional[str] = None


class LimitsConfig(BaseModel):
    """System limits configuration."""
    max_concurrent_requests: int = Field(default=50, ge=1, le=1000)
    max_tokens_per_request: int = Field(default=8000, ge=100, le=128000)
    request_timeout_seconds: int = Field(default=300, ge=10, le=3600)


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    health_check_interval: int = Field(default=60, ge=10, le=3600)
    metrics_port: int = Field(default=8000, ge=1024, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")


class ProvidersEnvironmentConfig(BaseModel):
    """Complete provider environment configuration.

    This model validates the entire providers_{env}.yaml file.
    """
    environment: Environment
    providers: Dict[str, ProviderConfig]
    routing: RoutingConfig
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    @field_validator('providers')
    @classmethod
    def validate_at_least_one_enabled(cls, v):
        """Ensure at least one provider is enabled."""
        if not any(p.enabled for p in v.values()):
            raise ValueError("At least one provider must be enabled")
        return v

    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names."""
        return [name for name, config in self.providers.items() if config.enabled]

    def get_free_providers(self) -> List[str]:
        """Get list of free-tier enabled providers."""
        return [
            name
            for name, config in self.providers.items()
            if config.enabled and config.tier == ProviderTier.FREE
        ]

    def get_provider_by_priority(self, priority: ProviderPriority) -> List[str]:
        """Get providers by priority level."""
        return [
            name
            for name, config in self.providers.items()
            if config.enabled and config.priority == priority
        ]


# Type alias for convenience
ProviderEnvConfig = ProvidersEnvironmentConfig
