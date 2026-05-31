"""OpenTelemetry distributed tracing configuration.

Enhancement 005: OpenTelemetry Distributed Tracing
- End-to-end request visibility across LLM providers and tools
- Export to Tempo/Jaeger via OTLP
- Target latency overhead: <5ms
"""

from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
import structlog

logger = structlog.get_logger()

# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def init_tracing(
    service_name: str = "ai-orchestrator",
    service_version: str = "0.1.0",
    otlp_endpoint: str = "http://localhost:4317",
    sampling_rate: float = 1.0,
    enabled: bool = True,
) -> trace.Tracer:
    """Initialize OpenTelemetry distributed tracing.

    Args:
        service_name: Service name for traces
        service_version: Service version
        otlp_endpoint: OTLP collector endpoint (monitoring-hub Tempo)
        sampling_rate: Sampling rate (0.0-1.0). 1.0 = 100% of traces
        enabled: Enable/disable tracing

    Returns:
        Tracer instance
    """
    global _tracer

    if not enabled:
        logger.info("tracing_disabled")
        # Return no-op tracer
        _tracer = trace.NoOpTracer()
        return _tracer

    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": "development",
        "service.namespace": "ai-orchestration",
    })

    # Create OTLP exporter to monitoring-hub Tempo
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # No TLS for local development
    )

    # Configure sampling to reduce overhead
    # ParentBased ensures child spans inherit parent's sampling decision
    root_sampler = TraceIdRatioBased(rate=sampling_rate)
    sampler = ParentBased(root=root_sampler)

    # Create tracer provider
    provider = TracerProvider(
        resource=resource,
        sampler=sampler,
    )

    # Add batch span processor for async export (reduces latency)
    # BatchSpanProcessor buffers spans and sends them in batches
    processor = BatchSpanProcessor(
        otlp_exporter,
        max_queue_size=2048,
        schedule_delay_millis=5000,  # Export every 5 seconds
        max_export_batch_size=512,
    )
    provider.add_span_processor(processor)

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer instance
    _tracer = trace.get_tracer(__name__)

    logger.info(
        "tracing_initialized",
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        sampling_rate=sampling_rate,
    )

    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance.

    Returns:
        Tracer instance (may be no-op if tracing disabled)
    """
    global _tracer

    if _tracer is None:
        # Initialize with defaults if not yet initialized
        return init_tracing()

    return _tracer


def trace_llm_request(
    provider: str,
    model: str,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
):
    """Context manager for tracing LLM provider requests.

    Usage:
        with trace_llm_request("chatgpt", "gpt-4") as span:
            response = await provider.complete(messages)
            span.set_attribute("tokens.prompt", len(tokens))
            span.set_attribute("tokens.completion", response.tokens)

    Args:
        provider: LLM provider name
        model: Model identifier
        prompt_tokens: Number of prompt tokens (optional)
        completion_tokens: Number of completion tokens (optional)
    """
    tracer = get_tracer()

    span = tracer.start_span(
        f"llm.{provider}.complete",
        attributes={
            "llm.provider": provider,
            "llm.model": model,
            "llm.operation": "complete",
        }
    )

    if prompt_tokens is not None:
        span.set_attribute("llm.tokens.prompt", prompt_tokens)
    if completion_tokens is not None:
        span.set_attribute("llm.tokens.completion", completion_tokens)

    return trace.use_span(span, end_on_exit=True)


def trace_tool_execution(tool_name: str, operation: str):
    """Context manager for tracing tool executions.

    Usage:
        with trace_tool_execution("github", "create_pr") as span:
            result = await github_tool.create_pr(...)
            span.set_attribute("tool.result", "success")

    Args:
        tool_name: Tool identifier
        operation: Operation name
    """
    tracer = get_tracer()

    span = tracer.start_span(
        f"tool.{tool_name}.{operation}",
        attributes={
            "tool.name": tool_name,
            "tool.operation": operation,
        }
    )

    return trace.use_span(span, end_on_exit=True)


def trace_context_operation(operation: str, context_size: Optional[int] = None):
    """Context manager for tracing context management operations.

    Usage:
        with trace_context_operation("window_check", len(context)) as span:
            fits = check_context_window(context)
            span.set_attribute("context.fits", fits)

    Args:
        operation: Operation name (e.g., "window_check", "truncate")
        context_size: Context size in tokens (optional)
    """
    tracer = get_tracer()

    span = tracer.start_span(
        f"context.{operation}",
        attributes={
            "context.operation": operation,
        }
    )

    if context_size is not None:
        span.set_attribute("context.size_tokens", context_size)

    return trace.use_span(span, end_on_exit=True)


def trace_routing_decision(
    method: str,
    provider: str,
    confidence: float,
    category: Optional[str] = None,
):
    """Context manager for tracing routing decisions.

    Usage:
        with trace_routing_decision("ml", "chatgpt", 0.95, "ui_ux") as span:
            result = await route_request(...)
            span.set_attribute("routing.fallback_used", False)

    Args:
        method: Routing method (ml, regex, explicit, default)
        provider: Selected provider
        confidence: Confidence score
        category: Task category (optional)
    """
    tracer = get_tracer()

    span = tracer.start_span(
        "routing.decision",
        attributes={
            "routing.method": method,
            "routing.provider": provider,
            "routing.confidence": confidence,
        }
    )

    if category is not None:
        span.set_attribute("routing.category", category)

    return trace.use_span(span, end_on_exit=True)


def add_event_to_current_span(name: str, attributes: Optional[dict] = None):
    """Add an event to the current active span.

    Args:
        name: Event name
        attributes: Event attributes (optional)
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes=attributes or {})


def set_span_error(exception: Exception):
    """Mark the current span as errored and record the exception.

    Args:
        exception: The exception that occurred
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_status(trace.Status(trace.StatusCode.ERROR))
        current_span.record_exception(exception)
