# 🚀 Token Analytics - Quick Start Guide

**5-Minute Setup** | **3 Ways to Access** | **Real-Time Monitoring**

---

## ⚡ 1-Minute Quick Start

```bash
cd /Users/shiva/Projects/ai-orchestrator

# Generate test data
python simulate_run.py

# View dashboard
streamlit run dashboard/token_analytics.py
```

**Access**: http://localhost:8501

---

## 🎯 3 Ways to Access Analytics

### 🖥️ **Option 1: Standalone Dashboard** (Recommended for focused analysis)
```bash
streamlit run dashboard/token_analytics.py
```
- **Best for**: Deep-dive cost analysis, pricing comparisons
- **Features**: Full-screen analytics, auto-refresh, detailed charts

### 📊 **Option 2: Integrated Dashboard** (Recommended for overview)
```bash
streamlit run dashboard/dashboard.py
```
- **Best for**: All-in-one monitoring with system status
- **Tab**: "🔍 Token Analytics"

### 🔌 **Option 3: REST API** (Recommended for integrations)
```bash
# Start API server
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Get summary
curl http://localhost:8000/api/analytics/summary | jq
```
- **Best for**: Automation, scripts, external tools
- **Endpoints**: `/tokens`, `/summary`, `/cost-breakdown`

---

## 📊 Key Endpoints

```bash
# Token usage by agent
curl http://localhost:8000/api/analytics/tokens

# Complete analytics summary
curl http://localhost:8000/api/analytics/summary

# Cost breakdown details
curl http://localhost:8000/api/analytics/cost-breakdown

# Prometheus metrics
curl http://localhost:8000/metrics | grep ai_orchestrator
```

---

## 📈 Grafana Setup (Optional)

```bash
# 1. Import dashboard
# Open: http://localhost:3000
# Go to: Dashboards → Import
# Upload: grafana/llm-token-dashboard.json

# 2. Verify metrics
curl http://localhost:8000/metrics | grep ai_orchestrator_llm_tokens_total

# 3. View dashboard
# Navigate to: "AI Orchestrator - LLM Token Analytics"
```

---

## 💰 Understanding Your Costs

### Current Token Pricing (per 1K tokens)

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| **OpenAI** | GPT-4 Turbo | $0.01 | $0.03 |
| **OpenAI** | GPT-3.5 Turbo | $0.0005 | $0.0015 |
| **Anthropic** | Claude 3 Opus | $0.015 | $0.075 |
| **Anthropic** | Claude 3 Sonnet | $0.003 | $0.015 |
| **Anthropic** | Claude 3 Haiku | $0.00025 | $0.00125 |
| **Google** | Gemini Pro | $0.0005 | $0.0015 |
| **Local** | Llama2/Mistral | $0.00 | $0.00 |

### Quick Cost Calculation

**Example**: 10,000 tokens with Claude 3 Sonnet
- Input (60%): 6,000 tokens × $0.003/1K = $0.018
- Output (40%): 4,000 tokens × $0.015/1K = $0.060
- **Total**: $0.078

---

## 🔍 What You'll See

### Dashboard Metrics
- **💵 Total Cost**: Cumulative spending across all agents
- **🔢 Total Tokens**: Sum of tokens consumed
- **📊 Requests**: Number of LLM API calls
- **🤖 Agents**: Number of active agents tracked

### Visualizations
1. **Bar Chart**: Tokens per agent
2. **Timeline**: Usage trend over time
3. **Pie Chart**: Cost distribution
4. **Table**: Detailed breakdown with per-request averages
5. **Health Status**: Local LLM availability and latency

---

## 🎮 Interactive Features

### In Streamlit Dashboard
- ✅ **Auto-refresh**: Enable 15-second updates
- 📁 **Custom Path**: Change manifest location
- 📊 **Expandable Sections**: View pricing reference
- 📈 **Hover Details**: Interact with charts

### In API
- 🔄 **Real-time**: Always returns latest data
- 📊 **JSON Format**: Easy to parse and integrate
- 🎯 **Prometheus**: Metrics auto-update on `/summary` call

---

## 🧪 Test It Out

### Generate Sample Data
```bash
# Run orchestration
python simulate_run.py

# Check generated data
cat manifest_state.json | jq '.monitoring.token_usage'
```

### View Results
```bash
# Dashboard
streamlit run dashboard/token_analytics.py

# API
curl http://localhost:8000/api/analytics/summary | jq

# Metrics
curl http://localhost:8000/metrics | grep ai_orchestrator
```

---

## 🔧 Common Tasks

### Check Today's Spend
```bash
curl -s http://localhost:8000/api/analytics/summary | jq '.total_cost_usd'
```

### Find Most Expensive Agent
```bash
curl -s http://localhost:8000/api/analytics/cost-breakdown | \
  jq '.breakdown | to_entries | max_by(.value.cost_usd) | .key'
```

### Monitor LLM Health
```bash
curl -s http://localhost:8000/api/analytics/summary | jq '.local_llm'
```

### Export Data
```bash
curl -s http://localhost:8000/api/analytics/tokens > token-data.json
```

---

## 🚨 Troubleshooting

### No Data Showing?
```bash
# 1. Check manifest exists
ls -la manifest_state.json

# 2. Generate data
python simulate_run.py

# 3. Verify manifest content
cat manifest_state.json | jq '.monitoring'
```

### API Not Responding?
```bash
# 1. Check if API is running
curl http://localhost:8000/api/health

# 2. Start API server
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Dashboard Shows Errors?
```bash
# 1. Check Python dependencies
poetry install

# 2. Verify Streamlit version
streamlit --version

# 3. Check logs
tail -f logs/orchestrator.log
```

---

## 📚 Next Steps

1. **Set Up Grafana** (Optional): Import `grafana/llm-token-dashboard.json`
2. **Configure Alerts**: Set cost thresholds in Grafana
3. **Optimize Costs**: Switch expensive agents to cheaper models
4. **Integrate with CI/CD**: Add analytics to your pipeline

---

## 📖 Full Documentation

- **Complete Guide**: `TOKEN_ANALYTICS_README.md`
- **Implementation Details**: `TOKEN_ANALYTICS_IMPLEMENTATION.md`
- **Grafana Setup**: `grafana/README.md`
- **API Docs**: http://localhost:8000/docs

---

## ⏱️ Quick Commands Cheat Sheet

```bash
# Dashboard
streamlit run dashboard/token_analytics.py

# Integrated Dashboard
streamlit run dashboard/dashboard.py

# API Server
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Generate Data
python simulate_run.py

# View Metrics
curl http://localhost:8000/metrics | grep ai_orchestrator

# API Summary
curl http://localhost:8000/api/analytics/summary | jq

# Token Data
curl http://localhost:8000/api/analytics/tokens | jq

# Cost Breakdown
curl http://localhost:8000/api/analytics/cost-breakdown | jq
```

---

**🎉 You're ready to monitor your LLM costs!**

Start with the standalone dashboard, then explore the API and Grafana integrations as needed.
