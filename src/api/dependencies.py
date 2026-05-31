"""Shared dependencies for API routers.

Enhancement 019: API Router Refactoring.
"""

from src.core.orchestrator import Orchestrator
from src.core.model_registry import ModelRegistry

# Global instances
_orchestrator: Orchestrator | None = None
_model_registry: ModelRegistry | None = None


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def get_model_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry


def init_dependencies() -> None:
    """Initialize all dependencies."""
    global _orchestrator, _model_registry
    _orchestrator = Orchestrator()
    _model_registry = ModelRegistry()
