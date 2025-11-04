# AI Orchestrator - Complete Usage Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Setup & Install

```bash
cd /Users/shiva/Projects/ai-orchestrator

# Copy and configure environment
cp .env.example .env

# Edit with your API keys
nano .env  # or use your preferred editor
```

**Required in `.env`:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
GOOGLE_API_KEY=your-key-here
```

**Optional (for local LLM):**
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2:13b

# Set in .env
LOCAL_LLM_ENABLED=true
LOCAL_LLM_MODEL=llama2:13b
```

### Step 2: Start the System

```bash
# Option A: Docker (recommended)
docker-compose up -d

# Option B: Direct Python
poetry install
poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Verify It's Running

```bash
# Check health
curl http://localhost:8000/api/health

# Should return: {"status": "healthy", ...}
```

---

## 💬 **Using the CLI (Interactive)**

The CLI provides a rich terminal interface for chatting with the orchestrator.

### Start Interactive Mode

```bash
poetry run python src/cli.py interactive
```

### Example Session

```
You> Build a REST API for user authentication

Provider: claude_code
Category: code_generation
Confidence: 90%

Response:
┌────────────────────────────────────────┐
│ I'll create a REST API with:          │
│ - JWT authentication                   │
│ - User registration/login endpoints    │
│ - Password hashing with bcrypt         │
│ - Token refresh mechanism              │
└────────────────────────────────────────┘

Tools Executed:
  ✓ github: create_repository (1.2s)
  ✓ docker: build_image (3.5s)

Execution time: 8.5s

You> @chatgpt: Create a dashboard for this API

Provider: chatgpt
Category: ui_generation
Confidence: 100%

Response:
┌────────────────────────────────────────┐
│ I'll design a dashboard with:         │
│ - User management panel                │
│ - Authentication logs viewer           │
│ - API metrics display                  │
└────────────────────────────────────────┘

You> Analyze incident: API stopped responding

Provider: local
Category: incident_analysis
Confidence: 95%

Response:
┌────────────────────────────────────────┐
│ Root Cause Analysis:                   │
│ - Database connection pool exhausted   │
│ - Recommended: Increase pool size      │
│ - Add connection timeout handling      │
└────────────────────────────────────────┘

You> /quit
Goodbye!
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help and available commands |
| `/health` | Check system health |
| `/providers` | List available providers |
| `/quit` | Exit interactive mode |

### Provider Override

```bash
# Force specific provider
You> @claude-code: Explain Docker
You> @chatgpt: Write backend code
You> @gemini: Optimize this prompt
You> @local: Analyze these logs
You> @claude: Explain this architecture
```

---

## 🌐 **Using the REST API**

### Basic Request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Your request here"
  }'
```

### Complete Examples

#### 1. Code Generation + Deployment

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Build and deploy a user service API",
    "enable_tools": true
  }'
```

**Response:**
```json
{
  "provider": "claude_code",
  "message": "I've created and deployed a user service API...",
  "tool_results": [
    {"tool_type": "github", "success": true},
    {"tool_type": "docker", "success": true},
    {"tool_type": "kubernetes", "success": true}
  ],
  "execution_time": 12.3
}
```

#### 2. Incident Analysis (with Context)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this production incident",
    "context": {
      "timestamp": "2025-10-12T14:30:00Z",
      "logs": [
        "ERROR: Database connection timeout at 14:30:00",
        "ERROR: Connection pool exhausted",
        "WARN: High memory usage: 95%"
      ],
      "metrics": {
        "error_rate": 0.35,
        "response_time_ms": 5000,
        "active_connections": 250,
        "cpu_usage": 0.95
      }
    }
  }'
```

**Response:**
```json
{
  "provider": "local",
  "message": "Root Cause Analysis:\n\n1. Database connection pool exhausted...",
  "fallback_events": [],
  "execution_time": 3.2
}
```

#### 3. UI Generation

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@chatgpt: Create a monitoring dashboard",
    "enable_tools": true
  }'
```

#### 4. Multi-LLM Collaboration

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Build complete dashboard with deployment",
    "enable_collaboration": true,
    "enable_tools": true
  }'
```

**Response:**
```json
{
  "provider": "claude_code",
  "collaboration_steps": [
    {
      "step": 1,
      "provider": "gemini",
      "response": "Optimized requirements...",
      "execution_time": 2.1
    },
    {
      "step": 2,
      "provider": "chatgpt",
      "response": "Dashboard design...",
      "execution_time": 3.5
    },
    {
      "step": 3,
      "provider": "claude_code",
      "response": "Deployed to production...",
      "execution_time": 8.2
    }
  ],
  "execution_time": 15.8
}
```

---

## 🐍 **Using Python Client**

### Install and Use

```bash
# Use the provided client
cd /Users/shiva/Projects/ai-orchestrator
poetry run python examples/python_client.py
```

### In Your Code

```python
from examples.python_client import AIOrchestrator
import asyncio

async def my_app():
    async with AIOrchestrator() as ai:
        # Simple request
        result = await ai.chat("Build a REST API")
        print(result['message'])

        # With provider override
        result = await ai.chat(
            "Create a dashboard",
            provider="chatgpt"
        )

        # With context
        result = await ai.chat(
            "Analyze incident",
            context={
                "logs": ["ERROR: ..."],
                "metrics": {"cpu": 0.95}
            }
        )

        # Check health
        health = await ai.health()
        print(health['status'])

asyncio.run(my_app())
```

---

## 🎯 **Common Use Cases**

### Use Case 1: DevOps Automation

```bash
# Deploy application
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Deploy my-app to Kubernetes cluster",
    "enable_tools": true
  }'

# Scale deployment
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Scale my-app deployment to 5 replicas"
  }'

# Check deployment status
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show status of my-app pods"
  }'
```

### Use Case 2: Incident Response

```bash
# Analyze incident (uses Local LLM first - private & free)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze production outage",
    "context": {
      "logs": ["ERROR logs here"],
      "metrics": {"error_rate": 0.4}
    }
  }'

# Create fixes
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create fixes for the connection pool issue"
  }'

# Generate postmortem
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@chatgpt: Create postmortem document",
    "context": {"analysis": "..."}
  }'
```

### Use Case 3: Full Stack Development

```bash
# Collaborate: Gemini → ChatGPT → Claude Code
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Build complete e-commerce dashboard",
    "enable_collaboration": true
  }'
```

---

## 🎨 **Provider Selection Guide**

### When to Use Each Provider

| Provider | Use When You Need... | Example |
|----------|---------------------|---------|
| **Claude Code** | Code, DevOps, deployment | "Deploy to K8s" |
| **ChatGPT** | UI, dashboards, workflows | "Create dashboard" |
| **Gemini** | Prompt optimization | "Optimize this prompt" |
| **Local LLM** | Private incident analysis | "Analyze outage" |
| **Claude** | General reasoning | Auto-fallback |

### Automatic Routing (Recommended)

Just send your request - the router picks the best provider:

```bash
"Build API" → Claude Code (90% confidence)
"Create dashboard" → ChatGPT (90% confidence)
"Analyze incident" → Local LLM (95% confidence)
```

### Manual Override

Use `@provider:` prefix:

```bash
@claude-code: your request
@chatgpt: your request
@gemini: your request
@local: your request
@claude: your request
```

---

## 🔧 **Configuration Options**

### Request Options

```json
{
  "message": "string (required)",
  "context": {}, // optional: additional context
  "explicit_provider": "claude_code", // optional: force provider
  "enable_tools": true, // default: true
  "enable_collaboration": true // default: true
}
```

### Disable Tools

```bash
# No tool execution (faster, explanation only)
curl -X POST http://localhost:8000/api/chat \
  -d '{
    "message": "Explain Kubernetes",
    "enable_tools": false
  }'
```

### Disable Collaboration

```bash
# Single provider only
curl -X POST http://localhost:8000/api/chat \
  -d '{
    "message": "Build dashboard",
    "enable_collaboration": false
  }'
```

---

## 📊 **Monitoring Your Usage**

### Check Health

```bash
curl http://localhost:8000/api/health
```

### View Metrics (Prometheus)

```bash
# Access metrics endpoint
curl http://localhost:8000/metrics

# Or view in Prometheus UI
open http://localhost:9090
```

### View Dashboards (Grafana)

```bash
# Access Grafana
open http://localhost:3000
# Login: admin/admin
```

**Available Metrics:**
- Request counts by provider/category
- Response times
- Fallback occurrences
- Tool execution stats

---

## 🐛 **Troubleshooting**

### Problem: Server not responding

```bash
# Check if running
curl http://localhost:8000/api/health

# Check Docker containers
docker-compose ps

# View logs
docker-compose logs -f orchestrator
```

### Problem: Provider unavailable

```bash
# Check provider status
curl http://localhost:8000/api/health

# Check API keys in .env
cat .env | grep API_KEY
```

### Problem: Local LLM not working

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model
ollama pull llama2:13b
```

### Problem: Tools not executing

```bash
# Verify tools enabled in request
{
  "message": "...",
  "enable_tools": true  // ← Check this
}

# Check tool permissions (Docker, K8s access)
docker ps  # Should work
kubectl get pods  # Should work
```

---

## 📚 **API Reference**

Full API documentation available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Documentation**: `docs/api-reference.md`

---

## 🎓 **Learning Resources**

| Resource | Location |
|----------|----------|
| Architecture Overview | `docs/ARCHITECTURE.md` |
| Visual Diagrams | `docs/DIAGRAMS.md` |
| Routing Patterns | `docs/routing-patterns.md` |
| All Documentation | `docs/INDEX.md` |

---

## 💡 **Pro Tips**

1. **Let the router choose**: It's optimized for best results
2. **Use Local LLM for incidents**: Private, fast, and free
3. **Enable collaboration for complex tasks**: Better quality
4. **Provide context**: Logs and metrics improve analysis
5. **Monitor fallbacks**: High fallback rate = check provider health
6. **Use explicit providers for testing**: Compare provider outputs

---

## 🎯 **Next Steps**

1. ✅ **Try the CLI**: `poetry run python src/cli.py interactive`
2. ✅ **Send test request**: Use curl examples above
3. ✅ **Check health**: `curl http://localhost:8000/api/health`
4. ✅ **View docs**: `open http://localhost:8000/docs`
5. ✅ **Monitor metrics**: `open http://localhost:9090`
6. ✅ **Read patterns**: `cat docs/routing-patterns.md`

---

**Need help?**
- Check `QUICKSTART.md` for setup issues
- See `docs/api-reference.md` for API details
- Review `docs/ARCHITECTURE.md` for how it works

**Happy orchestrating!** 🚀
