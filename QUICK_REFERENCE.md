# AI Orchestrator - Quick Reference Card

## 🚀 **Start in 30 Seconds**

```bash
cd /Users/shiva/Projects/ai-orchestrator
cp .env.example .env
# Add your API keys to .env
docker-compose up -d
curl http://localhost:8000/api/health
```

---

## 💬 **Three Ways to Use**

### 1. CLI (Interactive)
```bash
poetry run python src/cli.py interactive
```

### 2. REST API
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Your request"}'
```

### 3. Python Client
```python
from examples.python_client import AIOrchestrator
async with AIOrchestrator() as ai:
    result = await ai.chat("Build API")
```

---

## 🎯 **Provider Selection**

| Pattern | Provider | Example |
|---------|----------|---------|
| `build`, `code`, `deploy` | Claude Code | "Build REST API" |
| `ui`, `dashboard`, `interface` | ChatGPT | "Create dashboard" |
| `optimize prompt` | Gemini | "Improve this prompt" |
| `analyze incident`, `logs` | Local LLM | "Analyze outage" |
| `@provider:` | Explicit | "@chatgpt: write code" |

**Auto-routes to best provider by default!**

---

## 📡 **API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message |
| `/api/health` | GET | Check health |
| `/api/providers` | GET | List providers |
| `/metrics` | GET | Prometheus metrics |
| `/docs` | GET | Swagger UI |

---

## 🛠️ **Common Requests**

### Code Generation
```bash
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Build REST API for auth"}'
```

### Deployment
```bash
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Deploy to Kubernetes"}'
```

### Incident Analysis
```bash
curl -X POST http://localhost:8000/api/chat \
  -d '{
    "message": "Analyze incident",
    "context": {
      "logs": ["ERROR: DB timeout"],
      "metrics": {"cpu": 0.95}
    }
  }'
```

### UI/Dashboard
```bash
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "@chatgpt: Create dashboard"}'
```

### Multi-LLM Collaboration
```bash
curl -X POST http://localhost:8000/api/chat \
  -d '{
    "message": "Build complete dashboard",
    "enable_collaboration": true
  }'
```

---

## 🎨 **CLI Commands**

| Command | Action |
|---------|--------|
| `You> Build API` | Send message |
| `@provider: task` | Force provider |
| `/help` | Show help |
| `/health` | Check health |
| `/providers` | List providers |
| `/quit` | Exit |

---

## 🔄 **Fallback Chains**

### Incident Analysis
```
Local LLM (primary)
    ↓ (if fails)
Claude (fallback #1)
    ↓ (if fails)
Gemini (fallback #2)
```

### Code Tasks
```
Claude Code (primary)
    ↓ (if fails)
Claude (fallback)
```

---

## 🔧 **Request Options**

```json
{
  "message": "string",           // Required
  "context": {},                 // Optional
  "explicit_provider": "string", // Optional
  "enable_tools": true,          // Default: true
  "enable_collaboration": true   // Default: true
}
```

---

## 📊 **Monitoring**

```bash
# Health check
curl http://localhost:8000/api/health

# Metrics
curl http://localhost:8000/metrics

# Prometheus
open http://localhost:9090

# Grafana
open http://localhost:3000
```

---

## 🐛 **Troubleshooting**

| Problem | Solution |
|---------|----------|
| Server not responding | `docker-compose ps` |
| Provider unavailable | Check `.env` API keys |
| Local LLM not working | `ollama serve` |
| Tools not executing | `enable_tools: true` |

---

## 📚 **Documentation**

| Doc | Location |
|-----|----------|
| Full guide | `USAGE_GUIDE.md` |
| Quick start | `QUICKSTART.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| Diagrams | `docs/DIAGRAMS.md` |
| API reference | `docs/api-reference.md` |
| Routing patterns | `docs/routing-patterns.md` |
| Index | `docs/INDEX.md` |

---

## 🎓 **Examples**

```bash
# View CLI examples
poetry run python src/cli.py interactive

# Run Python examples
poetry run python examples/python_client.py

# View basic examples
cat examples/basic_usage.py
```

---

## ⚙️ **Configuration**

### Required in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

### Optional:
```bash
LOCAL_LLM_ENABLED=true
LOCAL_LLM_MODEL=llama2:13b
GITHUB_TOKEN=ghp_...
```

---

## 🌟 **Key Features**

✅ **5 LLM Providers** (Claude Code, ChatGPT, Gemini, Claude, Local)
✅ **Intelligent Routing** (pattern-based with confidence scores)
✅ **Tool Execution** (GitHub, Docker, K8s, Terminal, FileSystem)
✅ **Fallback Chains** (high availability)
✅ **Multi-LLM Collaboration** (orchestrate complex tasks)
✅ **Quality Checking** (automatic validation)
✅ **Privacy-First** (local LLM for sensitive data)
✅ **Monitoring** (Prometheus + Grafana)

---

## 💡 **Pro Tips**

1. Let the router choose (it's optimized)
2. Use Local LLM for incidents (private & free)
3. Enable collaboration for complex tasks
4. Provide context for better analysis
5. Check health regularly
6. Monitor metrics for insights

---

## 📍 **Quick Links**

- **Project**: `/Users/shiva/Projects/ai-orchestrator/`
- **Docs**: `http://localhost:8000/docs`
- **Metrics**: `http://localhost:8000/metrics`
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000`

---

## 🆘 **Need Help?**

```bash
# Check documentation index
cat docs/INDEX.md

# View usage guide
cat USAGE_GUIDE.md

# Read quick start
cat QUICKSTART.md

# CLI help
poetry run python src/cli.py --help
```

---

**Print this page for quick reference!**

**Last Updated**: 2025-10-12 | **Version**: 1.0.0
