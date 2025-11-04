# Grafana Dashboard for AI Orchestrator

This directory contains Grafana dashboard templates for monitoring LLM token usage, costs, and health metrics.

## Dashboard: LLM Token Analytics

File: `llm-token-dashboard.json`

### Features

1. **Token Usage per Agent** - Real-time token consumption statistics
2. **Token Usage Trend** - Historical token usage over time
3. **Total Estimated Cost** - Aggregate cost metrics in USD
4. **Cost Distribution** - Pie chart showing cost breakdown by agent
5. **Local LLM Health Status** - Health indicator for local models
6. **Local LLM Latency** - Response time metrics
7. **Token Distribution** - Donut chart of token distribution
8. **Cost Trend** - Stacked bars showing cost evolution

### Metrics Used

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `ai_orchestrator_llm_tokens_total` | Gauge | agent, model | Total tokens used per agent |
| `ai_orchestrator_estimated_cost_usd` | Gauge | agent, model | Estimated cost in USD per agent |
| `ai_orchestrator_llm_health_status` | Gauge | model, endpoint | LLM health (1=healthy, 0=unhealthy) |
| `ai_orchestrator_llm_latency_seconds` | Gauge | model, endpoint | LLM latency in seconds |

## Installation

### Option 1: Import via Grafana UI

1. Open Grafana (usually at http://localhost:3000)
2. Login (default: admin/admin)
3. Click **Dashboards** → **Import**
4. Upload `llm-token-dashboard.json`
5. Select your Prometheus datasource
6. Click **Import**

### Option 2: Import via API

```bash
# Set your Grafana API key
export GRAFANA_API_KEY="your-api-key"

# Import dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @llm-token-dashboard.json
```

### Option 3: Provisioning (Recommended for Production)

1. Copy dashboard JSON to Grafana provisioning directory:
   ```bash
   cp llm-token-dashboard.json /etc/grafana/provisioning/dashboards/
   ```

2. Create dashboard provider config (`/etc/grafana/provisioning/dashboards/ai-orchestrator.yaml`):
   ```yaml
   apiVersion: 1

   providers:
     - name: 'AI Orchestrator'
       orgId: 1
       folder: 'AI Orchestrator'
       type: file
       disableDeletion: false
       updateIntervalSeconds: 10
       allowUiUpdates: true
       options:
         path: /etc/grafana/provisioning/dashboards
         foldersFromFilesStructure: true
   ```

3. Restart Grafana:
   ```bash
   systemctl restart grafana-server
   ```

## Prerequisites

### Prometheus Configuration

Ensure Prometheus is scraping the AI Orchestrator metrics endpoint:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ai-orchestrator'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Data Source Setup

1. In Grafana, go to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Set URL: `http://localhost:9090` (or your Prometheus URL)
5. Click **Save & Test**

## Dashboard Configuration

### Refresh Rate

Default: **30 seconds**

To change:
1. Open dashboard
2. Click ⚙️ (Settings) → **General**
3. Set **Auto refresh** to desired interval

### Time Range

Default: **Last 6 hours**

Available ranges:
- Last 5 minutes
- Last 15 minutes
- Last 1 hour
- Last 6 hours
- Last 24 hours
- Last 7 days
- Custom range

### Alerts (Optional)

You can set up alerts on key metrics:

1. **High Cost Alert**:
   - Metric: `sum(ai_orchestrator_estimated_cost_usd) > 1.0`
   - Notify when total cost exceeds $1.00

2. **LLM Health Alert**:
   - Metric: `ai_orchestrator_llm_health_status == 0`
   - Notify when local LLM becomes unhealthy

3. **High Latency Alert**:
   - Metric: `ai_orchestrator_llm_latency_seconds > 1.0`
   - Notify when latency exceeds 1 second

## Customization

### Adding Panels

1. Click **Add panel** (+ icon)
2. Select visualization type
3. Configure query:
   ```promql
   ai_orchestrator_llm_tokens_total{agent="claude"}
   ```
4. Customize display options
5. Save panel

### Modifying Queries

Example queries:

```promql
# Total tokens across all agents
sum(ai_orchestrator_llm_tokens_total)

# Average cost per agent
avg(ai_orchestrator_estimated_cost_usd) by (agent)

# Tokens per model
sum(ai_orchestrator_llm_tokens_total) by (model)

# Health status by model
ai_orchestrator_llm_health_status{model="llama2:13b"}
```

## Troubleshooting

### Dashboard shows "No data"

1. **Check Prometheus is scraping metrics**:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. **Verify metrics are being exposed**:
   ```bash
   curl http://localhost:8000/metrics | grep ai_orchestrator
   ```

3. **Check Grafana data source connection**:
   - Go to Data Sources → Prometheus
   - Click **Save & Test**

### Metrics not updating

1. **Check API is running**:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Verify manifest exists**:
   ```bash
   ls -la manifest_state.json
   ```

3. **Trigger metrics update**:
   ```bash
   curl http://localhost:8000/api/analytics/summary
   ```

### Dashboard permissions issues

Ensure your Grafana user has:
- **Viewer** role (minimum) - Can view dashboards
- **Editor** role - Can modify dashboards
- **Admin** role - Full control

## Integration with Docker

If running in Docker Compose:

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/llm-token-dashboard.json:/etc/grafana/provisioning/dashboards/llm-token-dashboard.json
      - ./grafana/datasources.yaml:/etc/grafana/provisioning/datasources/datasources.yaml
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  ai-orchestrator:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - prometheus
```

## Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Prometheus Client (Python)](https://github.com/prometheus/client_python)

## Support

For issues or questions:
- Check logs: `docker logs grafana` or `/var/log/grafana/grafana.log`
- Grafana Community: https://community.grafana.com/
- Project Issues: [GitHub Issues](https://github.com/your-org/ai-orchestrator/issues)
