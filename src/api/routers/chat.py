"""API router for chat endpoints.

Enhancement 019: API Router Refactoring.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import structlog
import json
import time

from src.models.schemas import ChatRequest, ChatResponse, Message
from src.api.dependencies import get_orchestrator

logger = structlog.get_logger()
router = APIRouter(prefix="/api", tags=["chat"])

# Import metrics from main module to avoid duplication
# These will be set by init_chat_metrics after main.py loads
request_counter = None
request_duration = None
fallback_counter = None


def init_chat_metrics(counter, duration, fallback):
    """Initialize metrics from main module."""
    global request_counter, request_duration, fallback_counter
    request_counter = counter
    request_duration = duration
    fallback_counter = fallback


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat request.

    Args:
        request: Chat request

    Returns:
        ChatResponse

    Raises:
        HTTPException: If request processing fails
    """
    orchestrator = get_orchestrator()
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


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses using Server-Sent Events (SSE).

    Args:
        request: Chat request

    Returns:
        StreamingResponse with SSE format

    Raises:
        HTTPException: If request processing fails
    """
    orchestrator = get_orchestrator()

    async def event_generator():
        """Generate SSE events from streaming response."""
        try:
            logger.info("streaming_request_received", message_length=len(request.message))

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
