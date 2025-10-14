"""FastAPI application for AI Orchestrator."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from prometheus_client import Counter, Histogram, make_asgi_app
import structlog
from src.models.schemas import ChatRequest, ChatResponse, HealthStatus
from src.core.orchestrator import Orchestrator
from src.core.config import settings
import time
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


@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler."""
    logger.info("orchestrator_starting", host=settings.orchestrator_host, port=settings.orchestrator_port)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown event handler."""
    logger.info("orchestrator_shutting_down")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "AI Orchestrator",
        "version": "0.1.0",
        "status": "running",
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
