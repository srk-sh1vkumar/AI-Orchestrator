# 📊 Token Analytics & Monitoring Dashboard

Comprehensive real-time monitoring system for LLM token usage, cost estimation, and health metrics across all AI providers in the orchestrator.

## 🌟 Features

- **Real-time Token Tracking** - Monitor token consumption across all LLM providers
- **Cost Estimation** - Accurate cost calculations based on current provider pricing
- **Interactive Dashboards** - Streamlit-based visualization with Plotly charts
- **REST API** - Complete analytics API for integration with external systems
- **Prometheus Metrics** - Enterprise-grade metrics for Grafana integration
- **Grafana Dashboard** - Pre-built dashboard template for production monitoring
- **Health Monitoring** - Real-time local LLM health and latency tracking
- **Comprehensive Logging** - Structured JSON telemetry for audit trails

---

## 🚀 Quick Start

### 1. View Token Analytics Dashboard

```bash
cd /Users/shiva/Projects/ai-orchestrator
streamlit run dashboard/token_analytics.py
```

Access at: **http://localhost:8501**

### 2. Access Analytics via API

```bash
# Start the API server
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Get token usage data
curl http://localhost:8000/api/analytics/tokens

# Get comprehensive summary
curl http://localhost:8000/api/analytics/summary

# Get cost breakdown
curl http://localhost:8000/api/analytics/cost-breakdown
```

### 3. View Integrated Dashboard

```bash
# Run the main dashboard (includes Token Analytics tab)
streamlit run dashboard/dashboard.py
```

Access at: **http://localhost:8501** → Navigate to "🔍 Token Analytics" tab

---

## 📈 Available Metrics

### Token Usage Metrics

| Metric | Description | Labels |
|--------|-------------|--------|
| `ai_orchestrator_llm_tokens_total` | Total tokens used per agent | `agent`, `model` |
| `ai_orchestrator_estimated_cost_usd` | Estimated cost in USD | `agent`, `model` |
| `ai_orchestrator_llm_health_status` | LLM health (1=healthy, 0=unhealthy) | `model`, `endpoint` |
| `ai_orchestrator_llm_latency_seconds` | LLM response latency | `model`, `endpoint` |

### Accessing Prometheus Metrics

```bash
# View all metrics
curl http://localhost:8000/metrics

# Filter for token metrics
curl http://localhost:8000/metrics | grep ai_orchestrator

# Example metrics output:
# ai_orchestrator_llm_tokens_total{agent="claude",model="claude-3-sonnet-20240229"} 2500.0
# ai_orchestrator_estimated_cost_usd{agent="claude",model="claude-3-sonnet-20240229"} 0.0375
```

---

## 📊 Dashboard Features

### Token Analytics Dashboard

The standalone token analytics dashboard (`dashboard/token_analytics.py`) provides:

1. **Key Metrics Panel**
   - Total cost (USD)
   - Total tokens consumed
   - Total requests
   - Number of agents tracked

2. **Token Usage Visualization**
   - Bar chart showing tokens per agent
   - Timeline chart showing usage over time

3. **Cost Analysis**
   - Detailed cost breakdown table
   - Pie chart showing cost distribution
   - Cost per request calculations

4. **LLM Health Monitoring**
   - Real-time health status
   - Latency metrics
   - Connection details

5. **Model Pricing Reference**
   - Complete pricing table for all supported models
   - Input/output cost per 1K tokens

### Integrated Dashboard

The main dashboard (`dashboard/dashboard.py`) includes a "Token Analytics" tab that provides:

- Seamless integration with system status and self-development tracking
- Unified view of all orchestrator metrics
- Auto-refresh capability (configurable)
- Run orchestration directly from dashboard

---

## 🔌 API Endpoints

### `/api/analytics/tokens`

Get token usage analytics for all agents.

**Response:**
```json
{
  "agents": {
    "claude": {
      "tokens": 2500,
      "cost_usd": 0.0375,
      "model": "claude-3-sonnet-20240229",
      "requests": 3
    },
    "chatgpt": {
      "tokens": 1800,
      "cost_usd": 0.027,
      "model": "gpt-4-turbo-preview",
      "requests": 2
    }
  },
  "total_tokens": 4300,
  "total_cost_usd": 0.0645,
  "timestamp": "2025-10-17T10:30:00Z"
}
```

### `/api/analytics/summary`

Get comprehensive analytics summary.

**Response:**
```json
{
  "total_tokens": 4300,
  "total_requests": 5,
  "agents_tracked": 2,
  "total_cost_usd": 0.0645,
  "local_llm": {
    "status": "healthy",
    "latency_ms": 250.5,
    "model": "llama2:13b",
    "endpoint": "http://localhost:11434"
  },
  "timestamp": "2025-10-17T10:30:00Z"
}
```

### `/api/analytics/cost-breakdown`

Get detailed cost breakdown by agent and model.

**Response:**
```json
{
  "breakdown": {
    "claude": {
      "model": "claude-3-sonnet-20240229",
      "tokens": 2500,
      "cost_usd": 0.0375
    }
  },
  "total_cost_usd": 0.0645,
  "timestamp": "2025-10-17T10:30:00Z"
}
```

---

## 📉 Grafana Integration

### Import Dashboard

1. Open Grafana at http://localhost:3000
2. Navigate to **Dashboards** → **Import**
3. Upload `grafana/llm-token-dashboard.json`
4. Select your Prometheus data source
5. Click **Import**

### Dashboard Panels

The pre-built Grafana dashboard includes:

- **Token Usage per Agent** - Real-time stat panel
- **Token Usage Trend** - Time series chart
- **Total Estimated Cost** - Cost metric with thresholds
- **Cost Distribution** - Pie chart by agent
- **Local LLM Health Status** - Health indicator
- **Local LLM Latency** - Latency time series
- **Token Distribution** - Donut chart
- **Cost Trend** - Stacked area chart

See `grafana/README.md` for detailed setup instructions.

---

## 💰 Cost Estimation

### Supported Models & Pricing

The cost estimator uses current pricing (per 1K tokens):

#### OpenAI Models
- **GPT-4 Turbo**: $0.01 (input) / $0.03 (output)
- **GPT-4**: $0.03 (input) / $0.06 (output)
- **GPT-3.5 Turbo**: $0.0005 (input) / $0.0015 (output)

#### Anthropic Claude Models
- **Claude 3 Opus**: $0.015 (input) / $0.075 (output)
- **Claude 3 Sonnet**: $0.003 (input) / $0.015 (output)
- **Claude 3 Haiku**: $0.00025 (input) / $0.00125 (output)

#### Google Gemini Models
- **Gemini Pro**: $0.0005 (input) / $0.0015 (output)
- **Gemini Ultra**: $0.01 (input) / $0.03 (output)

#### Local Models
- **Llama2, Mistral, CodeLlama**: $0.00 (free)

### Cost Calculation

Costs are calculated using a 60/40 input/output token ratio:

```python
input_tokens = total_tokens * 0.6
output_tokens = total_tokens * 0.4

cost = (input_tokens / 1000 * input_cost_per_1k) +
       (output_tokens / 1000 * output_cost_per_1k)
```

---

## 🔍 Monitoring Workflow

### 1. Generate Usage Data

Run an orchestration to generate token usage data:

```bash
cd /Users/shiva/Projects/ai-orchestrator
python simulate_run.py
```

This creates `manifest_state.json` with monitoring data.

### 2. View Analytics

**Option A: Streamlit Dashboard**
```bash
streamlit run dashboard/token_analytics.py
```

**Option B: Integrated Dashboard**
```bash
streamlit run dashboard/dashboard.py
# Navigate to "Token Analytics" tab
```

**Option C: API**
```bash
curl http://localhost:8000/api/analytics/summary | jq
```

**Option D: Grafana**
- Open http://localhost:3000
- Navigate to "AI Orchestrator - LLM Token Analytics" dashboard

### 3. Continuous Monitoring

Enable auto-refresh in Streamlit dashboards or configure Grafana refresh rate.

---

## 📝 Telemetry Logging

### Log Token Analytics

```python
from src.telemetry_logger import get_telemetry_logger

tel = get_telemetry_logger()

tel.log_token_analytics(
    agent="Claude",
    tokens_used=1850,
    cost_usd=0.0278,
    model="claude-3-sonnet-20240229",
    status="success"
)
```

### Log Format

Logs are written in JSON format to `logs/agents.log`:

```json
{
  "timestamp": "2025-10-17T10:30:00Z",
  "event_type": "token_analytics",
  "agent": "Claude",
  "tokens_used": 1850,
  "cost_usd": 0.0278,
  "model": "claude-3-sonnet-20240229",
  "status": "success"
}
```

---

## 🛠️ Configuration

### Update Token Pricing

Edit `src/cost_estimator.py`:

```python
PRICING_TABLE = {
    "your-model-name": (input_cost_per_1k, output_cost_per_1k),
    # Example:
    "custom-model": (0.005, 0.015),
}
```

### Customize Dashboard

Edit `dashboard/token_analytics.py` to:
- Modify chart styles
- Add new visualizations
- Change refresh intervals
- Customize metrics

### Configure Prometheus

Add scrape config to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'ai-orchestrator'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

---

## 🧪 Testing

### Test Token Tracking

```bash
cd /Users/shiva/Projects/ai-orchestrator

# Test monitoring module
python src/monitor.py

# Test cost estimation
python src/cost_estimator.py

# Test telemetry logger
python src/telemetry_logger.py
```

### Test API Endpoints

```bash
# Start server
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/api/analytics/tokens
curl http://localhost:8000/api/analytics/summary
curl http://localhost:8000/api/analytics/cost-breakdown

# Test Prometheus metrics
curl http://localhost:8000/metrics | grep ai_orchestrator
```

### Test Dashboard

```bash
# Test standalone dashboard
streamlit run dashboard/token_analytics.py

# Test integrated dashboard
streamlit run dashboard/dashboard.py
```

---

## 📦 Dependencies

The token analytics system requires:

```toml
# From pyproject.toml
prometheus-client = "^0.19.0"  # Prometheus metrics
streamlit = "^1.29.0"          # Dashboard UI
plotly = "^5.18.0"             # Interactive charts
pandas = "^2.1.4"              # Data manipulation
structlog = "^23.2.0"          # Structured logging
fastapi = "^0.109.0"           # REST API
```

Install all dependencies:

```bash
poetry install
```

---

## 🔄 Workflow Integration

### With Docker Compose

Add to your `docker-compose.yml`:

```yaml
services:
  ai-orchestrator:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./manifest_state.json:/app/manifest_state.json

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/llm-token-dashboard.json:/etc/grafana/provisioning/dashboards/llm-token-dashboard.json

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

### With CI/CD

Add analytics to your pipeline:

```yaml
# .github/workflows/analytics.yml
- name: Generate Token Analytics Report
  run: |
    python simulate_run.py
    curl http://localhost:8000/api/analytics/summary > analytics-report.json

- name: Upload Analytics Report
  uses: actions/upload-artifact@v3
  with:
    name: token-analytics
    path: analytics-report.json
```

---

## 📊 Example Use Cases

### 1. Cost Optimization

Identify which agents are consuming the most tokens and optimize:

```bash
# View cost breakdown
curl http://localhost:8000/api/analytics/cost-breakdown | jq '.breakdown'

# Compare model costs
# Switch high-cost agents to more economical models
```

### 2. Performance Monitoring

Track LLM latency and health:

```bash
# Check local LLM status
curl http://localhost:8000/api/analytics/summary | jq '.local_llm'

# Monitor via Grafana dashboard
# Set up alerts for latency > 1s or health = 0
```

### 3. Budget Tracking

Set up cost alerts:

```bash
# In Grafana, create alert:
# Condition: sum(ai_orchestrator_estimated_cost_usd) > 10.00
# Notify: Email, Slack, PagerDuty
```

### 4. Usage Analysis

Analyze token usage patterns:

```bash
# View token distribution
streamlit run dashboard/token_analytics.py

# Export data for analysis
curl http://localhost:8000/api/analytics/tokens > usage-data.json
```

---

## 🎯 Best Practices

1. **Regular Monitoring**: Check dashboards daily to identify cost trends
2. **Set Budgets**: Use Grafana alerts to notify when costs exceed thresholds
3. **Optimize Models**: Switch to cheaper models for non-critical tasks
4. **Cache Responses**: Implement response caching to reduce duplicate requests
5. **Log Everything**: Enable comprehensive telemetry for audit trails
6. **Review Pricing**: Update pricing table monthly as providers change rates

---

## 🐛 Troubleshooting

### Dashboard shows no data

1. Verify manifest exists:
   ```bash
   ls -la manifest_state.json
   ```

2. Run orchestration to generate data:
   ```bash
   python simulate_run.py
   ```

3. Check manifest has monitoring data:
   ```bash
   cat manifest_state.json | jq '.monitoring'
   ```

### API returns errors

1. Check API is running:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. View API logs:
   ```bash
   tail -f logs/orchestrator.log
   ```

3. Verify Prometheus metrics:
   ```bash
   curl http://localhost:8000/metrics
   ```

### Grafana dashboard shows no metrics

1. Check Prometheus scraping:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. Verify data source in Grafana:
   - Configuration → Data Sources → Prometheus
   - Click "Save & Test"

3. Trigger metrics update:
   ```bash
   curl http://localhost:8000/api/analytics/summary
   ```

---

## 📚 Additional Resources

- **Main README**: `README.md`
- **Grafana Setup**: `grafana/README.md`
- **API Documentation**: http://localhost:8000/docs
- **Project Status**: `PROJECT_STATUS.md`

---

## ✅ Feature Checklist

- [x] Real-time token usage tracking
- [x] Cost estimation with current pricing
- [x] Interactive Streamlit dashboard
- [x] REST API endpoints for analytics
- [x] Prometheus metrics integration
- [x] Grafana dashboard template
- [x] Local LLM health monitoring
- [x] Comprehensive telemetry logging
- [x] Integrated dashboard tabs
- [x] Model pricing reference
- [x] Timeline visualizations
- [x] Cost breakdown tables

---

**🎉 Token Analytics System is fully operational!**

For questions or issues, please refer to the troubleshooting section or create a GitHub issue.
