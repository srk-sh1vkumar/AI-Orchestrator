"""Monitoring and metrics API endpoints for AI Orchestrator."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

from src.core.rate_limiter import get_rate_limiter
from src.core.semantic_cache import get_semantic_cache

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# Global orchestrator instance (set by main.py)
_orchestrator = None


def set_orchestrator(orchestrator):
    """Set the orchestrator instance for monitoring."""
    global _orchestrator
    _orchestrator = orchestrator


class ProviderMetrics(BaseModel):
    """Metrics for a single LLM provider."""
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    avg_response_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    rate_limit_stats: Dict[str, Any] = {}


class CacheMetrics(BaseModel):
    """Semantic cache performance metrics."""
    enabled: bool
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    avg_similarity_threshold: float = 0.85
    total_entries: int = 0


class SystemMetrics(BaseModel):
    """Overall system metrics."""
    uptime_seconds: float
    total_requests: int
    providers_healthy: int
    providers_total: int
    cache_enabled: bool
    rate_limiting_enabled: bool


class MonitoringResponse(BaseModel):
    """Complete monitoring dashboard data."""
    timestamp: datetime
    system: SystemMetrics
    providers: List[ProviderMetrics]
    cache: CacheMetrics
    rate_limits: Dict[str, Dict[str, Any]]  # Changed from float to Any to support daily quota date strings


# In-memory metrics storage (temporary - would use Redis/DB in production)
_metrics_store: Dict[str, Dict[str, Any]] = {
    "providers": {},
    "system": {
        "start_time": time.time(),
        "total_requests": 0,
    }
}


@router.get("/metrics", response_model=MonitoringResponse)
async def get_metrics():
    """Get comprehensive system metrics for monitoring dashboard."""
    try:
        if _orchestrator is None:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")

        orchestrator = _orchestrator
        rate_limiter = get_rate_limiter()

        # Get cache metrics
        cache_metrics = CacheMetrics(enabled=False)
        try:
            cache = get_semantic_cache()
            if cache:
                metrics = cache.get_metrics()
                cache_metrics = CacheMetrics(
                    enabled=True,
                    total_queries=metrics.total_queries,
                    cache_hits=metrics.cache_hits,
                    cache_misses=metrics.cache_misses,
                    hit_rate=metrics.cache_hits / metrics.total_queries if metrics.total_queries > 0 else 0.0,
                    total_entries=metrics.total_queries  # Approximation
                )
        except Exception as e:
            pass  # Cache not available

        # Get provider metrics
        provider_metrics_list = []
        for provider in orchestrator.providers.keys():
            provider_name = provider.value
            provider_data = _metrics_store["providers"].get(provider_name, {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tokens": 0,
                "total_response_time_ms": 0,
            })

            # Get rate limit stats using the orchestrator's mapping
            # Map LLMProvider enum to rate limiter provider name (e.g., chatgpt -> openai)
            rate_limiter_name = orchestrator._get_rate_limiter_provider_name(provider)
            rate_limit_stats = rate_limiter.get_provider_stats(rate_limiter_name)

            # Calculate averages
            total_req = provider_data["total_requests"]
            avg_response_time = (
                provider_data["total_response_time_ms"] / total_req
                if total_req > 0 else 0.0
            )

            provider_metrics_list.append(ProviderMetrics(
                provider=provider_name,
                total_requests=provider_data["total_requests"],
                successful_requests=provider_data["successful_requests"],
                failed_requests=provider_data["failed_requests"],
                total_tokens=provider_data["total_tokens"],
                avg_response_time_ms=avg_response_time,
                rate_limit_stats=rate_limit_stats
            ))

        # Get system metrics
        uptime = time.time() - _metrics_store["system"]["start_time"]
        health_status = await orchestrator.health_check()
        providers_healthy = sum(1 for p in health_status["providers"].values() if p.get("healthy", False))

        system_metrics = SystemMetrics(
            uptime_seconds=uptime,
            total_requests=_metrics_store["system"]["total_requests"],
            providers_healthy=providers_healthy,
            providers_total=len(orchestrator.providers),
            cache_enabled=cache_metrics.enabled,
            rate_limiting_enabled=True  # Always enabled
        )

        # Get all rate limit stats
        all_rate_limits = rate_limiter.get_all_stats()

        return MonitoringResponse(
            timestamp=datetime.utcnow(),
            system=system_metrics,
            providers=provider_metrics_list,
            cache=cache_metrics,
            rate_limits=all_rate_limits
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")


@router.post("/record")
async def record_request(
    provider: str,
    success: bool,
    response_time_ms: float,
    tokens_used: Optional[int] = None
):
    """Record a request for metrics tracking.

    This endpoint is called internally by the orchestrator after each LLM request.
    """
    try:
        # Initialize provider metrics if not exists
        if provider not in _metrics_store["providers"]:
            _metrics_store["providers"][provider] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tokens": 0,
                "total_response_time_ms": 0.0,
            }

        # Update metrics
        provider_data = _metrics_store["providers"][provider]
        provider_data["total_requests"] += 1
        _metrics_store["system"]["total_requests"] += 1

        if success:
            provider_data["successful_requests"] += 1
        else:
            provider_data["failed_requests"] += 1

        provider_data["total_response_time_ms"] += response_time_ms

        if tokens_used:
            provider_data["total_tokens"] += tokens_used

        return {"status": "recorded"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record metrics: {str(e)}")


@router.get("/providers/{provider_name}")
async def get_provider_metrics(provider_name: str):
    """Get detailed metrics for a specific provider."""
    try:
        provider_data = _metrics_store["providers"].get(provider_name, {})

        if not provider_data:
            return {
                "provider": provider_name,
                "total_requests": 0,
                "message": "No metrics available for this provider"
            }

        total_req = provider_data["total_requests"]

        return {
            "provider": provider_name,
            "total_requests": total_req,
            "successful_requests": provider_data["successful_requests"],
            "failed_requests": provider_data["failed_requests"],
            "success_rate": provider_data["successful_requests"] / total_req if total_req > 0 else 0.0,
            "total_tokens": provider_data["total_tokens"],
            "avg_response_time_ms": provider_data["total_response_time_ms"] / total_req if total_req > 0 else 0.0,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch provider metrics: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics."""
    try:
        cache = get_semantic_cache()
        if not cache:
            return {"enabled": False, "message": "Cache is not enabled"}

        metrics = cache.get_metrics()

        return {
            "enabled": True,
            "total_queries": metrics.total_queries,
            "cache_hits": metrics.cache_hits,
            "cache_misses": metrics.cache_misses,
            "hit_rate": metrics.cache_hits / metrics.total_queries if metrics.total_queries > 0 else 0.0,
            "avg_similarity_search_time_ms": metrics.avg_similarity_search_time_ms,
            "avg_cache_save_time_ms": metrics.avg_cache_save_time_ms,
            "similarity_threshold": 0.85,  # From cache config
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cache stats: {str(e)}")


@router.get("/rate-limits")
async def get_rate_limits():
    """Get rate limit status for all providers."""
    try:
        rate_limiter = get_rate_limiter()
        all_stats = rate_limiter.get_all_stats()

        return {
            "providers": all_stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch rate limits: {str(e)}")


@router.delete("/reset")
async def reset_metrics():
    """Reset all metrics (useful for testing or starting fresh)."""
    global _metrics_store

    _metrics_store = {
        "providers": {},
        "system": {
            "start_time": time.time(),
            "total_requests": 0,
        }
    }

    return {"status": "metrics_reset", "timestamp": datetime.utcnow().isoformat()}
