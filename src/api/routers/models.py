"""API router for model registry endpoints.

Enhancement 019: API Router Refactoring.
"""

from fastapi import APIRouter, HTTPException
import structlog

from src.api.dependencies import get_model_registry

logger = structlog.get_logger()
router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def list_models(
    provider: str | None = None,
    enabled_only: bool = True,
    tags: str | None = None,
):
    """List all registered models with optional filters.

    Args:
        provider: Filter by provider (deepseek, mistral, llama2, codellama)
        enabled_only: Only return enabled models (default: True)
        tags: Comma-separated tags to filter by

    Returns:
        List of models with metadata
    """
    try:
        from src.models.schemas import LLMProvider

        model_registry = get_model_registry()

        # Parse provider
        provider_enum = None
        if provider:
            try:
                provider_enum = LLMProvider(provider.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]

        # Get models from registry
        models = model_registry.list_models(
            provider=provider_enum,
            enabled_only=enabled_only,
            tags=tag_list,
        )

        return {
            "models": [
                {
                    "model_id": entry.metadata.model_id,
                    "provider": entry.metadata.provider.value,
                    "model_name": entry.metadata.model_name,
                    "version": entry.metadata.version,
                    "description": entry.metadata.description,
                    "capabilities": {
                        "code_generation": entry.metadata.capabilities.code_generation,
                        "code_analysis": entry.metadata.capabilities.code_analysis,
                        "debugging": entry.metadata.capabilities.debugging,
                        "documentation": entry.metadata.capabilities.documentation,
                        "refactoring": entry.metadata.capabilities.refactoring,
                        "testing": entry.metadata.capabilities.testing,
                        "general_chat": entry.metadata.capabilities.general_chat,
                        "technical_writing": entry.metadata.capabilities.technical_writing,
                    },
                    "parameters": entry.metadata.parameters,
                    "performance_metrics": entry.metadata.performance_metrics,
                    "cost_per_million_tokens": entry.metadata.cost_per_million_tokens,
                    "is_local": entry.metadata.is_local,
                    "requires_gpu": entry.metadata.requires_gpu,
                    "tags": entry.metadata.tags,
                    "enabled": entry.metadata.enabled,
                    "health_status": entry.health_status,
                    "last_health_check": entry.last_health_check.isoformat() if entry.last_health_check else None,
                    "total_requests": entry.total_requests,
                    "total_errors": entry.total_errors,
                    "avg_response_time": entry.avg_response_time,
                    "created_at": entry.metadata.created_at.isoformat(),
                    "updated_at": entry.metadata.updated_at.isoformat(),
                }
                for entry in models
            ],
            "total": len(models),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_models_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_model_statistics():
    """Get overall model registry statistics.

    Returns:
        Registry statistics
    """
    try:
        model_registry = get_model_registry()
        stats = model_registry.get_statistics()
        return stats
    except Exception as e:
        logger.error("get_model_statistics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capability/{capability}")
async def get_models_by_capability(capability: str):
    """Get models that support a specific capability.

    Args:
        capability: Capability name (code_generation, debugging, etc.)

    Returns:
        List of models with that capability
    """
    try:
        model_registry = get_model_registry()

        # Validate capability name
        valid_capabilities = [
            "code_generation", "code_analysis", "debugging",
            "documentation", "refactoring", "testing",
            "general_chat", "technical_writing"
        ]
        if capability not in valid_capabilities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid capability. Valid options: {', '.join(valid_capabilities)}"
            )

        models = model_registry.get_models_by_capability(capability)

        return {
            "capability": capability,
            "models": [
                {
                    "model_id": entry.metadata.model_id,
                    "provider": entry.metadata.provider.value,
                    "model_name": entry.metadata.model_name,
                    "description": entry.metadata.description,
                    "is_local": entry.metadata.is_local,
                    "health_status": entry.health_status,
                    "performance_metrics": entry.metadata.performance_metrics,
                }
                for entry in models
            ],
            "total": len(models),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_models_by_capability_failed", error=str(e), capability=capability)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}")
async def get_model(model_id: str):
    """Get detailed information about a specific model.

    Args:
        model_id: Model identifier (e.g., "deepseek-coder-6.7b")

    Returns:
        Model details
    """
    try:
        model_registry = get_model_registry()
        entry = model_registry.get_model(model_id)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        return {
            "model_id": entry.metadata.model_id,
            "provider": entry.metadata.provider.value,
            "model_name": entry.metadata.model_name,
            "version": entry.metadata.version,
            "description": entry.metadata.description,
            "capabilities": {
                "code_generation": entry.metadata.capabilities.code_generation,
                "code_analysis": entry.metadata.capabilities.code_analysis,
                "debugging": entry.metadata.capabilities.debugging,
                "documentation": entry.metadata.capabilities.documentation,
                "refactoring": entry.metadata.capabilities.refactoring,
                "testing": entry.metadata.capabilities.testing,
                "general_chat": entry.metadata.capabilities.general_chat,
                "technical_writing": entry.metadata.capabilities.technical_writing,
            },
            "parameters": entry.metadata.parameters,
            "performance_metrics": entry.metadata.performance_metrics,
            "cost_per_million_tokens": entry.metadata.cost_per_million_tokens,
            "is_local": entry.metadata.is_local,
            "requires_gpu": entry.metadata.requires_gpu,
            "tags": entry.metadata.tags,
            "enabled": entry.metadata.enabled,
            "health_status": entry.health_status,
            "last_health_check": entry.last_health_check.isoformat() if entry.last_health_check else None,
            "total_requests": entry.total_requests,
            "total_errors": entry.total_errors,
            "avg_response_time": entry.avg_response_time,
            "error_rate": (entry.total_errors / entry.total_requests * 100) if entry.total_requests > 0 else 0.0,
            "created_at": entry.metadata.created_at.isoformat(),
            "updated_at": entry.metadata.updated_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_model_failed", error=str(e), model_id=model_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/enable")
async def enable_model(model_id: str):
    """Enable a model.

    Args:
        model_id: Model identifier

    Returns:
        Success message
    """
    try:
        model_registry = get_model_registry()
        success = model_registry.enable_model(model_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        return {"message": f"Model {model_id} enabled successfully", "model_id": model_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("enable_model_failed", error=str(e), model_id=model_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/disable")
async def disable_model(model_id: str):
    """Disable a model.

    Args:
        model_id: Model identifier

    Returns:
        Success message
    """
    try:
        model_registry = get_model_registry()
        success = model_registry.disable_model(model_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        return {"message": f"Model {model_id} disabled successfully", "model_id": model_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("disable_model_failed", error=str(e), model_id=model_id)
        raise HTTPException(status_code=500, detail=str(e))
