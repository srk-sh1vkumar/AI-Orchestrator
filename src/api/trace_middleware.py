"""Request tracing middleware for distributed tracing.

Enhancement 017: Production Architecture - Phase 0.

Adds unique trace_id to each request for correlation across services.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import uuid
import time
import structlog
from contextvars import ContextVar

# Context variable for storing trace_id across async calls
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

logger = structlog.get_logger()


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Middleware to inject and propagate trace_id for request correlation.

    Adds:
    - X-Trace-ID header to all requests and responses
    - Request timing
    - Structured logging with trace context
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Process request and inject trace_id."""
        # Check if trace_id already exists in headers (from upstream service)
        trace_id = request.headers.get("X-Trace-ID")

        if not trace_id:
            # Generate new trace_id
            trace_id = str(uuid.uuid4())

        # Store in context variable for access in handlers
        trace_id_var.set(trace_id)

        # Add to request state for easy access
        request.state.trace_id = trace_id

        # Record request start time
        start_time = time.time()

        # Add trace context to logger
        logger_with_trace = logger.bind(
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown"
        )

        logger_with_trace.info(
            "request_started",
            headers={k: v for k, v in request.headers.items() if k.lower() not in ["authorization", "x-api-key"]}
        )

        try:
            # Process request
            response: Response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Add trace_id to response headers
            response.headers["X-Trace-ID"] = trace_id

            # Add timing header
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

            logger_with_trace.info(
                "request_completed",
                status_code=response.status_code,
                duration_seconds=duration
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            logger_with_trace.error(
                "request_failed",
                error=str(e),
                error_type=type(e).__name__,
                duration_seconds=duration
            )
            raise


def get_trace_id() -> str:
    """Get current request's trace_id from context.

    Returns:
        Trace ID string, or empty string if not set
    """
    return trace_id_var.get()


def get_trace_context() -> dict:
    """Get trace context for logging.

    Returns:
        Dict with trace_id
    """
    trace_id = get_trace_id()
    if trace_id:
        return {"trace_id": trace_id}
    return {}
