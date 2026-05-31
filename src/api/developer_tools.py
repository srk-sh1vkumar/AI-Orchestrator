"""Developer tools API endpoints for debugging and testing."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import asyncio
import structlog

from src.core.orchestrator import Orchestrator
from src.providers.base import LLMProvider

logger = structlog.get_logger()
router = APIRouter(prefix="/api/dev", tags=["developer-tools"])

# Global flag for mock mode
_MOCK_MODE_ENABLED = False
_MOCK_RESPONSES = {}


class DebugRequest(BaseModel):
    """Request to debug a specific LLM request."""
    message: str
    provider: Optional[str] = None
    include_routing_decision: bool = True
    include_context: bool = True
    include_timing: bool = True


class DebugResponse(BaseModel):
    """Detailed debug information for a request."""
    request_id: str
    timestamp: datetime
    original_message: str
    routing_decision: Optional[Dict[str, Any]] = None
    selected_provider: str
    provider_response: Optional[str] = None
    context_used: Optional[Dict[str, Any]] = None
    timing: Optional[Dict[str, float]] = None
    errors: List[str] = []
    warnings: List[str] = []


class ProviderTestRequest(BaseModel):
    """Request to test a specific provider."""
    provider: str
    test_message: str = "Hello! This is a test message. Please respond with 'Test successful'."
    timeout_seconds: int = 30


class ProviderTestResponse(BaseModel):
    """Response from provider testing."""
    provider: str
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float
    timestamp: datetime


class MockResponse(BaseModel):
    """Mock response configuration."""
    provider: str
    pattern: str  # Regex pattern to match messages
    response: str
    delay_ms: int = 0


@router.post("/debug")
async def debug_request(request: DebugRequest) -> DebugResponse:
    """
    Debug a request with detailed lifecycle information.

    Shows routing decisions, context, timing, and full request lifecycle.
    """
    try:
        start_time = datetime.now()
        request_id = f"debug-{int(start_time.timestamp() * 1000)}"

        # Initialize orchestrator
        orchestrator = Orchestrator()

        # Build debug response
        debug_info = DebugResponse(
            request_id=request_id,
            timestamp=start_time,
            original_message=request.message,
            selected_provider=request.provider or "auto",
            errors=[],
            warnings=[],
        )

        # Capture routing decision
        if request.include_routing_decision:
            try:
                # Get routing decision without executing
                routing_info = {
                    "requested_provider": request.provider,
                    "available_providers": [p.value for p in LLMProvider],
                    "routing_method": "explicit" if request.provider else "automatic",
                }

                if not request.provider:
                    # Simulate automatic routing decision
                    routing_info["pattern_matched"] = "general query"
                    routing_info["confidence"] = 0.85
                    routing_info["fallback_chain"] = ["gemini", "local", "claude"]

                debug_info.routing_decision = routing_info
            except Exception as e:
                debug_info.warnings.append(f"Routing decision capture failed: {str(e)}")

        # Execute request and capture timing
        timing_data = {}
        try:
            exec_start = datetime.now()

            # Execute the actual request
            response = await orchestrator.process_request(
                message=request.message,
                provider=request.provider,
            )

            exec_end = datetime.now()
            exec_duration = (exec_end - exec_start).total_seconds() * 1000

            debug_info.provider_response = response.get("response", "")
            debug_info.selected_provider = response.get("provider", "unknown")

            if request.include_timing:
                timing_data = {
                    "total_ms": exec_duration,
                    "request_sent_at": exec_start.isoformat(),
                    "response_received_at": exec_end.isoformat(),
                }
                debug_info.timing = timing_data

        except Exception as e:
            debug_info.errors.append(f"Request execution failed: {str(e)}")
            debug_info.provider_response = None

        # Capture context if requested
        if request.include_context:
            try:
                context_info = {
                    "message_length": len(request.message),
                    "estimated_tokens": len(request.message.split()),  # Rough estimate
                    "mock_mode_enabled": _MOCK_MODE_ENABLED,
                }
                debug_info.context_used = context_info
            except Exception as e:
                debug_info.warnings.append(f"Context capture failed: {str(e)}")

        return debug_info

    except Exception as e:
        logger.error("debug_request_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Debug request failed: {str(e)}")


@router.post("/test-provider")
async def test_provider(request: ProviderTestRequest) -> ProviderTestResponse:
    """
    Test a specific provider with a simple message.

    Useful for verifying provider configuration and API keys.
    """
    try:
        start_time = datetime.now()

        # Initialize orchestrator
        orchestrator = Orchestrator()

        try:
            # Execute test request
            response = await asyncio.wait_for(
                orchestrator.process_request(
                    message=request.test_message,
                    provider=request.provider,
                ),
                timeout=request.timeout_seconds
            )

            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000

            return ProviderTestResponse(
                provider=request.provider,
                success=True,
                response=response.get("response", ""),
                error=None,
                latency_ms=latency_ms,
                timestamp=start_time,
            )

        except asyncio.TimeoutError:
            return ProviderTestResponse(
                provider=request.provider,
                success=False,
                response=None,
                error=f"Request timed out after {request.timeout_seconds} seconds",
                latency_ms=request.timeout_seconds * 1000,
                timestamp=start_time,
            )
        except Exception as e:
            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000

            return ProviderTestResponse(
                provider=request.provider,
                success=False,
                response=None,
                error=str(e),
                latency_ms=latency_ms,
                timestamp=start_time,
            )

    except Exception as e:
        logger.error("test_provider_failed", provider=request.provider, error=str(e))
        raise HTTPException(status_code=500, detail=f"Provider test failed: {str(e)}")


@router.post("/mock-mode/enable")
async def enable_mock_mode():
    """
    Enable mock mode for offline development.

    When enabled, requests return mock responses instead of calling real LLM APIs.
    """
    global _MOCK_MODE_ENABLED
    _MOCK_MODE_ENABLED = True

    logger.info("mock_mode_enabled")

    return {
        "mock_mode_enabled": True,
        "message": "Mock mode enabled. All LLM requests will return mock responses.",
        "mock_responses_configured": len(_MOCK_RESPONSES),
    }


@router.post("/mock-mode/disable")
async def disable_mock_mode():
    """Disable mock mode and resume normal LLM API calls."""
    global _MOCK_MODE_ENABLED
    _MOCK_MODE_ENABLED = False

    logger.info("mock_mode_disabled")

    return {
        "mock_mode_enabled": False,
        "message": "Mock mode disabled. LLM requests will use real APIs.",
    }


@router.get("/mock-mode/status")
async def get_mock_mode_status():
    """Get current mock mode status."""
    return {
        "mock_mode_enabled": _MOCK_MODE_ENABLED,
        "mock_responses_configured": len(_MOCK_RESPONSES),
        "mock_responses": list(_MOCK_RESPONSES.keys()),
    }


@router.get("/mock-mode")
async def get_mock_mode():
    """Get current mock mode status (alias for /mock-mode/status)."""
    return {
        "enabled": _MOCK_MODE_ENABLED,
        "mock_responses_configured": len(_MOCK_RESPONSES),
        "mock_responses": list(_MOCK_RESPONSES.keys()),
    }


class MockModeToggle(BaseModel):
    """Request to toggle mock mode."""
    enabled: bool


@router.post("/mock-mode/toggle")
async def toggle_mock_mode(request: MockModeToggle):
    """Toggle mock mode on/off."""
    global _MOCK_MODE_ENABLED
    _MOCK_MODE_ENABLED = request.enabled

    logger.info("mock_mode_toggled", enabled=request.enabled)

    return {
        "enabled": _MOCK_MODE_ENABLED,
        "message": f"Mock mode {'enabled' if request.enabled else 'disabled'}",
        "mock_responses_configured": len(_MOCK_RESPONSES),
    }


@router.post("/mock-responses")
async def add_mock_response(mock: MockResponse):
    """
    Add a mock response for a specific provider and pattern.

    When mock mode is enabled, matching requests will return the configured response.
    """
    global _MOCK_RESPONSES

    key = f"{mock.provider}:{mock.pattern}"
    _MOCK_RESPONSES[key] = {
        "response": mock.response,
        "delay_ms": mock.delay_ms,
        "provider": mock.provider,
    }

    logger.info("mock_response_added", provider=mock.provider, pattern=mock.pattern)

    return {
        "message": f"Mock response added for {mock.provider}",
        "pattern": mock.pattern,
        "total_mock_responses": len(_MOCK_RESPONSES),
    }


@router.delete("/mock-responses")
async def clear_mock_responses():
    """Clear all configured mock responses."""
    global _MOCK_RESPONSES

    count = len(_MOCK_RESPONSES)
    _MOCK_RESPONSES = {}

    logger.info("mock_responses_cleared", count=count)

    return {
        "message": f"Cleared {count} mock responses",
        "total_mock_responses": 0,
    }


@router.get("/request-history")
async def get_request_history(
    limit: int = Query(10, ge=1, le=100),
    provider: Optional[str] = None,
):
    """
    Get recent request history for debugging.

    Returns last N requests with timing and status information.
    """
    # TODO: Implement request history tracking in orchestrator
    # For now, return placeholder
    return {
        "message": "Request history tracking not yet implemented",
        "limit": limit,
        "provider_filter": provider,
        "requests": [],
    }


@router.get("/health-check")
async def developer_tools_health():
    """Health check for developer tools."""
    return {
        "status": "healthy",
        "mock_mode_enabled": _MOCK_MODE_ENABLED,
        "endpoints_available": [
            "/api/dev/debug",
            "/api/dev/test-provider",
            "/api/dev/mock-mode/enable",
            "/api/dev/mock-mode/disable",
            "/api/dev/mock-mode/status",
            "/api/dev/mock-responses",
            "/api/dev/request-history",
        ],
    }
