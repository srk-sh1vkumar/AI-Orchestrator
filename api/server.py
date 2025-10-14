"""
FastAPI Server - Orchestrator API with Prometheus Metrics

Exposes REST endpoints for orchestrator control, monitoring,
and Prometheus-compatible metrics export.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)
import json
import os
from pathlib import Path
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="DevAI Orchestrator API",
    description="Multi-agent AI orchestration with self-development tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Metrics
# Token usage metrics
token_usage_counter = Counter(
    'ai_orchestrator_llm_tokens_total',
    'Total tokens used by LLM agents',
    ['agent', 'model']
)

# LLM latency metrics
llm_latency_histogram = Histogram(
    'ai_orchestrator_llm_latency_seconds',
    'LLM response latency',
    ['model', 'agent']
)

# LLM health gauge
llm_health_gauge = Gauge(
    'ai_orchestrator_llm_health_status',
    'LLM health status (1=healthy, 0=unhealthy)',
    ['model', 'endpoint']
)

# Agent phase tracking
agent_phase_counter = Counter(
    'ai_orchestrator_agent_phase_total',
    'Agent phases completed',
    ['phase', 'agent', 'status']
)

# Cost tracking
estimated_cost_gauge = Gauge(
    'ai_orchestrator_estimated_costs_usd',
    'Estimated costs in USD',
    ['period']
)

# Self-development metrics
learning_hours_gauge = Gauge(
    'ai_orchestrator_self_learning_hours_total',
    'Total learning hours tracked'
)

goals_completed_counter = Counter(
    'ai_orchestrator_goals_completed_total',
    'Total goals completed',
    ['goal_type']
)

reflections_counter = Counter(
    'ai_orchestrator_reflections_total',
    'Total reflections generated',
    ['source']
)

# Request tracking
request_counter = Counter(
    'ai_orchestrator_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)

request_duration = Histogram(
    'ai_orchestrator_request_duration_seconds',
    'Request duration',
    ['endpoint']
)


def load_manifest() -> Dict[str, Any]:
    """Load the current manifest state from file."""
    manifest_path = Path("manifest_state.json")

    if not manifest_path.exists():
        return {
            "monitoring": {
                "token_usage": {},
                "local_llm_status": {},
                "estimated_costs_usd": 0.0
            },
            "self_development": {
                "goals": [],
                "milestones": [],
                "reflections": [],
                "metrics": {
                    "learning_hours": 0,
                    "completed_projects": 0,
                    "skills_gained": []
                }
            },
            "workflow": {
                "phases_completed": []
            }
        }

    with open(manifest_path, 'r') as f:
        return json.load(f)


def update_prometheus_metrics(manifest: Dict[str, Any]) -> None:
    """Update Prometheus metrics from manifest data."""

    # Update token usage metrics
    if "token_usage" in manifest.get("monitoring", {}):
        for agent, data in manifest["monitoring"]["token_usage"].items():
            model = data.get("model", "unknown")
            tokens = data.get("total_tokens", 0)

            # Set counter to current value (approximate)
            token_usage_counter.labels(agent=agent, model=model)._value.set(tokens)

    # Update LLM health
    if "local_llm_status" in manifest.get("monitoring", {}):
        health = manifest["monitoring"]["local_llm_status"]
        model = health.get("model", "unknown")
        endpoint = health.get("endpoint", "unknown")
        healthy = 1 if health.get("healthy", False) else 0

        llm_health_gauge.labels(model=model, endpoint=endpoint).set(healthy)

    # Update cost metrics
    if "estimated_costs_usd" in manifest.get("monitoring", {}):
        cost = manifest["monitoring"]["estimated_costs_usd"]
        estimated_cost_gauge.labels(period="total").set(cost)

    # Update self-development metrics
    if "self_development" in manifest:
        self_dev = manifest["self_development"]

        # Learning hours
        if "metrics" in self_dev:
            learning_hours = self_dev["metrics"].get("learning_hours", 0)
            learning_hours_gauge.set(learning_hours)

            # Completed projects
            completed = self_dev["metrics"].get("completed_projects", 0)
            goals_completed_counter.labels(goal_type="project")._value.set(completed)

        # Reflections
        if "reflections" in self_dev:
            reflections_counter.labels(source="ai_generated")._value.set(len(self_dev["reflections"]))

    # Update phase metrics
    if "workflow" in manifest and "phases_completed" in manifest["workflow"]:
        for phase_data in manifest["workflow"]["phases_completed"]:
            phase = phase_data.get("phase", "unknown")
            agent = phase_data.get("agent", "unknown")
            agent_phase_counter.labels(phase=phase, agent=agent, status="success").inc()


@app.get("/")
async def root():
    """Root endpoint - API information."""
    request_counter.labels(endpoint="/", method="GET", status="200").inc()

    return {
        "service": "DevAI Orchestrator API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/metrics",
            "/status",
            "/growth",
            "/health",
            "/docs"
        ]
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    """
    try:
        # Load manifest and update metrics
        manifest = load_manifest()
        update_prometheus_metrics(manifest)

        # Generate Prometheus format
        metrics_output = generate_latest().decode('utf-8')

        request_counter.labels(endpoint="/metrics", method="GET", status="200").inc()
        return PlainTextResponse(content=metrics_output, media_type=CONTENT_TYPE_LATEST)

    except Exception as e:
        logger.error("metrics_generation_failed", error=str(e))
        request_counter.labels(endpoint="/metrics", method="GET", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def status():
    """
    System status endpoint.

    Returns:
        JSON summary of orchestrator status, phases, tokens, and LLM health
    """
    try:
        manifest = load_manifest()

        # Extract key metrics
        monitoring = manifest.get("monitoring", {})
        workflow = manifest.get("workflow", {})

        # Calculate aggregates
        total_tokens = sum(
            data.get("total_tokens", 0)
            for data in monitoring.get("token_usage", {}).values()
        )

        phases_completed = len(workflow.get("phases_completed", []))
        current_phase = workflow.get("current_phase", "Unknown")

        status_data = {
            "status": "operational",
            "current_phase": current_phase,
            "phases_completed": phases_completed,
            "monitoring": {
                "total_tokens": total_tokens,
                "estimated_costs_usd": monitoring.get("estimated_costs_usd", 0.0),
                "local_llm_healthy": monitoring.get("local_llm_status", {}).get("healthy", False),
                "llm_latency_ms": monitoring.get("local_llm_status", {}).get("latency_ms", 0)
            },
            "agents": {
                agent: data.get("status", "unknown")
                for agent, data in workflow.get("agents", {}).items()
            }
        }

        request_counter.labels(endpoint="/status", method="GET", status="200").inc()
        return status_data

    except Exception as e:
        logger.error("status_check_failed", error=str(e))
        request_counter.labels(endpoint="/status", method="GET", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/growth")
async def growth():
    """
    Self-development growth endpoint.

    Returns:
        JSON summary of personal development goals, milestones, and metrics
    """
    try:
        manifest = load_manifest()
        self_dev = manifest.get("self_development", {})

        # Calculate goal statistics
        goals = self_dev.get("goals", [])
        completed_goals = [g for g in goals if g.get("status") == "Completed"]
        in_progress_goals = [g for g in goals if g.get("status") == "In Progress"]

        growth_data = {
            "metrics": self_dev.get("metrics", {}),
            "goals": {
                "total": len(goals),
                "completed": len(completed_goals),
                "in_progress": len(in_progress_goals),
                "list": goals
            },
            "milestones": self_dev.get("milestones", []),
            "recent_reflections": self_dev.get("reflections", [])[-5:],  # Last 5
            "skills_gained": self_dev.get("metrics", {}).get("skills_gained", [])
        }

        request_counter.labels(endpoint="/growth", method="GET", status="200").inc()
        return growth_data

    except Exception as e:
        logger.error("growth_data_failed", error=str(e))
        request_counter.labels(endpoint="/growth", method="GET", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns:
        Basic health status
    """
    request_counter.labels(endpoint="/health", method="GET", status="200").inc()

    return {
        "status": "healthy",
        "service": "DevAI Orchestrator API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    # Use port 8002 to avoid conflict with existing orchestrator on 8000
    PORT = 8002

    print("Starting DevAI Orchestrator API Server...")
    print("Endpoints available:")
    print(f"  - http://localhost:{PORT}/metrics   (Prometheus metrics)")
    print(f"  - http://localhost:{PORT}/status    (System status)")
    print(f"  - http://localhost:{PORT}/growth    (Self-development)")
    print(f"  - http://localhost:{PORT}/docs      (API documentation)")
    print(f"  - http://localhost:{PORT}/redoc     (ReDoc)")

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        log_level="info"
    )
