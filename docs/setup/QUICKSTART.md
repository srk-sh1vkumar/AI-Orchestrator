# AI Orchestrator - Quick Start Guide

## Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker & Docker Compose (optional, for running with services)
- API Keys for LLM providers
- Local LLM server (optional, Ollama recommended)

## Installation

### 1. Clone and Setup

```bash
cd ai-orchestrator
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and add your API keys:

```bash
# Required for Claude Code and Claude
ANTHROPIC_API_KEY=sk-ant-...

# Required for ChatGPT
OPENAI_API_KEY=sk-...

# Required for Gemini
GOOGLE_API_KEY=...

# Optional: Local LLM (Ollama)
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama2:13b
```

### 3. Install Dependencies

```bash
# Using Poetry
poetry install

# Or using pip
pip install -r requirements.txt  # (you'll need to generate this from pyproject.toml)
```

### 4. Setup Local LLM (Optional but Recommended)

For privacy-focused incident analysis:

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2:13b

# Start Ollama server (runs on localhost:11434)
ollama serve
```

## Running the Orchestrator

### Option 1: Direct Python

```bash
# Start the server
make run
# or
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker Compose (Recommended)

Includes Redis, Ollama, Prometheus, and Grafana:

```bash
# Start all services
make docker-up
# or
docker-compose up -d

# View logs
docker-compose logs -f orchestrator

# Stop services
make docker-down
```

## Testing the Orchestrator

### 1. Health Check

```bash
curl http://localhost:8000/api/health
```

### 2. List Available Providers

```bash
curl http://localhost:8000/api/providers
```

### 3. Send a Test Request

```bash
# Code generation (routes to Claude Code)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Build a REST API endpoint for user registration"
  }'

# Incident analysis (routes to Local LLM → Claude → Gemini)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this incident: API response time increased from 100ms to 5s at 2PM"
  }'

# Explicit provider
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@chatgpt: Create a dashboard layout for monitoring"
  }'
```

## Usage Examples

### Python Client

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={
                "message": "Deploy this app to Kubernetes",
                "enable_tools": True
            }
        )
        data = response.json()
        print(f"Provider: {data['provider']}")
        print(f"Response: {data['message']}")
        print(f"Tools executed: {len(data['tool_results'])}")

asyncio.run(main())
```

### Run Example Script

```bash
poetry run python examples/basic_usage.py
```

## Routing Rules

The orchestrator automatically routes tasks based on intent:

| Pattern | Provider | Example |
|---------|----------|---------|
| `build`, `code`, `implement`, `deploy` | Claude Code | "Build a REST API" |
| `ui`, `dashboard`, `interface` | ChatGPT | "Create a dashboard" |
| `optimize prompt`, `improve instruction` | Gemini | "Optimize this prompt" |
| `analyze incident`, `analyze logs` | Local LLM → Claude → Gemini | "Analyze this outage" |
| `@provider: task` | Specified provider | "@chatgpt: Design UI" |

## Monitoring

### Prometheus Metrics

Available at `http://localhost:8000/metrics`:

- `orchestrator_requests_total` - Total requests by provider/category
- `orchestrator_request_duration_seconds` - Request latency
- `orchestrator_fallbacks_total` - Fallback occurrences

### Grafana Dashboard

Access Grafana at `http://localhost:3000` (default: admin/admin)

Import the provided dashboard for orchestrator metrics.

## Development

### Run Tests

```bash
make test
# or
poetry run pytest tests/ -v
```

### Format Code

```bash
make format
```

### Lint Code

```bash
make lint
```

## Common Issues

### 1. Provider Not Available

**Error:** `Provider not available: local`

**Solution:** Ensure Ollama is running or disable local LLM:
```bash
LOCAL_LLM_ENABLED=false
```

### 2. API Key Not Configured

**Error:** `API key not configured`

**Solution:** Add the missing API key to `.env`

### 3. Docker Socket Permission

**Error:** `Permission denied: /var/run/docker.sock`

**Solution:** Add user to docker group:
```bash
sudo usermod -aG docker $USER
```

### 4. Port Already in Use

**Error:** `Port 8000 already in use`

**Solution:** Change port in `.env`:
```bash
ORCHESTRATOR_PORT=8001
```

## Next Steps

1. **Integrate with CI/CD**: Add orchestrator to your deployment pipeline
2. **Create Custom Tools**: Extend tools for your specific needs
3. **Configure Monitoring**: Set up alerts in Grafana
4. **Optimize Routing**: Adjust routing patterns in `src/core/routing.py`
5. **Add More Providers**: Integrate additional LLM providers

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Support

- GitHub Issues: [Create an issue]
- Documentation: See README.md for detailed information
- Examples: Check `examples/` directory

## Architecture Overview

```
User Request
    ↓
FastAPI Server (/api/chat)
    ↓
Task Router (analyze intent)
    ↓
Provider Selection (with fallback chain)
    ↓
LLM Provider (Claude Code, ChatGPT, Gemini, Local, Claude)
    ↓
Tool Execution (GitHub, Docker, K8s, etc.)
    ↓
Response + Metrics
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

Enjoy using the AI Orchestrator!
