"""Configuration management for the AI Orchestrator."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Keys
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    google_api_key: str = Field(default="")

    # Local LLM Configuration
    local_llm_enabled: bool = Field(default=True)
    local_llm_base_url: str = Field(default="http://localhost:11434")
    local_llm_model: str = Field(default="llama2:13b")
    local_llm_timeout: int = Field(default=120)

    # Claude Code Integration
    claude_code_cli_path: str = Field(default="/usr/local/bin/claude")
    claude_code_project_root: str = Field(default="/path/to/projects")

    # GitHub Integration
    github_token: str = Field(default="")
    github_api_url: str = Field(default="https://api.github.com")

    # CI/CD Integration
    jenkins_url: str = Field(default="")
    jenkins_user: str = Field(default="")
    jenkins_token: str = Field(default="")
    github_actions_token: str = Field(default="")

    # Docker/Kubernetes
    docker_host: str = Field(default="unix:///var/run/docker.sock")
    kubernetes_config_path: str = Field(default="~/.kube/config")

    # Monitoring
    grafana_url: str = Field(default="")
    grafana_api_key: str = Field(default="")
    prometheus_url: str = Field(default="")

    # Logging
    elasticsearch_url: str = Field(default="")
    elasticsearch_username: str = Field(default="elastic")
    elasticsearch_password: str = Field(default="")
    splunk_url: str = Field(default="")
    splunk_token: str = Field(default="")
    aws_region: str = Field(default="us-east-1")
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")

    # Orchestrator Settings
    orchestrator_host: str = Field(default="0.0.0.0")
    orchestrator_port: int = Field(default=8000)
    orchestrator_workers: int = Field(default=4)
    log_level: str = Field(default="INFO")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Quality Check Settings
    quality_check_enabled: bool = Field(default=True)
    quality_check_min_length: int = Field(default=50)
    quality_check_confidence_threshold: float = Field(default=0.7)

    # Fallback Settings
    fallback_enabled: bool = Field(default=True)
    fallback_timeout: int = Field(default=30)
    fallback_max_retries: int = Field(default=3)

    def validate_provider_config(self) -> dict[str, bool]:
        """Validate which providers are properly configured."""
        return {
            "claude_code": bool(self.anthropic_api_key),
            "chatgpt": bool(self.openai_api_key),
            "gemini": bool(self.google_api_key),
            "claude": bool(self.anthropic_api_key),
            "local": self.local_llm_enabled
        }


# Global settings instance
settings = Settings()
