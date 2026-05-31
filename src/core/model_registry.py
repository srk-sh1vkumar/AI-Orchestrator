"""Model Registry for managing custom and fine-tuned models."""

from typing import Dict, List, Optional
from datetime import datetime
import structlog
from src.models.schemas import (
    LLMProvider,
    ModelMetadata,
    ModelCapabilities,
    ModelRegistryEntry,
)

logger = structlog.get_logger()


class ModelRegistry:
    """Registry for managing custom models with metadata and health tracking."""

    def __init__(self):
        """Initialize the model registry."""
        self.models: Dict[str, ModelRegistryEntry] = {}
        self._initialize_default_models()

    def _initialize_default_models(self):
        """Initialize registry with default models."""
        # DeepSeek-Coder 6.7B
        deepseek_metadata = ModelMetadata(
            model_id="deepseek-coder-6.7b",
            provider=LLMProvider.DEEPSEEK,
            model_name="deepseek-coder:6.7b",
            version="1.0.0",
            description="DeepSeek-Coder 6.7B specialized for code generation and analysis",
            capabilities=ModelCapabilities(
                code_generation=True,
                code_analysis=True,
                debugging=True,
                documentation=True,
                refactoring=True,
                testing=True,
                general_chat=False,
                technical_writing=True,
            ),
            parameters={
                "size_gb": 3.8,
                "quantization": "4-bit",
                "context_window": 16384,
                "architecture": "deepseek-coder",
                "backend": "ollama",
            },
            performance_metrics={
                "tokens_per_sec": 12.0,  # Estimated for M1 Pro
                "avg_latency_ms": 150.0,
                "context_window_tokens": 16384,
            },
            cost_per_million_tokens=0.0,  # Local model, no API cost
            is_local=True,
            requires_gpu=False,  # Works on CPU, accelerated by Metal on M1
            tags=["code", "local", "ollama", "4-bit", "specialized"],
            enabled=True,
        )
        self.register_model(deepseek_metadata)

        # Llama2 7B
        llama2_metadata = ModelMetadata(
            model_id="llama2-7b",
            provider=LLMProvider.LLAMA2,
            model_name="llama2:7b",
            version="1.0.0",
            description="Llama2 7B for general log analysis and incident analysis",
            capabilities=ModelCapabilities(
                code_generation=False,
                code_analysis=True,
                debugging=False,
                documentation=False,
                refactoring=False,
                testing=False,
                general_chat=True,
                technical_writing=True,
            ),
            parameters={
                "size_gb": 3.8,
                "quantization": "default",
                "context_window": 4096,
                "architecture": "llama2",
                "backend": "ollama",
            },
            performance_metrics={
                "tokens_per_sec": 10.0,
                "avg_latency_ms": 200.0,
                "context_window_tokens": 4096,
            },
            cost_per_million_tokens=0.0,
            is_local=True,
            requires_gpu=False,
            tags=["general", "local", "ollama", "log-analysis"],
            enabled=True,
        )
        self.register_model(llama2_metadata)

        # CodeLlama 7B
        codellama_metadata = ModelMetadata(
            model_id="codellama-7b",
            provider=LLMProvider.CODELLAMA,
            model_name="codellama:7b",
            version="1.0.0",
            description="CodeLlama 7B for code-related incident analysis",
            capabilities=ModelCapabilities(
                code_generation=True,
                code_analysis=True,
                debugging=True,
                documentation=True,
                refactoring=True,
                testing=True,
                general_chat=False,
                technical_writing=True,
            ),
            parameters={
                "size_gb": 3.8,
                "quantization": "default",
                "context_window": 16384,
                "architecture": "codellama",
                "backend": "ollama",
            },
            performance_metrics={
                "tokens_per_sec": 11.0,
                "avg_latency_ms": 180.0,
                "context_window_tokens": 16384,
            },
            cost_per_million_tokens=0.0,
            is_local=True,
            requires_gpu=False,
            tags=["code", "local", "ollama", "incident-analysis"],
            enabled=True,
        )
        self.register_model(codellama_metadata)

        # Mistral 7B
        mistral_metadata = ModelMetadata(
            model_id="mistral-7b",
            provider=LLMProvider.MISTRAL,
            model_name="mistral:7b",
            version="1.0.0",
            description="Mistral 7B for general incident analysis",
            capabilities=ModelCapabilities(
                code_generation=True,
                code_analysis=True,
                debugging=True,
                documentation=True,
                refactoring=True,
                testing=True,
                general_chat=True,
                technical_writing=True,
            ),
            parameters={
                "size_gb": 4.4,
                "quantization": "default",
                "context_window": 8192,
                "architecture": "mistral",
                "backend": "ollama",
            },
            performance_metrics={
                "tokens_per_sec": 13.0,
                "avg_latency_ms": 140.0,
                "context_window_tokens": 8192,
            },
            cost_per_million_tokens=0.0,
            is_local=True,
            requires_gpu=False,
            tags=["general", "local", "ollama", "versatile"],
            enabled=True,
        )
        self.register_model(mistral_metadata)

        logger.info("model_registry_initialized", model_count=len(self.models))

    def register_model(self, metadata: ModelMetadata) -> None:
        """Register a new model in the registry.

        Args:
            metadata: Model metadata
        """
        entry = ModelRegistryEntry(
            metadata=metadata,
            health_status="unknown",
            last_health_check=None,
            total_requests=0,
            total_errors=0,
            avg_response_time=0.0,
        )
        self.models[metadata.model_id] = entry
        logger.info("model_registered", model_id=metadata.model_id, provider=metadata.provider.value)

    def get_model(self, model_id: str) -> Optional[ModelRegistryEntry]:
        """Get a model from the registry.

        Args:
            model_id: Model identifier

        Returns:
            Model registry entry or None
        """
        return self.models.get(model_id)

    def list_models(
        self,
        provider: Optional[LLMProvider] = None,
        enabled_only: bool = True,
        tags: Optional[List[str]] = None,
    ) -> List[ModelRegistryEntry]:
        """List models in the registry with optional filters.

        Args:
            provider: Filter by provider
            enabled_only: Only return enabled models
            tags: Filter by tags (model must have all specified tags)

        Returns:
            List of model registry entries
        """
        results = []
        for entry in self.models.values():
            # Filter by enabled status
            if enabled_only and not entry.metadata.enabled:
                continue

            # Filter by provider
            if provider and entry.metadata.provider != provider:
                continue

            # Filter by tags
            if tags:
                if not all(tag in entry.metadata.tags for tag in tags):
                    continue

            results.append(entry)

        return results

    def update_health_status(self, model_id: str, status: str) -> None:
        """Update health status for a model.

        Args:
            model_id: Model identifier
            status: Health status ("healthy", "degraded", "unhealthy", "unknown")
        """
        if model_id in self.models:
            self.models[model_id].health_status = status
            self.models[model_id].last_health_check = datetime.utcnow()
            logger.info("model_health_updated", model_id=model_id, status=status)

    def record_request(self, model_id: str, response_time_ms: float, error: bool = False) -> None:
        """Record a request to a model for metrics tracking.

        Args:
            model_id: Model identifier
            response_time_ms: Response time in milliseconds
            error: Whether the request resulted in an error
        """
        if model_id in self.models:
            entry = self.models[model_id]
            entry.total_requests += 1

            if error:
                entry.total_errors += 1

            # Update rolling average response time
            if entry.total_requests == 1:
                entry.avg_response_time = response_time_ms
            else:
                # Weighted average (last 100 requests have more weight)
                weight = min(entry.total_requests, 100)
                entry.avg_response_time = (
                    entry.avg_response_time * (weight - 1) + response_time_ms
                ) / weight

    def get_models_by_capability(self, capability: str) -> List[ModelRegistryEntry]:
        """Get models that have a specific capability.

        Args:
            capability: Capability name (e.g., "code_generation", "debugging")

        Returns:
            List of models with the specified capability
        """
        results = []
        for entry in self.models.values():
            if not entry.metadata.enabled:
                continue

            capabilities_dict = entry.metadata.capabilities.dict()
            if capabilities_dict.get(capability, False):
                results.append(entry)

        return results

    def enable_model(self, model_id: str) -> bool:
        """Enable a model.

        Args:
            model_id: Model identifier

        Returns:
            True if successful, False otherwise
        """
        if model_id in self.models:
            self.models[model_id].metadata.enabled = True
            self.models[model_id].metadata.updated_at = datetime.utcnow()
            logger.info("model_enabled", model_id=model_id)
            return True
        return False

    def disable_model(self, model_id: str) -> bool:
        """Disable a model.

        Args:
            model_id: Model identifier

        Returns:
            True if successful, False otherwise
        """
        if model_id in self.models:
            self.models[model_id].metadata.enabled = False
            self.models[model_id].metadata.updated_at = datetime.utcnow()
            logger.info("model_disabled", model_id=model_id)
            return True
        return False

    def get_statistics(self) -> Dict[str, any]:
        """Get overall registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        total_models = len(self.models)
        enabled_models = sum(1 for m in self.models.values() if m.metadata.enabled)
        local_models = sum(1 for m in self.models.values() if m.metadata.is_local)
        total_requests = sum(m.total_requests for m in self.models.values())
        total_errors = sum(m.total_errors for m in self.models.values())

        return {
            "total_models": total_models,
            "enabled_models": enabled_models,
            "disabled_models": total_models - enabled_models,
            "local_models": local_models,
            "cloud_models": total_models - local_models,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0.0,
        }
