# Monitoring Hub Integration Guide

**Enhancement 017: Production Architecture - Phase 4**

This guide covers the complete integration between AI Orchestrator and the centralized Monitoring Hub for comprehensive observability across the entire platform.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Metrics Collection](#metrics-collection)
4. [Distributed Tracing](#distributed-tracing)
5. [Log Aggregation](#log-aggregation)
6. [Alerting](#alerting)
7. [Dashboards](#dashboards)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What is the Monitoring Hub?

The Monitoring Hub is a centralized observability platform that provides unified monitoring, tracing, and alerting for all projects:

- **AI Orchestrator** - LLM routing and tool execution
- **E-commerce Microservices** - Spring Boot services
- **SRE Analytics** - Analytics and reporting platform

### Components

| Component | Port | Purpose |
|-----------|------|---------|
| **Grafana** | 3002 | Unified dashboards and visualization |
| **Prometheus** | 9091 | Centralized metrics collection |
| **Jaeger** | 16686 | Distributed tracing UI |
| **Tempo** | 3201 | Cloud-native tracing backend |
| **OTEL Collector** | 4317, 4318 | OpenTelemetry ingestion |
| **Loki** | 3100 | Log aggregation |
| **AlertManager** | 9093 | Alert routing and deduplication |

### Integration Benefits

- **Unified Observability**: Single pane of glass for all projects
- **Correlated Data**: Metrics, traces, and logs in one place
- **Centralized Alerting**: Consistent alert management
- **Cross-Project Analysis**: Compare performance across services
- **Reduced Overhead**: Shared infrastructure

---

## Architecture

### Data Flow

```
AI Orchestrator
    |
    ├─> Metrics ─────────> Prometheus (port 8000/metrics)
    ├─> Traces ──────────> OTEL Collector ─────> Tempo/Jaeger
    └─> Logs ────────────> Loki (via Promtail)
                                  |
                                  v
                             Grafana Dashboards
                                  |
                                  v
                            AlertManager
```

### Network Configuration

All services communicate via `monitoring-hub` Docker network:

```yaml
networks:
  monitoring-hub:
    external: true
```

**Host Access**: Projects running on host use `host.docker.internal` to access monitoring hub services.

---

## Metrics Collection

### Prometheus Scrape Configuration

Location: `/Users/shiva/Projects/monitoring-hub/prometheus/prometheus.yml`

#### AI Orchestrator Targets

```yaml
# AI Orchestrator FastAPI Backend
- job_name: 'ai-orchestrator-backend'
  scrape_interval: 10s
  metrics_path: '/metrics'
  static_configs:
    - targets: ['host.docker.internal:8000']
      labels:
        project: 'ai-orchestrator'
        service: 'backend'
        tier: 'api'
        component: 'fastapi'

# AI Orchestrator Health Checks
- job_name: 'ai-orchestrator-health'
  scrape_interval: 30s
  metrics_path: '/api/health'
  static_configs:
    - targets: ['host.docker.internal:8000']

# vLLM Inference Server (Enhancement 017)
- job_name: 'ai-orchestrator-vllm'
  scrape_interval: 15s
  metrics_path: '/metrics'
  static_configs:
    - targets: ['host.docker.internal:8001']
      labels:
        provider: 'vllm'
        tier: 'llm'

# Ollama (Local LLM)
- job_name: 'ai-orchestrator-ollama'
  scrape_interval: 15s
  static_configs:
    - targets: ['host.docker.internal:11434']
      labels:
        provider: 'ollama'

# MongoDB (State Persistence)
- job_name: 'ai-orchestrator-mongodb'
  scrape_interval: 30s
  static_configs:
    - targets: ['host.docker.internal:27017']
      labels:
        tier: 'database'

# Redis (Semantic Cache)
- job_name: 'ai-orchestrator-redis'
  scrape_interval: 30s
  static_configs:
    - targets: ['host.docker.internal:6379']
      labels:
        tier: 'cache'
```

### Exposed Metrics

The AI Orchestrator exposes these metric families:

#### Core Application Metrics

```promql
# Request counts
orchestrator_requests_total{provider,status}
orchestrator_request_duration_seconds{provider}

# Provider health
llm_provider_health{provider}  # 0=unhealthy, 1=healthy

# Fallback events
orchestrator_fallbacks_total{from_provider,to_provider}

# Context window
context_window_tokens{provider}
context_window_truncations_total{strategy}
context_window_status{status}  # ok, warning, truncated

# Semantic cache
cache_hits_total
cache_misses_total
cache_size_bytes
cache_evictions_total

# Rate limiting
rate_limit_hits_total{provider}
rate_limit_blocks_total{provider}

# Cost tracking (Enhancement 007)
llm_request_cost_usd{provider,model}
budget_remaining_usd{budget_name}
budget_exceeded_total{budget_name}

# Tool execution
tool_executions_total{tool_type,status}
tool_execution_duration_seconds{tool_type}
tool_execution_errors_total{tool_type}

# Collaboration (Enhancement 006)
collaboration_sessions_total
collaboration_providers_count
```

### Querying Metrics

Access Prometheus at: http://localhost:9091

**Example Queries:**

```promql
# Total requests per second by provider
rate(orchestrator_requests_total[5m])

# Provider health status
llm_provider_health{project="ai-orchestrator"}

# Cache hit rate
rate(cache_hits_total[5m]) /
  (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# P95 request latency
histogram_quantile(0.95,
  rate(orchestrator_request_duration_seconds_bucket[5m]))

# Daily cost by provider
sum(increase(llm_request_cost_usd[24h])) by (provider)

# vLLM throughput (if running)
rate(vllm_request_success_total[1m])
```

---

## Distributed Tracing

### OpenTelemetry Configuration

The AI Orchestrator is configured to export traces to the Monitoring Hub's OTEL Collector.

**Configuration** (src/core/config.py):

```python
# OpenTelemetry Tracing (Enhancement 005)
tracing_enabled: bool = Field(default=True)
tracing_otlp_endpoint: str = Field(default="http://localhost:4317")
tracing_sampling_rate: float = Field(default=1.0)  # 100% in dev
tracing_service_name: str = Field(default="ai-orchestrator")
tracing_service_version: str = Field(default="0.1.0")
```

### Trace Instrumentation

All LLM provider calls are automatically instrumented:

**Traced Operations:**
- LLM completions (all providers)
- Streaming responses
- Provider fallbacks
- Tool executions
- Context window management
- Semantic cache lookups
- Collaboration sessions

**Span Attributes:**

```python
# Automatically added to all LLM request spans
span.set_attribute("llm.provider", "vllm")
span.set_attribute("llm.model", "meta-llama/Llama-2-13b-chat-hf")
span.set_attribute("llm.temperature", 0.7)
span.set_attribute("llm.max_tokens", 4096)
span.set_attribute("llm.tokens.input", 150)
span.set_attribute("llm.tokens.output", 320)
span.set_attribute("llm.tokens.total", 470)
span.set_attribute("llm.execution_time_ms", 1234)
```

### Viewing Traces

Access tracing UIs:

**Jaeger** (mature UI): http://localhost:16686
- Best for: Search, filtering, dependency graphs
- Search by service, operation, tags
- View trace timelines and dependencies

**Tempo** (via Grafana): http://localhost:3002
- Best for: Correlation with metrics and logs
- Integrated dashboards
- TraceQL queries

**Example TraceQL Queries:**

```traceql
# Find slow LLM requests (>2s)
{ duration > 2s && service.name = "ai-orchestrator" }

# Find failed provider calls
{ status = error && span.llm.provider = "vllm" }

# Find requests with high token usage
{ span.llm.tokens.total > 4000 }
```

### Trace Sampling

**Development** (`tracing_sampling_rate: 1.0`):
- 100% of requests traced
- Useful for debugging

**Production** (`tracing_sampling_rate: 0.1`):
- 10% of requests traced
- Reduces overhead while maintaining visibility

**Adjust in .env:**

```bash
TRACING_SAMPLING_RATE=0.1  # 10%
```

---

## Log Aggregation

### Loki Integration

The Monitoring Hub collects logs from AI Orchestrator via Promtail.

**Log Sources:**
- Application logs (structlog JSON)
- Container logs (stdout/stderr)
- Error logs (critical events)

### Structured Logging

AI Orchestrator uses structlog for structured JSON logging:

```json
{
  "event": "request_completed",
  "provider": "vllm",
  "tokens": 470,
  "duration_seconds": 1.234,
  "trace_id": "abc123...",
  "timestamp": "2025-11-28T12:00:00Z",
  "level": "info"
}
```

### LogQL Queries

Access Loki via Grafana Explore: http://localhost:3002/explore

**Example Queries:**

```logql
# All AI Orchestrator logs
{job="ai-orchestrator"}

# Errors only
{job="ai-orchestrator"} |= "level=error"

# Provider-specific logs
{job="ai-orchestrator"} | json | provider="vllm"

# Slow requests (>2s)
{job="ai-orchestrator"} | json | duration_seconds > 2

# Trace correlation
{job="ai-orchestrator"} | json | trace_id="abc123..."

# Pattern matching
{job="ai-orchestrator"} |~ "(?i)rate limit|quota exceeded"
```

### Log Retention

**Current Settings** (monitoring-hub/loki/loki-config.yaml):
- Retention: 7 days
- Max streams: 10,000
- Max entries: 1,000,000

**Increase Retention:**

```yaml
limits_config:
  retention_period: 30d  # Change from 7d
```

---

## Alerting

### AlertManager Rules

Location: `/Users/shiva/Projects/monitoring-hub/prometheus/rules/cross_project_alerts.yml`

#### AI Orchestrator Alert Rules

```yaml
- name: ai_orchestrator_alerts
  interval: 30s
  rules:
    # LLM Provider Health
    - alert: AILLMProviderDown
      expr: |
        llm_provider_health{project="ai-orchestrator"} == 0
      for: 2m
      labels:
        severity: critical
        project: ai-orchestrator
      annotations:
        summary: "LLM Provider {{ $labels.provider }} is down"
        description: "Provider has been unhealthy for 2 minutes"

    # High Error Rate
    - alert: AIHighErrorRate
      expr: |
        rate(orchestrator_requests_total{status="error"}[5m]) /
        rate(orchestrator_requests_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High error rate in AI Orchestrator"
        description: "Error rate is above 10% for 2 minutes"

    # Quota Exceeded
    - alert: AIQuotaExceeded
      expr: |
        rate(rate_limit_blocks_total[5m]) > 0
      labels:
        severity: warning
      annotations:
        summary: "Provider {{ $labels.provider }} quota exceeded"

    # Budget Alerts
    - alert: AIBudgetExceeded
      expr: |
        budget_remaining_usd <= 0
      labels:
        severity: critical
      annotations:
        summary: "Budget {{ $labels.budget_name }} exceeded"
        description: "No remaining budget for LLM requests"

    - alert: AIBudgetWarning
      expr: |
        budget_remaining_usd / budget_limit_usd < 0.2
      labels:
        severity: warning
      annotations:
        summary: "Budget {{ $labels.budget_name }} at 80%"

    # Tool Execution Failures
    - alert: AIToolExecutionFailures
      expr: |
        rate(tool_execution_errors_total[5m]) > 0.05
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High tool execution failure rate"

    # vLLM Server Down (if enabled)
    - alert: AIVLLMServerDown
      expr: |
        up{job="ai-orchestrator-vllm"} == 0
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "vLLM inference server is down"

    # Cache Performance
    - alert: AICacheLowHitRate
      expr: |
        rate(cache_hits_total[10m]) /
        (rate(cache_hits_total[10m]) + rate(cache_misses_total[10m])) < 0.3
      for: 10m
      labels:
        severity: info
      annotations:
        summary: "Semantic cache hit rate below 30%"
```

### Alert Routing

**AlertManager Configuration:**

```yaml
route:
  group_by: ['project', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Critical alerts - immediate notification
    - match:
        severity: critical
      receiver: 'critical-alerts'

    # Warning alerts - grouped notifications
    - match:
        severity: warning
      receiver: 'warning-alerts'
      group_interval: 30m
```

### Alert Destinations

**Configure Receivers** (alertmanager/config/alertmanager.yml):

```yaml
receivers:
  - name: 'critical-alerts'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#alerts-critical'
    email_configs:
      - to: 'oncall@company.com'

  - name: 'warning-alerts'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#alerts-warning'
```

---

## Dashboards

### Accessing Grafana

URL: http://localhost:3002
Default Credentials: admin/admin

### Pre-configured Dashboards

#### 1. Cross-Project Overview

**Path:** General / Cross-Project Overview

**Panels:**
- System health across all projects
- Request rates and latencies
- Error rates
- Resource utilization

#### 2. AI Orchestrator Monitoring

**Path:** AI Orchestrator / AI Orchestrator Monitoring

**Panels:**
- Provider distribution (pie chart)
- Request rate by provider
- Latency percentiles (P50, P95, P99)
- Provider health status
- Fallback events
- Cost tracking (daily/weekly/monthly)
- Cache performance
- Tool execution statistics

**Dashboard JSON:** `monitoring-hub/grafana/dashboards/ai-orchestrator-monitoring.json`

### Creating Custom Dashboards

1. Access Grafana: http://localhost:3002
2. Click "+  → Create Dashboard"
3. Add panels with Prometheus data source
4. Save dashboard
5. Export JSON:
   - Dashboard settings → JSON Model
   - Copy to `monitoring-hub/grafana/dashboards/`

**Example Panel Query:**

```json
{
  "expr": "rate(orchestrator_requests_total{provider='vllm'}[5m])",
  "legendFormat": "{{provider}} - {{status}}",
  "refId": "A"
}
```

---

## Testing

### Verify Integration

**1. Start Monitoring Hub:**

```bash
cd /Users/shiva/Projects/monitoring-hub
docker-compose up -d

# Verify all services
docker-compose ps
```

**2. Start AI Orchestrator:**

```bash
cd /Users/shiva/Projects/ai-orchestrator
poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**3. Generate Test Traffic:**

```bash
# Send test requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test request $i\"}"
  sleep 1
done
```

**4. Verify Data Collection:**

**Prometheus Targets:**
```bash
curl http://localhost:9091/targets
# Check ai-orchestrator-backend target is UP
```

**Metrics Endpoint:**
```bash
curl http://localhost:8000/metrics | grep orchestrator_requests_total
```

**Traces in Jaeger:**
```bash
open http://localhost:16686
# Search for service "ai-orchestrator"
```

**Logs in Loki:**
```bash
# Via Grafana Explore:
open http://localhost:3002/explore
# Select Loki datasource
# Query: {job="ai-orchestrator"}
```

**Grafana Dashboard:**
```bash
open http://localhost:3002/d/ai-orchestrator
```

---

## Troubleshooting

### Issue: Metrics Not Appearing in Prometheus

**Check:**

```bash
# 1. Verify AI Orchestrator is exposing metrics
curl http://localhost:8000/metrics

# 2. Check Prometheus scrape status
curl http://localhost:9091/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="ai-orchestrator-backend")'

# 3. Check Prometheus logs
cd /Users/shiva/Projects/monitoring-hub
docker-compose logs prometheus | grep "ai-orchestrator"
```

**Solutions:**

- Ensure AI Orchestrator is running on port 8000
- Check `host.docker.internal` resolves correctly
- Reload Prometheus config: `docker-compose restart prometheus`

### Issue: Traces Not Appearing

**Check OTLP Endpoint:**

```bash
# Verify OTEL collector is running
docker ps | grep otel-collector

# Check collector logs
docker-compose -f /Users/shiva/Projects/monitoring-hub/docker-compose.yml logs otel-collector

# Test OTLP endpoint
curl http://localhost:4318/v1/traces
```

**Solutions:**

- Verify `TRACING_OTLP_ENDPOINT=http://localhost:4317` in .env
- Check tracing is enabled: `TRACING_ENABLED=true`
- Restart AI Orchestrator to reconnect

### Issue: Alerts Not Firing

**Check Alert Rules:**

```bash
# View active alerts in Prometheus
curl http://localhost:9091/api/v1/alerts

# Check AlertManager
curl http://localhost:9093/api/v1/alerts
```

**Solutions:**

- Verify alert rules loaded: Check Prometheus UI → Alerts
- Test alert expression in Prometheus query interface
- Check AlertManager config: `monitoring-hub/alertmanager/config/alertmanager.yml`

### Issue: Dashboard Shows No Data

**Check Data Source:**

1. Grafana → Configuration → Data Sources
2. Verify Prometheus URL: `http://prometheus:9090`
3. Click "Save & Test"

**Check Time Range:**

- Dashboards default to "Last 6 hours"
- If AI Orchestrator just started, select "Last 5 minutes"

---

## Advanced Configuration

### Custom Metrics

Add custom metrics to AI Orchestrator:

```python
from prometheus_client import Counter, Histogram

# Define metric
custom_metric = Counter(
    'ai_custom_metric_total',
    'Description of metric',
    ['label1', 'label2']
)

# Increment metric
custom_metric.labels(label1='value1', label2='value2').inc()
```

Metrics will automatically be scraped by Prometheus.

### Alert Silencing

Temporarily silence alerts via AlertManager:

```bash
# Via UI
open http://localhost:9093

# Via API
curl -X POST http://localhost:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "AILLMProviderDown"}
    ],
    "startsAt": "2025-11-28T12:00:00Z",
    "endsAt": "2025-11-28T14:00:00Z",
    "createdBy": "admin",
    "comment": "Planned maintenance"
  }'
```

### Log Retention Tuning

Increase log retention for production:

```yaml
# monitoring-hub/loki/loki-config.yaml
limits_config:
  retention_period: 30d

table_manager:
  retention_deletes_enabled: true
  retention_period: 720h  # 30 days
```

Restart Loki:

```bash
cd /Users/shiva/Projects/monitoring-hub
docker-compose restart loki
```

---

## Production Checklist

- [ ] Monitoring hub services running and healthy
- [ ] Prometheus scraping AI Orchestrator targets
- [ ] Traces appearing in Jaeger/Tempo
- [ ] Logs flowing to Loki
- [ ] Grafana dashboards displaying data
- [ ] Alert rules tested and firing correctly
- [ ] AlertManager routing configured
- [ ] Notification channels tested (Slack, email, etc.)
- [ ] Data retention policies set appropriately
- [ ] Backup strategy for metrics and logs
- [ ] Documentation updated with deployment specifics

---

## Next Steps

1. **Explore Dashboards**: Review pre-built dashboards and customize
2. **Set Up Notifications**: Configure Slack/email for alerts
3. **Tune Alert Thresholds**: Adjust based on actual traffic patterns
4. **Create Runbooks**: Document response procedures for common alerts
5. **Monitor Costs**: Track LLM costs via cost tracking metrics

For more information:
- Monitoring Hub: /Users/shiva/Projects/monitoring-hub/README.md
- Grafana Docs: https://grafana.com/docs/
- Prometheus Docs: https://prometheus.io/docs/

---

**Last Updated:** 2025-11-28
**Enhancement:** 017 - Production Architecture - Phase 4
**Status:** Complete
