#!/bin/bash

# Start AI Orchestrator with OpenTelemetry auto-instrumentation
# Enhancement 005: Agent-based distributed tracing

# OpenTelemetry configuration
export OTEL_SERVICE_NAME="ai-orchestrator"
export OTEL_SERVICE_VERSION="0.1.0"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"  # Monitoring-hub Tempo
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
export OTEL_TRACES_SAMPLER="parentbased_traceidratio"
export OTEL_TRACES_SAMPLER_ARG="1.0"  # 100% sampling
export OTEL_RESOURCE_ATTRIBUTES="deployment.environment=development,service.namespace=ai-orchestration"

# Optional: Enable logging instrumentation
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

# Run with auto-instrumentation
echo "Starting AI Orchestrator with OpenTelemetry tracing..."
echo "OTLP Endpoint: $OTEL_EXPORTER_OTLP_ENDPOINT"
echo "Service: $OTEL_SERVICE_NAME v$OTEL_SERVICE_VERSION"
echo "Sampling: 100%"
echo

./venv/bin/opentelemetry-instrument \
    ./venv/bin/uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
