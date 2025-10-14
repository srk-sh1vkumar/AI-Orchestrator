# 🚀 DevAI Orchestrator - Quick Start Guide

Get up and running with the DevAI Orchestrator in under 5 minutes!

---

## ⚡ 5-Minute Setup

### Step 1: Prerequisites Check

```bash
# Check Python version (3.11+ required)
python --version

# Check if Poetry is installed (recommended)
poetry --version

# If not installed:
pip install poetry
```

### Step 2: Install Dependencies

```bash
cd /Users/shiva/Projects/ai-orchestrator

# Using Poetry (recommended)
poetry install

# OR using pip
pip install -r requirements.txt
```

### Step 3: Configure Environment (Optional for Demo)

```bash
# Demo mode works without API keys!
# For full functionality, configure API keys:

cp .env.example .env
nano .env  # Add your API keys
```

### Step 4: Run Your First Simulation

```bash
# Execute complete orchestration workflow
python simulate_run.py
```

**Expected Output:**
```
🚀 DEVAI ORCHESTRATOR - COMPLETE SIMULATION
============================================================
Executing full orchestrator workflow with monitoring...

🎨 PHASE 1: Architecture Design
✅ Design completed successfully

💻 PHASE 2: Code Generation & Implementation
✅ Code generation completed successfully

🚀 PHASE 3: Deployment & CI/CD
✅ Deployment configuration completed successfully

🌱 PHASE 4: Self-Development Tracking
✅ Self-development tracking completed

📊 SIMULATION COMPLETE - FINAL SUMMARY
Total Tokens: 9,080
Total Estimated Cost: $0.0523 USD
Learning Hours: 2.5 hours
```

**Files Created:**
- ✅ `manifest_state.json` - Full execution state
- ✅ `orchestrator_summary.json` - Quick summary
- ✅ `logs/orchestrator.log` - Main events
- ✅ `logs/agents.log` - Agent executions
- ✅ `logs/errors.log` - Error tracking

---

## 🖥️ Start the Dashboard

### Terminal 1: API Server

```bash
cd api
python server.py
```

**Endpoints Available:**
- 📊 http://localhost:8000/docs - Swagger UI
- 📈 http://localhost:8000/metrics - Prometheus metrics
- 🔍 http://localhost:8000/status - System status
- 🌱 http://localhost:8000/growth - Self-development data

### Terminal 2: Streamlit Dashboard

```bash
cd dashboard
streamlit run dashboard.py
```

**Dashboard Features:**
- 📊 Real-time token usage charts
- 💰 Cost breakdown visualization
- 🎯 Goal progress tracking
- 🏆 Milestone display
- 💭 AI-generated reflections
- 🔄 One-click orchestration

**Opens at:** http://localhost:8501

---

## 🧪 Quick Tests

### 1. Test Core Orchestrator

```bash
cd src
python ai_orchestrator.py
```

### 2. Test Monitoring

```bash
cd src
python monitor.py
```

### 3. Test Cost Estimator

```bash
cd src
python cost_estimator.py
```

### 4. Test Self-Development Agent

```bash
cd src
python self_dev_agent.py
```

### 5. Test API Endpoints

```bash
# Start server first (Terminal 1)
cd api && python server.py

# Then test (Terminal 2)
curl http://localhost:8000/health
curl http://localhost:8000/status | jq
curl http://localhost:8000/metrics
curl http://localhost:8000/growth | jq .metrics
```

---

## 📊 View Your Data

### Inspect Manifest

```bash
# Pretty-print JSON
cat manifest_state.json | jq

# View specific sections
cat manifest_state.json | jq '.monitoring'
cat manifest_state.json | jq '.self_development'
cat manifest_state.json | jq '.workflow'
```

### Check Logs

```bash
# Recent orchestrator events
tail -20 logs/orchestrator.log | jq

# Agent executions
tail -20 logs/agents.log | jq

# Errors (if any)
tail -20 logs/errors.log | jq
```

### Query Prometheus Metrics

```bash
# Fetch metrics
curl -s http://localhost:8000/metrics | grep ai_orchestrator

# Specific metrics
curl -s http://localhost:8000/metrics | grep tokens_total
curl -s http://localhost:8000/metrics | grep learning_hours
```

---

## 🎯 Common Use Cases

### Use Case 1: Track Development Session

```bash
# 1. Run orchestration
python simulate_run.py

# 2. View results in dashboard
cd dashboard && streamlit run dashboard.py

# 3. Check learning hours
cat manifest_state.json | jq '.self_development.metrics.learning_hours'
```

### Use Case 2: Monitor LLM Costs

```bash
# 1. Run simulation
python simulate_run.py

# 2. View cost breakdown
cat manifest_state.json | jq '.monitoring.cost_breakdown'

# 3. Check total cost
cat manifest_state.json | jq '.monitoring.estimated_costs_usd'
```

### Use Case 3: Export Metrics to Prometheus

```bash
# 1. Start API server
cd api && python server.py

# 2. Configure Prometheus to scrape
# prometheus.yml:
#   scrape_configs:
#     - job_name: 'ai_orchestrator'
#       static_configs:
#         - targets: ['localhost:8000']

# 3. View in Prometheus
# http://localhost:9090/graph
```

### Use Case 4: Track Personal Goals

```python
from self_dev_agent import SelfDevelopmentAgent

agent = SelfDevelopmentAgent()
manifest = load_manifest()

# Add new goal
manifest["self_development"]["goals"].append({
    "id": "g3",
    "title": "Master Cloud Architecture",
    "status": "Planned",
    "progress": 0
})

# Track learning session
manifest = agent.track_learning_hours(manifest, 3.5)

# Generate reflection
reflection = agent.generate_reflection(context)
```

---

## 🐳 Docker Quick Start

### Build Image

```bash
docker build -t devai-orchestrator:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/manifest_state.json:/app/manifest_state.json \
  devai-orchestrator:latest
```

### Docker Compose

```bash
docker-compose up -d
```

---

## 🔧 Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Or run with Poetry
poetry run python simulate_run.py
```

### Issue: API server won't start

**Solution:**
```bash
# Check port availability
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Start on different port
cd api && uvicorn server:app --port 8001
```

### Issue: Dashboard shows "No manifest data"

**Solution:**
```bash
# Run simulation first
python simulate_run.py

# Verify manifest exists
ls -lh manifest_state.json

# Refresh dashboard (press 'R')
```

### Issue: Import errors in dashboard

**Solution:**
```bash
# Install Streamlit dependencies
pip install streamlit plotly pandas

# Or use Poetry
poetry add streamlit plotly pandas
```

---

## 📚 Next Steps

### 1. Customize Your Workflow

Edit `src/ai_orchestrator.py` to add custom agents:

```python
def agent_custom_task(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Your custom agent logic here"""
    print("Running custom task...")
    # ... implementation
    return manifest
```

### 2. Add New Metrics

Edit `api/server.py` to expose custom metrics:

```python
custom_metric = Counter(
    'ai_orchestrator_custom_total',
    'Custom metric description',
    ['label']
)
```

### 3. Integrate with Existing Tools

```python
# Add to src/tools/ (if needed)
# Follow existing tool patterns from base project
```

### 4. Enhance Self-Development Tracking

Edit `src/self_dev_agent.py`:

```python
# Add custom goal types
# Customize reflection templates
# Integrate with Notion/Google Sheets
```

---

## 🎓 Learning Path

### Week 1: Core Understanding
- [x] Run simulation successfully
- [x] Explore manifest structure
- [x] Understand agent workflow
- [ ] Review code modules

### Week 2: Customization
- [ ] Add custom agent
- [ ] Modify cost calculations
- [ ] Customize dashboard
- [ ] Add new metrics

### Week 3: Integration
- [ ] Connect to Prometheus/Grafana
- [ ] Integrate with CI/CD
- [ ] Add Slack notifications
- [ ] Deploy to production

---

## 💡 Pro Tips

1. **Use Poetry** for dependency management - it's more robust
2. **Enable auto-refresh** in dashboard for real-time monitoring
3. **Check logs** regularly during development
4. **Customize reflection templates** for personalized insights
5. **Export metrics** to Grafana for advanced visualization
6. **Run simulations daily** to track consistent learning progress
7. **Back up manifest** regularly for historical analysis

---

## 📞 Get Help

- **Documentation**: [README_DEVAI_ORCHESTRATOR.md](README_DEVAI_ORCHESTRATOR.md)
- **Implementation Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Future Features**: [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md)
- **API Reference**: http://localhost:8000/docs (when running)

---

## ✅ Success Checklist

After completing this guide, you should have:

- [x] Installed all dependencies
- [x] Run first simulation successfully
- [x] Generated manifest and logs
- [x] Started API server
- [x] Launched dashboard
- [x] Viewed metrics and charts
- [x] Understood core workflow
- [x] Explored self-development features

**Congratulations! You're now ready to use the DevAI Orchestrator! 🎉**

---

**Time to Complete**: ~5-10 minutes
**Next**: Explore advanced features and customization options
