"""Provider & Tool Registry — Enhancement 017 Phase 3.

Replaces the hardcoded _init_providers() in orchestrator.py with config-driven
provider loading. Providers are declared in config/providers_dev.yaml (or the
env-specific equivalent); adding a new provider no longer requires code changes.

Tool registry wraps the existing ToolManager with the same config-driven pattern.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Type
import yaml
import structlog

from src.models.schemas import LLMProvider
from src.providers.base import BaseLLMProvider
from src.core.config import settings

logger = structlog.get_logger().bind(component="registry")


# ── Provider class map ────────────────────────────────────────────────────────
# Maps the YAML provider name → provider class.
# Import lazily inside the function to avoid circular imports at module load.

_PROVIDER_CLASS_MAP: Dict[str, str] = {
    "claude":       "src.providers.claude:ClaudeProvider",
    "claude_code":  "src.providers.claude_code:ClaudeCodeProvider",
    "chatgpt":      "src.providers.chatgpt:ChatGPTProvider",
    "gemini":       "src.providers.gemini:GeminiProvider",
    "local":        "src.providers.local_llm:LocalLLMProvider",
    "deepseek":     "src.providers.deepseek:DeepSeekProvider",
    "vllm":         "src.providers.vllm_provider:VLLMProvider",
    "llama2":       "src.providers.llama2:Llama2Provider",
    "codellama":    "src.providers.codellama:CodeLlamaProvider",
    "mistral":      "src.providers.mistral:MistralProvider",
}

# Which settings field gates each provider (missing key → check is skipped)
_PROVIDER_KEY_GUARD: Dict[str, str] = {
    "claude":       "anthropic_api_key",
    "claude_code":  "anthropic_api_key",
    "chatgpt":      "openai_api_key",
    "gemini":       "google_api_key",
}


def _import_provider_class(dotted: str) -> Type[BaseLLMProvider]:
    """Dynamically import a provider class from 'module:ClassName' string."""
    module_path, class_name = dotted.split(":")
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _has_api_key(provider_name: str) -> bool:
    """Return False if a required API key setting is empty."""
    guard = _PROVIDER_KEY_GUARD.get(provider_name)
    if guard is None:
        return True  # local/vllm providers need no API key
    return bool(getattr(settings, guard, ""))


class ProviderRegistry:
    """Config-driven provider registry.

    Usage:
        registry = ProviderRegistry()
        registry.load_from_config()          # loads providers_dev.yaml by default
        providers = registry.active_providers()  # {LLMProvider: instance}
    """

    def __init__(self) -> None:
        self._providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def load_from_config(self, config_path: Optional[Path] = None) -> None:
        """Load and instantiate providers declared as enabled in config."""
        if config_path is None:
            config_path = Path("config/providers_dev.yaml")

        if not config_path.exists():
            logger.warning("provider_config_not_found", path=str(config_path))
            return

        with open(config_path) as f:
            config = yaml.safe_load(f)

        provider_configs: Dict[str, Any] = config.get("providers", {})

        for name, cfg in provider_configs.items():
            if not cfg.get("enabled", False):
                logger.debug("provider_disabled", name=name)
                continue

            if not _has_api_key(name):
                logger.info("provider_skipped_no_key", name=name)
                continue

            dotted = _PROVIDER_CLASS_MAP.get(name)
            if dotted is None:
                logger.warning("provider_not_in_class_map", name=name)
                continue

            try:
                cls = _import_provider_class(dotted)
                instance = cls()
                enum_key = LLMProvider(name)
                self._providers[enum_key] = instance
                self._metadata[name] = {
                    "tier": cfg.get("tier", "unknown"),
                    "priority": cfg.get("priority", "medium"),
                    "cost_per_1k": cfg.get("cost_per_1k_tokens", 0.0),
                    "backend": cfg.get("backend", "api"),
                }
                logger.info("provider_registered", name=name, tier=cfg.get("tier"))
            except Exception as e:
                logger.error("provider_registration_failed", name=name, error=str(e))

    def register(
        self,
        name: str,
        instance: BaseLLMProvider,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Manually register a provider instance (for testing or dynamic addition)."""
        enum_key = LLMProvider(name)
        self._providers[enum_key] = instance
        self._metadata[name] = metadata or {}
        logger.info("provider_manually_registered", name=name)

    def get(self, provider: LLMProvider) -> Optional[BaseLLMProvider]:
        return self._providers.get(provider)

    def active_providers(self) -> Dict[LLMProvider, BaseLLMProvider]:
        return dict(self._providers)

    def list_names(self) -> list[str]:
        return [p.value for p in self._providers]

    def metadata(self, name: str) -> Dict[str, Any]:
        return self._metadata.get(name, {})

    async def health_check_all(self) -> Dict[str, bool]:
        """Run health checks on all registered providers concurrently."""
        import asyncio
        results: Dict[str, bool] = {}
        tasks = {
            p.value: provider.health_check()
            for p, provider in self._providers.items()
        }
        outcomes = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for name, outcome in zip(tasks.keys(), outcomes):
            results[name] = bool(outcome) if not isinstance(outcome, Exception) else False
            if isinstance(outcome, Exception):
                logger.error("health_check_exception", provider=name, error=str(outcome))
        return results

    def stats(self) -> Dict[str, Any]:
        tiers: Dict[str, int] = {}
        for name in self._metadata:
            tier = self._metadata[name].get("tier", "unknown")
            tiers[tier] = tiers.get(tier, 0) + 1
        return {
            "registered": len(self._providers),
            "providers": self.list_names(),
            "by_tier": tiers,
        }


# ── Module-level singleton ────────────────────────────────────────────────────

_registry: Optional[ProviderRegistry] = None


def get_provider_registry(config_path: Optional[Path] = None) -> ProviderRegistry:
    """Return the singleton registry, loading from config on first call."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
        _registry.load_from_config(config_path)
    return _registry


def reset_registry() -> None:
    """Clear the singleton — used in tests."""
    global _registry
    _registry = None
