"""FastAPI application for AI Orchestrator."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from prometheus_client import Counter, Histogram, make_asgi_app
import structlog
from src.models.schemas import ChatRequest, ChatResponse, HealthStatus
from src.core.orchestrator import Orchestrator
from src.core.config import settings
from src.api.personal_tracker import router as tracker_router
from src.api.growth import router as growth_router
from src.api.monitoring import router as monitoring_router
from src.api.costs import router as costs_router
from src.api.enhancements import router as enhancements_router
from src.monitor import get_monitoring_metrics
import time
import json
from pathlib import Path

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Prometheus metrics
request_counter = Counter(
    "orchestrator_requests_total",
    "Total requests",
    ["provider", "category", "status"],
)
request_duration = Histogram(
    "orchestrator_request_duration_seconds",
    "Request duration",
    ["provider"],
)
fallback_counter = Counter(
    "orchestrator_fallbacks_total",
    "Total fallbacks",
    ["from_provider", "to_provider"],
)

# Token analytics metrics
from prometheus_client import Gauge
token_usage_gauge = Gauge(
    "ai_orchestrator_llm_tokens_total",
    "Total tokens used per agent",
    ["agent", "model"],
)
cost_gauge = Gauge(
    "ai_orchestrator_estimated_cost_usd",
    "Estimated cost in USD per agent",
    ["agent", "model"],
)
llm_health_gauge = Gauge(
    "ai_orchestrator_llm_health_status",
    "Local LLM health status (1=healthy, 0=unhealthy)",
    ["model", "endpoint"],
)
llm_latency_gauge = Gauge(
    "ai_orchestrator_llm_latency_seconds",
    "Local LLM latency in seconds",
    ["model", "endpoint"],
)

# Rate limiting and circuit breaker metrics
rate_limit_counter = Counter(
    "ai_orchestrator_rate_limit_hits_total",
    "Total rate limit hits",
    ["provider"],
)
circuit_breaker_state = Gauge(
    "ai_orchestrator_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open)",
    ["provider"],
)
rate_limit_available_tokens = Gauge(
    "ai_orchestrator_rate_limit_available_tokens",
    "Available rate limit tokens per provider",
    ["provider"],
)

# Tool output validation metrics
tool_validation_total = Counter(
    "ai_orchestrator_tool_validation_total",
    "Total tool output validations",
    ["tool_type", "operation", "status"],
)
tool_validation_failures = Counter(
    "ai_orchestrator_tool_validation_failures_total",
    "Total tool validation failures",
    ["tool_type", "operation", "error_type"],
)
tool_validation_duration = Histogram(
    "ai_orchestrator_tool_validation_duration_seconds",
    "Tool validation duration in seconds",
    ["tool_type"],
)

# Context window management metrics
context_window_status = Counter(
    "ai_orchestrator_context_window_status_total",
    "Context window status checks",
    ["provider", "status"],
)
context_window_truncations = Counter(
    "ai_orchestrator_context_window_truncations_total",
    "Context window truncations",
    ["provider", "strategy"],
)
context_window_tokens = Gauge(
    "ai_orchestrator_context_window_tokens",
    "Current context window token count",
    ["provider"],
)
context_window_utilization = Gauge(
    "ai_orchestrator_context_window_utilization_percent",
    "Context window utilization percentage",
    ["provider"],
)

# Intent-based routing metrics
routing_method = Counter(
    "ai_orchestrator_routing_method_total",
    "Routing method used",
    ["method"],  # "ml", "regex", "regex_fallback", "explicit", "default"
)
routing_confidence = Histogram(
    "ai_orchestrator_routing_confidence",
    "Routing confidence score",
    ["provider", "method"],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0],
)
ml_classification_latency = Histogram(
    "ai_orchestrator_ml_classification_latency_seconds",
    "ML classification latency",
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2],
)

# Create FastAPI app
app = FastAPI(
    title="AI Orchestrator",
    description="Intelligent LLM orchestration with multi-provider routing",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check if frontend dist exists and mount it
FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Initialize orchestrator
orchestrator = Orchestrator()

# Include routers
app.include_router(tracker_router)
app.include_router(growth_router)
app.include_router(monitoring_router)
app.include_router(costs_router)
app.include_router(enhancements_router)

# Set orchestrator for monitoring
from src.api.monitoring import set_orchestrator
set_orchestrator(orchestrator)


def update_prometheus_metrics() -> None:
    """Update Prometheus metrics from manifest data."""
    try:
        manifest_path = Path("manifest_state.json")
        if not manifest_path.exists():
            return

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        monitoring = manifest.get("monitoring", {})
        token_usage = monitoring.get("token_usage", {})
        cost_breakdown = monitoring.get("cost_breakdown", {})
        local_llm_status = monitoring.get("local_llm_status", {})

        # Update token usage metrics
        for agent, data in token_usage.items():
            model = data.get("model", "unknown")
            tokens = data.get("total_tokens", 0)
            token_usage_gauge.labels(agent=agent, model=model).set(tokens)

        # Update cost metrics
        for agent, data in cost_breakdown.items():
            model = data.get("model", "unknown")
            cost = data.get("cost_usd", 0.0)
            cost_gauge.labels(agent=agent, model=model).set(cost)

        # Update LLM health metrics
        if local_llm_status:
            model = local_llm_status.get("model", "unknown")
            endpoint = local_llm_status.get("endpoint", "unknown")
            is_healthy = 1 if local_llm_status.get("healthy", False) else 0
            latency_ms = local_llm_status.get("latency_ms", 0)
            latency_s = latency_ms / 1000.0

            llm_health_gauge.labels(model=model, endpoint=endpoint).set(is_healthy)
            llm_latency_gauge.labels(model=model, endpoint=endpoint).set(latency_s)

    except Exception as e:
        logger.error("prometheus_metrics_update_failed", error=str(e))


@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler."""
    logger.info("orchestrator_starting", host=settings.orchestrator_host, port=settings.orchestrator_port)
    # Initial metrics update
    update_prometheus_metrics()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown event handler."""
    logger.info("orchestrator_shutting_down")


@app.get("/")
async def root():
    """Serve frontend application at root."""
    if FRONTEND_DIST.exists():
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

    # Fallback to API info if frontend not built
    return {
        "service": "AI Orchestrator",
        "version": "0.1.0",
        "status": "running",
        "api_docs": "/docs",
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat request.

    Args:
        request: Chat request

    Returns:
        ChatResponse

    Raises:
        HTTPException: If request processing fails
    """
    start_time = time.time()

    try:
        logger.info("chat_request_received", message_length=len(request.message))

        response = await orchestrator.process_request(request)

        # Update metrics
        request_counter.labels(
            provider=response.provider.value,
            category=response.routing_decision.category.value,
            status="success",
        ).inc()

        request_duration.labels(provider=response.provider.value).observe(response.execution_time)

        # Count fallbacks
        for fallback in response.fallback_events:
            fallback_counter.labels(
                from_provider=fallback.from_provider.value,
                to_provider=fallback.to_provider.value,
            ).inc()

        logger.info(
            "chat_request_completed",
            provider=response.provider.value,
            execution_time=response.execution_time,
            fallback_count=len(response.fallback_events),
        )

        return response

    except Exception as e:
        logger.error("chat_request_failed", error=str(e))
        request_counter.labels(provider="unknown", category="unknown", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses using Server-Sent Events (SSE).

    Args:
        request: Chat request

    Returns:
        StreamingResponse with SSE format

    Raises:
        HTTPException: If request processing fails
    """
    async def event_generator():
        """Generate SSE events from streaming response."""
        try:
            logger.info("streaming_request_received", message_length=len(request.message))

            # Use orchestrator's routing to get provider and category
            from src.models.schemas import Message

            # Determine provider using orchestrator's router
            if request.explicit_provider:
                provider_enum = request.explicit_provider
                category = None  # Will be determined by router if needed
            else:
                # Use orchestrator's router to decide
                routing_decision = orchestrator.router.route(
                    request.message,
                    enable_collaboration=request.enable_collaboration
                )
                provider_enum = routing_decision.provider
                category = routing_decision.category

            # Get the provider instance from orchestrator's providers dict
            provider = orchestrator.providers.get(provider_enum)
            if not provider:
                raise ValueError(f"Provider {provider_enum.value} not available")

            # Create messages list
            messages = [Message(role="user", content=request.message)]

            # Stream from provider
            async for chunk in provider.stream(messages):
                # Format as SSE
                chunk_data = {
                    "provider": chunk.provider.value,
                    "content": chunk.content,
                    "is_final": chunk.is_final,
                    "tokens_used": chunk.tokens_used,
                    "metadata": chunk.metadata or {}
                }

                yield f"data: {json.dumps(chunk_data)}\n\n"

                # Update metrics on final chunk
                if chunk.is_final:
                    request_counter.labels(
                        provider=chunk.provider.value,
                        category=category.value if category else "unknown",
                        status="success",
                    ).inc()

            logger.info("streaming_request_completed", provider=provider_enum.value)

        except Exception as e:
            logger.error("streaming_request_failed", error=str(e))
            error_data = {
                "error": str(e),
                "is_final": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive",
        }
    )


@app.get("/api/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    """Health check endpoint.

    Returns:
        HealthStatus
    """
    try:
        health_data = await orchestrator.health_check()

        return HealthStatus(
            status=health_data["status"],
            providers=health_data["providers"],
            tools=health_data["tools"],
        )

    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/providers")
async def list_providers():
    """List available providers and their configuration.

    Returns:
        Provider information
    """
    provider_config = settings.validate_provider_config()

    return {
        "providers": {
            "claude_code": {
                "configured": provider_config["claude_code"],
                "role": "Code generation, DevOps, deployment",
            },
            "chatgpt": {
                "configured": provider_config["chatgpt"],
                "role": "UI/UX, workflow automation",
            },
            "gemini": {
                "configured": provider_config["gemini"],
                "role": "Prompt optimization, meta-prompting",
            },
            "claude": {
                "configured": provider_config["claude"],
                "role": "Incident analysis (fallback), reasoning",
            },
            "local": {
                "configured": provider_config["local"],
                "role": "Incident analysis (primary), privacy-focused",
                "model": settings.local_llm_model if settings.local_llm_enabled else None,
            },
        }
    }


@app.get("/api/analytics/tokens")
async def get_token_analytics():
    """Get token usage analytics for all agents.

    Returns:
        JSON with token usage and cost data for each agent
    """
    try:
        # Load manifest
        manifest_path = Path("manifest_state.json")
        if not manifest_path.exists():
            return {
                "error": "No manifest data available",
                "agents": {},
                "total_tokens": 0,
                "total_cost_usd": 0.0
            }

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        monitoring = manifest.get("monitoring", {})
        token_usage = monitoring.get("token_usage", {})
        cost_breakdown = monitoring.get("cost_breakdown", {})

        # Build response
        agents = {}
        total_tokens = 0
        total_cost = 0.0

        for agent, token_data in token_usage.items():
            tokens = token_data.get("total_tokens", 0)
            total_tokens += tokens

            cost_info = cost_breakdown.get(agent, {})
            cost_usd = cost_info.get("cost_usd", 0.0)
            total_cost += cost_usd

            agents[agent] = {
                "tokens": tokens,
                "cost_usd": cost_usd,
                "model": token_data.get("model", "unknown"),
                "requests": len(token_data.get("requests", []))
            }

        return {
            "agents": agents,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "timestamp": monitoring.get("timestamp", "unknown")
        }

    except Exception as e:
        logger.error("analytics_tokens_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get comprehensive analytics summary including tokens, costs, and LLM status.

    Returns:
        JSON with complete analytics data
    """
    try:
        # Update Prometheus metrics
        update_prometheus_metrics()

        # Load manifest
        manifest_path = Path("manifest_state.json")
        if not manifest_path.exists():
            return {
                "error": "No manifest data available",
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "agents_tracked": 0,
                "local_llm": {"status": "unknown", "latency": 0}
            }

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        # Get monitoring metrics
        metrics = get_monitoring_metrics(manifest)

        # Build summary response
        summary = {
            "total_tokens": metrics["aggregates"]["total_tokens"],
            "total_requests": metrics["aggregates"]["total_requests"],
            "agents_tracked": metrics["aggregates"]["agents_tracked"],
            "total_cost_usd": metrics["estimated_costs_usd"],
            "token_usage": metrics["token_usage"],
            "local_llm": {
                "status": "healthy" if metrics["local_llm_status"].get("healthy", False) else "unhealthy",
                "latency_ms": metrics["local_llm_status"].get("latency_ms", 0),
                "model": metrics["local_llm_status"].get("model", "unknown"),
                "endpoint": metrics["local_llm_status"].get("endpoint", "unknown")
            },
            "timestamp": metrics["timestamp"]
        }

        return summary

    except Exception as e:
        logger.error("analytics_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/cost-breakdown")
async def get_cost_breakdown():
    """Get detailed cost breakdown by agent and model.

    Returns:
        JSON with cost breakdown
    """
    try:
        # Load manifest
        manifest_path = Path("manifest_state.json")
        if not manifest_path.exists():
            return {"error": "No manifest data available", "breakdown": {}}

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        monitoring = manifest.get("monitoring", {})
        cost_breakdown = monitoring.get("cost_breakdown", {})
        total_cost = monitoring.get("estimated_costs_usd", 0.0)

        return {
            "breakdown": cost_breakdown,
            "total_cost_usd": total_cost,
            "timestamp": monitoring.get("timestamp", "unknown")
        }

    except Exception as e:
        logger.error("analytics_cost_breakdown_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Project Enhancement Tracker endpoints
@app.get("/api/enhancements")
async def get_enhancements():
    """Get all project enhancements from tracker YAML.

    Returns:
        Project enhancements data
    """
    try:
        import yaml

        yaml_path = Path("PROJECT_ENHANCEMENT_TRACKER_DB.yaml")
        if not yaml_path.exists():
            raise HTTPException(
                status_code=404, detail="Enhancement tracker file not found"
            )

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        enhancements = data.get("enhancements", [])

        # Calculate progress statistics
        total = len(enhancements)
        completed = sum(1 for e in enhancements if e.get("status") in ["Complete", "Completed"])
        in_progress = sum(1 for e in enhancements if e.get("status") == "In Progress")
        planned = sum(1 for e in enhancements if e.get("status") in ["Planned", "Ideation"])

        progress = {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "planned": planned,
            "completion_percentage": round((completed / total * 100), 1) if total > 0 else 0
        }

        return {
            "enhancements": enhancements,
            "progress": progress,
            "metadata": {
                "project_name": data.get("project_name"),
                "project_tag": data.get("project_tag"),
                "version": data.get("version"),
                "owner": data.get("owner"),
                "last_updated": data.get("metadata", {}).get("last_updated"),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_enhancements_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/enhancements/{enhancement_id}")
async def get_enhancement(enhancement_id: str):
    """Get specific enhancement details.

    Args:
        enhancement_id: Enhancement ID (e.g., "001", "012")

    Returns:
        Enhancement details
    """
    try:
        import yaml

        yaml_path = Path("PROJECT_ENHANCEMENT_TRACKER_DB.yaml")
        if not yaml_path.exists():
            raise HTTPException(
                status_code=404, detail="Enhancement tracker file not found"
            )

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        enhancements = data.get("enhancements", [])
        enhancement = next(
            (e for e in enhancements if e.get("id") == enhancement_id), None
        )

        if not enhancement:
            raise HTTPException(
                status_code=404,
                detail=f"Enhancement {enhancement_id} not found",
            )

        return enhancement
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_enhancement_failed", error=str(e), enhancement_id=enhancement_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/enhancements/status/{status}")
async def get_enhancements_by_status(status: str):
    """Get enhancements filtered by status.

    Args:
        status: Status filter (Complete, In Progress, Design, Planned)

    Returns:
        Filtered enhancements
    """
    try:
        import yaml

        yaml_path = Path("PROJECT_ENHANCEMENT_TRACKER_DB.yaml")
        if not yaml_path.exists():
            raise HTTPException(
                status_code=404, detail="Enhancement tracker file not found"
            )

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        enhancements = data.get("enhancements", [])
        filtered = [e for e in enhancements if e.get("status") == status]

        return {
            "enhancements": filtered,
            "total": len(filtered),
            "status": status,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_enhancements_by_status_failed", error=str(e), status=status)
        raise HTTPException(status_code=500, detail=str(e))


# E-Commerce Platform Enhancement Tracker endpoints
@app.get("/api/ecommerce/enhancements")
async def get_ecommerce_enhancements():
    """Get all e-commerce platform enhancements from tracker YAML."""
    try:
        import yaml
        yaml_path = Path("../ecommerce-microservices/ECOMMERCE_ENHANCEMENT_TRACKER.yaml")
        if not yaml_path.exists():
            raise HTTPException(status_code=404, detail="E-commerce enhancement tracker file not found")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        enhancements = data.get("enhancements", [])

        # Calculate progress statistics dynamically
        total = len(enhancements)
        completed = sum(1 for e in enhancements if e.get("status") in ["Complete", "Completed"])
        in_progress = sum(1 for e in enhancements if e.get("status") == "In Progress")
        planned = sum(1 for e in enhancements if e.get("status") in ["Planned", "Ideation"])

        progress = {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "planned": planned,
            "completion_percentage": round((completed / total * 100), 1) if total > 0 else 0
        }

        return {
            "enhancements": enhancements,
            "progress": progress,
            "metadata": {
                "project_name": data.get("project", {}).get("name"),
                "project_tag": data.get("project", {}).get("project_tag"),
                "version": data.get("project", {}).get("version"),
                "last_updated": data.get("project", {}).get("last_updated"),
                "technologies": data.get("project", {}).get("technologies", []),
            },
            "metrics": data.get("metrics", {}),
            "timeline": data.get("timeline", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_ecommerce_enhancements_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ecommerce/enhancements/{enhancement_id}")
async def get_ecommerce_enhancement(enhancement_id: str):
    """Get specific e-commerce enhancement details.

    Args:
        enhancement_id: Enhancement ID (e.g., "ECOM-001")

    Returns:
        Enhancement details
    """
    try:
        import yaml
        yaml_path = Path("../ecommerce-microservices/ECOMMERCE_ENHANCEMENT_TRACKER.yaml")
        if not yaml_path.exists():
            raise HTTPException(status_code=404, detail="E-commerce enhancement tracker file not found")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        enhancements = data.get("enhancements", [])
        enhancement = next((e for e in enhancements if e.get("id") == enhancement_id), None)

        if not enhancement:
            raise HTTPException(status_code=404, detail=f"Enhancement {enhancement_id} not found")

        return enhancement
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_ecommerce_enhancement_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ecommerce/enhancements/status/{status}")
async def get_ecommerce_enhancements_by_status(status: str):
    """Get e-commerce enhancements filtered by status.

    Args:
        status: Status filter (Completed, Planned, etc.)

    Returns:
        Filtered enhancements
    """
    try:
        import yaml
        yaml_path = Path("../ecommerce-microservices/ECOMMERCE_ENHANCEMENT_TRACKER.yaml")
        if not yaml_path.exists():
            raise HTTPException(status_code=404, detail="E-commerce enhancement tracker file not found")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        enhancements = data.get("enhancements", [])
        filtered = [e for e in enhancements if e.get("status", "").lower() == status.lower()]

        return {
            "enhancements": filtered,
            "total": len(filtered),
            "status": status,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_ecommerce_enhancements_by_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# SRE Analytics Enhancement Tracker endpoints
@app.get("/api/sre-analytics/enhancements")
async def get_sre_analytics_enhancements():
    """Get all SRE Analytics enhancements from tracker YAML."""
    try:
        import yaml
        yaml_path = Path("../sre-analytics/SRE_ANALYTICS_ENHANCEMENT_TRACKER.yaml")
        if not yaml_path.exists():
            raise HTTPException(status_code=404, detail="SRE Analytics enhancement tracker file not found")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        enhancements = data.get("enhancements", [])

        # Calculate progress statistics dynamically
        total = len(enhancements)
        completed = sum(1 for e in enhancements if e.get("status") in ["Complete", "Completed"])
        in_progress = sum(1 for e in enhancements if e.get("status") == "In Progress")
        planned = sum(1 for e in enhancements if e.get("status") in ["Planned", "Ideation"])

        progress = {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "planned": planned,
            "completion_percentage": round((completed / total * 100), 1) if total > 0 else 0
        }

        return {
            "enhancements": enhancements,
            "progress": progress,
            "metadata": {
                "project_name": data.get("project", {}).get("name"),
                "project_tag": data.get("project", {}).get("project_tag"),
                "version": data.get("project", {}).get("version"),
                "last_updated": data.get("project", {}).get("last_updated"),
                "technologies": data.get("project", {}).get("technologies", []),
            },
            "metrics": data.get("metrics", {}),
            "timeline": data.get("timeline", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_sre_analytics_enhancements_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sre-analytics/enhancements/{enhancement_id}")
async def get_sre_analytics_enhancement(enhancement_id: str):
    """Get specific SRE Analytics enhancement details."""
    try:
        import yaml
        yaml_path = Path("../sre-analytics/SRE_ANALYTICS_ENHANCEMENT_TRACKER.yaml")
        if not yaml_path.exists():
            raise HTTPException(status_code=404, detail="SRE Analytics enhancement tracker file not found")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        enhancements = data.get("enhancements", [])
        enhancement = next((e for e in enhancements if e["id"] == enhancement_id), None)

        if not enhancement:
            raise HTTPException(status_code=404, detail=f"Enhancement {enhancement_id} not found")

        return enhancement
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_sre_analytics_enhancement_failed", error=str(e), enhancement_id=enhancement_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sre-analytics/enhancements/status/{status}")
async def get_sre_analytics_enhancements_by_status(status: str):
    """Get SRE Analytics enhancements filtered by status."""
    try:
        import yaml
        yaml_path = Path("../sre-analytics/SRE_ANALYTICS_ENHANCEMENT_TRACKER.yaml")
        if not yaml_path.exists():
            raise HTTPException(status_code=404, detail="SRE Analytics enhancement tracker file not found")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        enhancements = data.get("enhancements", [])
        filtered = [e for e in enhancements if e.get("status", "").lower() == status.lower()]

        return {
            "enhancements": filtered,
            "total": len(filtered),
            "status": status,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_sre_analytics_enhancements_by_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Database / Conversation endpoints
@app.get("/api/conversations")
async def list_conversations(
    user_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    skip: int = 0,
):
    """List conversations with optional filters.

    Args:
        user_id: Filter by user ID
        status: Filter by status (active/archived/deleted)
        limit: Maximum results (default: 50)
        skip: Skip results (default: 0)

    Returns:
        List of conversations
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import ConversationRepository

        db_manager = await get_mongodb_manager()
        conv_repo = ConversationRepository(db_manager)

        conversations = await conv_repo.list_conversations(
            user_id=user_id,
            status=status,
            limit=limit,
            skip=skip,
        )

        return {
            "conversations": [
                {
                    "id": str(conv.id),
                    "title": conv.title,
                    "provider_used": conv.provider_used,
                    "routing_decision": conv.routing_decision,
                    "metrics": {
                        "message_count": conv.metrics.message_count,
                        "total_tokens": conv.metrics.total_tokens,
                        "total_cost_usd": conv.metrics.total_cost_usd,
                        "execution_time_ms": conv.metrics.execution_time_ms,
                    },
                    "status": conv.status,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                }
                for conv in conversations
            ],
            "total": len(conversations),
        }
    except Exception as e:
        logger.error("list_conversations_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation by ID.

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation details
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import ConversationRepository

        db_manager = await get_mongodb_manager()
        conv_repo = ConversationRepository(db_manager)

        conversation = await conv_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "provider_used": conversation.provider_used,
            "routing_decision": conversation.routing_decision,
            "metrics": {
                "message_count": conversation.metrics.message_count,
                "total_tokens": conversation.metrics.total_tokens,
                "total_cost_usd": conversation.metrics.total_cost_usd,
                "execution_time_ms": conversation.metrics.execution_time_ms,
            },
            "status": conversation.status,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_conversation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, limit: int | None = None):
    """Get messages for a conversation.

    Args:
        conversation_id: Conversation ID
        limit: Optional limit

    Returns:
        List of messages
    """
    try:
        from src.database.mongodb import get_mongodb_manager
        from src.database.repositories import MessageRepository

        db_manager = await get_mongodb_manager()
        msg_repo = MessageRepository(db_manager)

        messages = await msg_repo.get_conversation_messages(
            conversation_id, limit=limit
        )

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "provider": msg.provider,
                    "model": msg.model,
                    "token_count": msg.token_count,
                    "cost_usd": msg.cost_usd,
                    "metadata": msg.metadata,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
            "total": len(messages),
        }
    except Exception as e:
        logger.error("get_conversation_messages_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve frontend application.

    Args:
        full_path: Requested path

    Returns:
        FileResponse with index.html or 404
    """
    if FRONTEND_DIST.exists():
        # Serve index.html for all routes (SPA)
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

    raise HTTPException(status_code=404, detail="Frontend not built. Run: cd frontend && npm run build")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.orchestrator_host,
        port=settings.orchestrator_port,
        workers=settings.orchestrator_workers,
        log_level=settings.log_level.lower(),
        reload=False,
    )
